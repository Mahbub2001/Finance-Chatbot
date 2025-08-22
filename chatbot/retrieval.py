from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from chatbot.config import Settings
from chatbot.vectorstore import PineconeStore

class Retriever:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = SentenceTransformer(settings.embedding_model_name)
        self.store = PineconeStore(settings=settings)

    def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text, matching ingest.py approach."""
        return self.model.encode([text]).tolist()[0]

    def query_page(self, book_id: str, page_number: int) -> List[str]:
        """
        Extract all text chunks from a specific book and page number.
        Returns chunks sorted by their order within the page.
        
        Args:
            book_id (str): The book/document identifier
            page_number (int): The page number (1-based)
            
        Returns:
            List[str]: List of text chunks from the specified page
        """
        return self.store.query_page(book_id, page_number, self.settings.embedding_dim)

    def retrieve_relevant_docs(self, query: str, top_k: int = 5) -> List[Tuple[float, str, str, str, int]]:
        """
        Retrieve relevant documents from vector store based on semantic similarity.
        
        Args:
            query (str): The query string
            top_k (int): Number of top results to return
            
        Returns:
            List[Tuple[float, str, str, str, int]]: List of tuples containing 
                (similarity_score, book_id, chunk_id, text_content, page_number)
        """
        try:
            query_embedding = self.embed(query)
            
            raw_results = self.store.query(vector=query_embedding, top_k=top_k * 2)
            
            page_groups = {}
            for result in raw_results:
                page_num = result.get("page_number", 0)
                book_id = result.get("book_id", "unknown")
                key = f"{book_id}_{page_num}"
                
                if key not in page_groups:
                    page_groups[key] = []
                page_groups[key].append(result)
            
            processed_results = []
            for key, chunks in page_groups.items():
                sorted_chunks = sorted(chunks, key=lambda x: x.get("chunk_order", 0))
                
                if len(sorted_chunks) > 1 and len(processed_results) < top_k:
                    combined_text = " ".join([chunk.get("text", "") for chunk in sorted_chunks])
                    max_similarity = max([chunk.get("_score", 0.0) for chunk in sorted_chunks])
                    
                    processed_results.append((
                        max_similarity,
                        sorted_chunks[0].get("book_id", "unknown"),
                        f"combined_{key}",
                        combined_text,
                        sorted_chunks[0].get("page_number", 0)
                    ))
                else:
                    for chunk in sorted_chunks[:1]:  
                        if len(processed_results) < top_k:
                            processed_results.append((
                                chunk.get("_score", 0.0),
                                chunk.get("book_id", "unknown"),
                                chunk.get("_id", "unknown"),
                                chunk.get("text", ""),
                                chunk.get("page_number", 0)
                            ))
            
            processed_results.sort(key=lambda x: x[0], reverse=True)
            return processed_results[:top_k]
            
        except Exception as e:
            print(f"Error retrieving relevant documents: {e}")
            return []

    def retrieve_context_for_llm(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve relevant documents and format them as context for LLM.
        Args:
            query (str): The query string
            top_k (int): Number of top results to return
            
        Returns:
            str: Formatted context string for LLM
        """
        relevant_docs = self.retrieve_relevant_docs(query, top_k)
        
        if not relevant_docs:
            return "No relevant documents found."
        
        context_parts = []
        for i, (similarity, book_id, chunk_id, text_content, page_number) in enumerate(relevant_docs, 1):
            context_parts.append(f"Document {i} (from {book_id}, page {page_number}, similarity: {similarity:.4f}):\n{text_content}")
        
        return "\n\n" + "\n\n".join(context_parts)

    def retrieve(self, query: str, top_k: int = 5, filter: Dict = None) -> List[Dict]:
        """
        Retrieve documents based on query, with optional filtering.
        """
        qvec = self.embed(query)
        results = self.store.query(vector=qvec, top_k=top_k, filter=filter)
        return results
