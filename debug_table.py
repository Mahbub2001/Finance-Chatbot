"""
Debug script to analyze the table data retrieval for "Short Term Financial Objectives"
"""

from chatbot.config import Settings
from chatbot.retrieval import Retriever

def debug_table_retrieval():
    settings = Settings()
    retriever = Retriever(settings)
    
    query = "Short Term Financial Objectives Table 1.2.1"
    
    print("=== DEBUGGING TABLE RETRIEVAL ===")
    print(f"Query: {query}")
    print("-" * 50)
    
    results = retriever.retrieve_relevant_docs(query, top_k=10)
    
    print(f"Found {len(results)} results:")
    print()
    
    for i, (similarity, book_id, chunk_id, text_content, page_number) in enumerate(results, 1):
        print(f"RESULT {i}:")
        print(f"  Similarity: {similarity:.4f}")
        print(f"  Book: {book_id}")
        print(f"  Page: {page_number}")
        print(f"  Chunk ID: {chunk_id}")
        print(f"  Content Length: {len(text_content)} chars")
        print(f"  Content Preview: {text_content[:200]}...")
        print("-" * 50)
    
    print("\n=== DIRECT PAGE 2 QUERY ===")
    page_chunks = retriever.query_page("file-1.pdf", 2)
    
    print(f"Found {len(page_chunks)} chunks on page 2:")
    for i, chunk in enumerate(page_chunks, 1):
        print(f"\nCHUNK {i} (Page 2):")
        print(f"Content: {chunk}")
        print("-" * 30)

if __name__ == "__main__":
    debug_table_retrieval()
