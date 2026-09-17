import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from groq import Groq

# 1. Load Environment Variables (.env File)
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY `.env` file mein nahi mili!")

# 2. Document Load (Data folder)
print("1. Document load ho raha hai...")
file_path = os.path.join("data", "sample_contract.txt")

with open(file_path, "r", encoding="utf-8") as f:
    text_content = f.read()

documents = [Document(page_content=text_content)]

# 3. Document Chunking
print("2. Chunks banaye ja rahe hain...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

# 4. Vector Embeddings
print("3. Vector Embeddings generate ho rahe hain...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 5. Chroma Vector Store
print("4. Chroma Vector Store mein save ho raha hai...")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 6. Retriever Setup
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 7. Groq Client Initialize
client = Groq(api_key=groq_api_key)

# 8. User Queries Execution
queries = [
    "What is the duration of this contract?",
    "What are the payment terms?",
    "How can this agreement be terminated?"
]

print("\n=== Legal RAG Pipeline Answers ===\n")

# Aap ki key par active verified models
VERIFIED_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b"
]

for query in queries:
    relevant_docs = retriever.invoke(query)
    context = "\n".join([doc.page_content for doc in relevant_docs])

    prompt = f"""
You are a Legal AI Advisor. Answer the user's question based strictly on the provided contract context.
If the answer is not in the context, state that clearly.

Context:
{context}

Question: {query}
Answer:"""

    response_content = None
    
    for model_name in VERIFIED_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            response_content = response.choices[0].message.content
            if response_content:
                break
        except Exception as e:
            continue

    print(f"Q: {query}")
    print(f"A: {response_content}\n")
    print("-" * 50)