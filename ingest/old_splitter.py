from langchain_text_splitters import RecursiveCharacterTextSplitter

# We keep the chunk size relatively small (500) so the LLM gets precise context
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)