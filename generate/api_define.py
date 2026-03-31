import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. This magically loads the variables from your .env file
load_dotenv()

# The API key will be injected by the environment, not hardcoded
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set!")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=GOOGLE_API_KEY, 
    temperature=0.7
)