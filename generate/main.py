import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from api_define import llm
from prompt_template import prompt, parser
from qdrant_client.models import Filter, FieldCondition, MatchValue

app = FastAPI(title="Generate Service - AI Quiz Master")

# --- 1. Infrastructure Setup ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
qdrant = QdrantClient(host=QDRANT_HOST, port=6333)
COLLECTION_NAME = "spe_quiz_knowledge"

print("Loading Embedding Model for Retrieval...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# We grab the API key from the Linux environment
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    print("WARNING: GEMINI_API_KEY is missing. Generation will fail.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", # <-- THIS IS THE ONLY CHANGE
    google_api_key=GOOGLE_API_KEY, 
    temperature=0.3 
)

# --- 2. Data Schemas ---
class QuizQuestion(BaseModel):
    question: str = Field(description="The quiz question string")
    options: list[str] = Field(description="List of 4 possible answers")
    correct_answer: str = Field(description="The correct answer string")
    explanation: str = Field(description="Why this is the correct answer based on the text")

class GenerateRequest(BaseModel):
    topic: str = "" # Now optional
    source_file: str = "All Documents"
    num_questions: int = 1

chain = prompt | llm | parser

# --- 4. The API Endpoint ---
@app.post("/generate")
async def generate_quiz(request: GenerateRequest):
    # The "Secret Prompt" workaround for auto-generating without a topic
    search_query = request.topic if request.topic else "core concepts, main ideas, summary, definitions"
    query_vector = embeddings_model.embed_query(search_query)

    # 1. THE METADATA FILTER
    query_filter = None
    if request.source_file != "All Documents":
        query_filter = Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=request.source_file))]
        )

    # Grab more chunks if we need more questions
    chunks_to_fetch = 5 if request.num_questions == 1 else 10
    
    # We drop the strict score_threshold if we are doing a generic "Auto-Generate"
    threshold = 0.5 if request.topic else 0.2 

    search_result = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter, 
        limit=chunks_to_fetch,
        score_threshold=threshold
    )

    if not search_result.points:
        raise HTTPException(status_code=404, detail="No relevant context found in this document.")

    # Extract the payload from the .points list
    context_text = "\n\n".join([hit.payload.get("text", "") for hit in search_result.points])

    try:
        # Pass the variables to your prompt
        display_topic = request.topic if request.topic else f"the core concepts of {request.source_file}"
        result = chain.invoke({
            "topic": display_topic, 
            "context": context_text,
            "num_questions": request.num_questions
        })
        
        result["source_context"] = context_text 
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM failed: {str(e)}")
    
@app.get("/health")
async def health_check():
    return {"status": "healthy"}