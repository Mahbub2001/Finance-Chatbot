from typing import List, Dict, Any
from pinecone import Pinecone
from chatbot.config import Settings

class PineconeStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.index = self.pc.Index(self.settings.pinecone_index)

    def batch_upsert(self, to_upsert: List[tuple], batch_size: int = 100):
        """Splits the data into smaller batches to avoid Pinecone's 4MB limit."""
        for i in range(0, len(to_upsert), batch_size):
            batch = to_upsert[i : i + batch_size]
            self.index.upsert(vectors=batch)
            print(f"Upserted batch {i//batch_size + 1}/{(len(to_upsert) // batch_size) + 1}")

    def upsert(self, vectors: List[Dict[str, Any]]):
        # vectors: [{id, values, metadata}]
        self.index.upsert(vectors=vectors)

    def query(self, vector: List[float], top_k: int = 5, filter: Dict = None) -> List[Dict[str, Any]]:
        res = self.index.query(
            vector=vector, 
            top_k=top_k, 
            include_metadata=True,
            filter=filter
        )
        out = []
        for match in res.matches or []:
            md = match.metadata or {}
            md["_score"] = float(match.score) if match.score is not None else None
            md["_id"] = match.id  
            out.append(md)
        return out

    def query_page(self, book_id: str, page_number: int, embedding_dim: int = 384) -> List[str]:
        """Query all text chunks from a specific book and page number."""
        dummy_vector = [0.0] * embedding_dim
        filter_dict = {
            'book_id': {'$eq': book_id},
            'page_number': {'$eq': page_number}
        }
        
        try:
            results = self.index.query(
                vector=dummy_vector,
                top_k=10000,
                include_metadata=True,
                filter=filter_dict
            )
            sorted_chunks = sorted(results.matches, key=lambda x: x.metadata.get('chunk_order', 0))
            return [chunk.metadata.get('text', '') for chunk in sorted_chunks]
        except Exception as e:
            print(f"Error querying Pinecone: {e}")
            return []
