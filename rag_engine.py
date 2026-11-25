import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_DIR = "./faiss_index"

class RAGEngine:
    def __init__(self, pdf_path: str = "./data/college_handbook.pdf"):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Load index if exists, otherwise create it from PDF
        if os.path.exists(INDEX_DIR):
            self.vector_store = FAISS.load_local(
                INDEX_DIR, self.embeddings, allow_dangerous_deserialization=True
            )
        else:
            self.vector_store = self._build_vector_store(pdf_path)

    def _build_vector_store(self, pdf_path):
        if not os.path.exists(pdf_path):
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            raise FileNotFoundError(f"Please place a PDF at '{pdf_path}'!")
            
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = text_splitter.split_documents(docs)
        
        vector_store = FAISS.from_documents(splits, self.embeddings)
        vector_store.save_local(INDEX_DIR)
        return vector_store

    def query(self, user_question: str) -> dict:
        results = self.vector_store.similarity_search(user_question, k=2)
        context = "\n---\n".join([doc.page_content for doc in results])
        
        prompt = f"""You are a helpful college assistant. Answer concise and naturally in under 2-3 short sentences.
Context:
{context}

Question: {user_question}
Answer:"""

        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        answer = response.choices[0].message.content.strip()
        return {"answer": answer, "sources": [doc.page_content[:100] + "..." for doc in results]}