"""
This is a test script for retrieving and displaying relevant documents from a Pinecone index.
"""
import os
import time
from uuid import uuid4
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

data_folder = "./data"
chunk_size = 800
chunk_overlap = 50
check_interval = 10
pinecone_api_key = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
index_name = "finance-policy"
index = pc.Index(index_name)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def query_page(book_id, page_number):
    """Query all text chunks from a specific book and page number."""
    dummy_vector = [0.0] * model.get_sentence_embedding_dimension()
    filter = {
        'book_id': {'$eq': book_id},
        'page_number': {'$eq': page_number}
    }
    
    try:
        results = index.query(
            vector=dummy_vector,
            top_k=10000,
            include_metadata=True,
            filter=filter
        )
        # Sort chunks by their order within the page
        sorted_chunks = sorted(results.matches, key=lambda x: x.metadata['chunk_order'])
        return [chunk.metadata['text'] for chunk in sorted_chunks]
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []
    
book_id = ""  # Original filename before processing
page_number = 1  # 1-based page number

results = query_page(book_id, page_number)
for i, text in enumerate(results):
    print(f"Chunk {i+1}: {text}")


def retrieve_relevant_docs(query, top_k=5, model_name="sentence-transformers/all-MiniLM-L6-v2", index=None):
    """
    Retrieve relevant documents from Pinecone based on the query.

    Args:
        query (str): The query string.
        top_k (int): Number of top results to return.
        model_name (str): Name of the Sentence Transformer model to use.
        index: Pinecone index object.

    Returns:
        list: List of tuples containing (similarity, doc_id, chunk_id, chunk).
    """
    if index is None:
        raise ValueError("Pinecone index must be provided.")

    # Initialize the Sentence Transformer model
    model = SentenceTransformer(model_name)

    # Generate query embedding
    query_embedding = model.encode(query).tolist()

    # Query Pinecone index
    try:
        query_results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []

    # Process results
    results = []
    for match in query_results.matches:
        similarity = match.score  # Pinecone returns cosine similarity
        doc_id = match.metadata.get("book_id", "unknown")  # Retrieve book_id from metadata
        chunk_id = match.id  # Use the Pinecone ID as chunk_id
        chunk = match.metadata.get("text", "")  # Retrieve text from metadata
        results.append((similarity, doc_id, chunk_id, chunk))

    return results


# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(index_name)

# Query for relevant documents
query = "Under which sections of the Financial Management Act 1996 is the presentation and preparation of the Territory’s Budget provided?"
results = retrieve_relevant_docs(query, top_k=3, index=index)

# Display results
for similarity, doc_id, chunk_id, chunk in results:
    print(f"Similarity: {similarity:.4f}")
    print(f"Book ID: {doc_id}")
    print(f"Chunk ID: {chunk_id}")
    print(f"Text: {chunk}")
    print("-" * 50)