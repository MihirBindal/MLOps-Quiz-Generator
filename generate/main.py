import os
import re
import time
import json
import logging
import traceback
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Import your external configurations
from api_define import llm
from prompt_template import prompt, parser

# --- 1. Structured Logging Setup ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "service": "generate-api",
            "message": record.getMessage(),
        }
        if hasattr(record, "app_data"):
            log_data.update(record.app_data)
        return json.dumps(log_data)

logger = logging.getLogger("generate-api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

app = FastAPI(title="Generate Service - AI Quiz Master")

# --- 2. Infrastructure Setup ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
qdrant = QdrantClient(host=QDRANT_HOST, port=6333)
COLLECTION_NAME = "spe_quiz_knowledge"

logger.info("Loading Embedding Model for Retrieval...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    logger.warning("GEMINI_API_KEY is missing. Generation will fail.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=GOOGLE_API_KEY, 
    temperature=0.3 
)

class GenerateRequest(BaseModel):
    topic: str = "" 
    source_file: str = "All Documents"
    num_questions: int = 1

# --- 3. The API Endpoint ---
@app.post("/generate")
def generate_quiz(request: GenerateRequest):
    start_time = time.time()
    
    search_query = request.topic if request.topic else "core concepts, main ideas, summary, definitions"
    query_vector = embeddings_model.embed_query(search_query)

    query_filter = None
    if request.source_file != "All Documents":
        query_filter = Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=request.source_file))]
        )

    chunks_to_fetch = 5 if request.num_questions == 1 else 10
    threshold = 0.5 if request.topic else 0.2 

    search_result = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter, 
        limit=chunks_to_fetch,
        score_threshold=threshold
    )

    qdrant_scores = [hit.score for hit in search_result.points]
    max_score = max(qdrant_scores) if qdrant_scores else 0.0

    if not search_result.points:
        logger.warning(f"No relevant context found", extra={"app_data": {
            "event": "generate_404",
            "topic": request.topic,
            "source": request.source_file,
            "max_score": max_score
        }})
        raise HTTPException(status_code=404, detail=f"No relevant context found for '{request.topic}' in '{request.source_file}'.")

    context_text = "\n\n".join([hit.payload.get("text", "") for hit in search_result.points])

    try:
        display_topic = request.topic if request.topic else f"the core concepts of {request.source_file}"
        
        # Invoke LLM and capture response for metadata
        prompt_value = prompt.format(
            topic=display_topic, 
            context=context_text,
            num_questions=request.num_questions
        )
        response = llm.invoke(prompt_value)
        result = parser.parse(response.content)
        
        # Extract token usage
        usage = getattr(response, "usage_metadata", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        
        latency = time.time() - start_time
        
        logger.info(f"Quiz generated successfully", extra={"app_data": {
            "event": "generate_success",
            "topic": request.topic if request.topic else f"Full Doc: {request.source_file}",
            "source": request.source_file,
            "latency_sec": round(latency, 3),
            "qdrant_max_score": round(max_score, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "num_questions": request.num_questions
        }})
        
        result["source_context"] = context_text 
        return result
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"LLM generation failed: {error_str}", extra={"app_data": {
            "event": "generate_error",
            "error": error_str
        }})
        
        if "429 RESOURCE_EXHAUSTED" in error_str or "Quota exceeded" in error_str:
            match = re.search(r"retry in (\d+\.?\d*)s", error_str)
            wait_time = int(float(match.group(1))) + 1 if match else 30
            raise HTTPException(status_code=429, detail=f"Google API Rate Limit Reached. Quota resets in {wait_time} seconds.")
            
        elif "503 UNAVAILABLE" in error_str and "high demand" in error_str:
            raise HTTPException(status_code=503, detail="The Gemini API is currently experiencing high demand. Please try again in a few moments.")
            
        raise HTTPException(status_code=500, detail=f"LLM failed: {error_str}")
    
@app.get("/health")
def health_check():
    return {"status": "healthy"}