import os
import re
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Import your external configurations
from api_define import llm
from prompt_template import prompt, parser

app = FastAPI(title="Generate Service - AI Quiz Master")

# --- 1. Infrastructure Setup ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
qdrant = QdrantClient(host=QDRANT_HOST, port=6333)
COLLECTION_NAME = "spe_quiz_knowledge"

print("Loading Embedding Model for Retrieval...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    print("WARNING: GEMINI_API_KEY is missing. Generation will fail.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=GOOGLE_API_KEY, 
    temperature=0.3 
)

class GenerateRequest(BaseModel):
    topic: str = "" 
    source_file: str = "All Documents"
    num_questions: int = 1

chain = prompt | llm | parser

# --- 2. The API Endpoint ---
@app.post("/generate")
def generate_quiz(request: GenerateRequest):
    print(f"DEBUG: Generating quiz for topic='{request.topic}' source='{request.source_file}'")
    
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

    print(f"DEBUG: Found {len(search_result.points)} points in Qdrant")

    if not search_result.points:
        raise HTTPException(status_code=404, detail=f"No relevant context found for '{request.topic}' in '{request.source_file}'.")

    context_text = "\n\n".join([hit.payload.get("text", "") for hit in search_result.points])

    try:
        display_topic = request.topic if request.topic else f"the core concepts of {request.source_file}"
        result = chain.invoke({
            "topic": display_topic, 
            "context": context_text,
            "num_questions": request.num_questions
        })
        
        result["source_context"] = context_text 
        return result
        
    except Exception as e:
        error_str = str(e)
        print("====== LLM GENERATION CRASH ======")
        traceback.print_exc()
        print("==================================")
        
        # 1. Check if it's a Google API Rate Limit error
        if "429 RESOURCE_EXHAUSTED" in error_str or "Quota exceeded" in error_str:
            # 2. Extract the exact seconds using regex
            match = re.search(r"retry in (\d+\.?\d*)s", error_str)
            if match:
                wait_time = int(float(match.group(1))) + 1 # Round up to the nearest second
                message = f"Google API Rate Limit Reached. Quota resets in {wait_time} seconds."
            else:
                message = "Google API Rate Limit Reached. Please wait 30 seconds."
                
            # 3. Return a clean 429 HTTP Status Code
            raise HTTPException(status_code=429, detail=message)
            
        elif "503 UNAVAILABLE" in error_str and "high demand" in error_str:
            message = "The Gemini API is currently experiencing high demand. Please try again in a few moments."
            raise HTTPException(status_code=503, detail=message)
            
        # 4. Fallback for any other type of crash
        raise HTTPException(status_code=500, detail=f"LLM failed: {error_str}")
    
@app.get("/health")
def health_check():
    return {"status": "healthy"}