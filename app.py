from fastapi import FastAPI, UploadFile, File
from fastapi import Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from chatbot.config import Settings
from chatbot.memory import MemoryStore
from chatbot.retrieval import Retriever
from chatbot.llm import answer_with_context, vision_answer
import os

app = FastAPI(title="Finance Policy RAG Chatbot")

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

settings = Settings()
memory = MemoryStore(base_dir="sessions", max_turns=6)
retriever = Retriever(settings=settings)

class ChatRequest(BaseModel):
    question: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class PageRequest(BaseModel):
    book_id: str
    page_number: int

class PageResponse(BaseModel):
    book_id: str
    page_number: int
    chunks: List[str]

class VisionRequest(BaseModel):
    prompt: str
    base64_image: str  

@app.get("/")
def read_root():
    """Serve the main HTML interface"""
    return FileResponse('static/index.html')

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = memory.get_history(req.session_id)
    summary = memory.get_summary(req.session_id)

    relevant_docs = retriever.retrieve_relevant_docs(req.question, top_k=5)
    
    contexts = []
    for similarity, book_id, chunk_id, text_content, page_number in relevant_docs:
        contexts.append({
            "text": text_content,
            "book_id": book_id,
            "chunk_id": chunk_id,
            "similarity": similarity,
            "page_number": page_number,
            "page": page_number 
        })

    answer = answer_with_context(
        question=req.question,
        contexts=contexts,
        chat_history=history,
        summary=summary
    )
    print(f"Generated answer: {answer}")

    memory.append_turn(req.session_id, user=req.question, assistant=answer)

    sources = [
        {
            "book_id": c.get("book_id"), 
            "chunk_id": c.get("chunk_id"),
            "similarity": c.get("similarity"),
            "page_number": c.get("page_number"),
            "page": c.get("page_number"),  
            "snippet": c.get("text", "")[:300]
        }
        for c in contexts
    ]

    return ChatResponse(answer=answer, sources=sources)

@app.post("/page", response_model=PageResponse)
def get_page(req: PageRequest):
    """
    Extract all text chunks from a specific book and page number.
    This is the page-based extraction functionality.
    """
    chunks = retriever.query_page(req.book_id, req.page_number)
    
    return PageResponse(
        book_id=req.book_id,
        page_number=req.page_number,
        chunks=chunks
    )

@app.post("/vision")
def vision(req: VisionRequest):
    result = vision_answer(prompt=req.prompt, base64_image=req.base64_image)
    return {"answer": result}
