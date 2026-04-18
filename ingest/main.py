import os
import shutil
import time
import json
import logging
import uuid
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from parsers.pdf_parser import parse_pdf
from parsers.docx_parser import parse_docx
from parsers.pptx_parser import parse_pptx

# --- 1. Structured Logging Setup ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "service": "ingest-api",
            "message": record.getMessage(),
        }
        if hasattr(record, "app_data"):
            log_data.update(record.app_data)
        return json.dumps(log_data)

logger = logging.getLogger("ingest-api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

app = FastAPI(title="Ingest Service - Modular Multi-Format OCR")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ingest-api"}

logger.info("Loading SentenceTransformers...")
embeddings_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
qdrant = QdrantClient(host=QDRANT_HOST, port=6333)
COLLECTION_NAME = "spe_quiz_knowledge"

def extract_text_routed(file_path: str, filename: str) -> str:
    """The central router that delegates to the correct parser module."""
    ext = filename.lower().split('.')[-1]
    
    if ext == 'pptx':
        return parse_pptx(file_path)
    elif ext == 'docx':
        return parse_docx(file_path)
    elif ext == 'pdf':
        return parse_pdf(file_path)
    else:
        return ""

def process_and_embed(file_path: str, filename: str):
    """The background worker that chunks and embeds the text."""
    start_time = time.time()
    logger.info(f"Started processing {filename}")
    
    # 1. DELEGATE EXTRACTION
    try:
        full_text = extract_text_routed(file_path, filename)
        
        if not full_text.strip():
            logger.warning(f"No text extracted from {filename}", extra={"app_data": {
                "event": "ingest_empty",
                "filename": filename
            }})
            os.remove(file_path)
            return

        # 2. CHUNK
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(full_text)

        # 3. DATABASE SETUP
        if not qdrant.collection_exists(COLLECTION_NAME):
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        # 4. EMBED AND PUSH
        points = []
        for chunk in chunks:
            vector = embeddings_model.embed_query(chunk)
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()), 
                    vector=vector,
                    payload={"text": chunk, "source": filename} 
                )
            )
        
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        
        # Calculate stats
        latency = time.time() - start_time
        file_size = os.path.getsize(file_path)
        
        logger.info(f"Successfully pushed {filename} to Qdrant", extra={"app_data": {
            "event": "ingest_success",
            "filename": filename,
            "file_size_bytes": file_size,
            "chunks": len(chunks),
            "chars": len(full_text),
            "latency_sec": round(latency, 3)
        }})
        
    except Exception as e:
        logger.error(f"Ingestion failed for {filename}: {str(e)}", extra={"app_data": {
            "event": "ingest_error",
            "filename": filename,
            "error": str(e)
        }})
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    allowed_extensions = ['pptx', 'docx', 'pdf']
    ext = file.filename.lower().split('.')[-1]
    
    if ext not in allowed_extensions:
        return {"error": f"Unsupported file type. Allowed types: {allowed_extensions}"}
        
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_and_embed, temp_file_path, file.filename)
    return {"status": "processing", "message": f"{file.filename} delegated to background parser."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/documents")
async def list_documents():
    """Fetches a list of unique filenames currently in the database."""
    try:
        if not qdrant.collection_exists(COLLECTION_NAME):
            return {"documents": []}
            
        records, _ = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            with_payload=["source"],
            with_vectors=False,
            limit=10000 
        )
        
        sources = list(set([r.payload.get("source") for r in records if r.payload and "source" in r.payload]))
        return {"documents": sources}
    except Exception as e:
        return {"documents": [], "error": str(e)}