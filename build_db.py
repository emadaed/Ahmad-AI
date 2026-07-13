import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

KNOWLEDGE_DIR = "knowledge"
DB_DIR = "chroma_db"

print("Starting Knowledge Base Ingestion...")

# 1. Load all text files from the knowledge directory
loader = DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.txt", loader_cls=TextLoader)
documents = loader.load()

if not documents:
    print("No documents found in the 'knowledge' folder. Please add some .txt files.")
    exit()

print(f"Loaded {len(documents)} document(s).")

# 2. Split text into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)
print(f"Split into {len(chunks)} chunk(s).")

# 3. Create embeddings using Ollama and save to ChromaDB
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings, 
    persist_directory=DB_DIR
)

print(f"Success! Vector database saved to ./{DB_DIR}")