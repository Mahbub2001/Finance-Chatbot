import os
import time
from uuid import uuid4
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv
import pdfplumber
import pandas as pd
from pdfplumber.utils import extract_text, get_bbox_overlap, obj_to_bbox
from groq import Groq
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

data_folder = "./data"
chunk_size = 1000
chunk_overlap = 100
check_interval = 10
pinecone_api_key = os.getenv("PINECONE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
index_name = "finance-policy"
index = pc.Index(index_name)

# Process PDF files with table extraction. This is done using pdfplumber.
def process_pdf_with_tables(pdf_path):
    """Extract PDF content with proper table formatting using pdfplumber"""
    try:
        pdf = pdfplumber.open(pdf_path)
        all_pages = []
        
        table_settings = {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "min_words_vertical": 1,
            "min_words_horizontal": 1
        }

        for page in pdf.pages:
            page_number = page.page_number
            filtered_page = page
            chars = filtered_page.chars

            try:
                for table in page.find_tables(table_settings=table_settings):
                    try:
                        first_table_char = page.crop(table.bbox).chars[0]
                    except IndexError:
                        first_table_char = {"x0": table.bbox[0], "y0": table.bbox[1], "text": ""}

                    filtered_page = filtered_page.filter(
                        lambda obj: get_bbox_overlap(obj_to_bbox(obj), table.bbox) is None
                    )
                    chars = filtered_page.chars
                    # Create DataFrame from table data.
                    df = pd.DataFrame(table.extract())
                    if df.empty:
                        continue

                    headers = list(df.iloc[0])
                    df = df.drop(0).reset_index(drop=True) if len(df) > 1 else df

                    table_text = []
                    for col_idx, header in enumerate(headers):
                        if header is None or str(header).strip() == "":
                            continue
                        col_values = df[col_idx].dropna().tolist()
                        section = f"{header.strip()}:\n" + "\n".join(
                            f"- {str(val).strip()}" for val in col_values if str(val).strip()
                        )
                        table_text.append(section)

                    formatted_table = "\n\n".join(table_text)
                    chars.append(first_table_char | {"text": formatted_table})

                page_text = extract_text(chars, layout=True)
                all_pages.append({
                    'page_number': page_number,
                    'content': page_text
                })
                
            except Exception as e:
                print(f"Error processing page {page_number}: {str(e)}")
                page_text = page.extract_text()
                all_pages.append({
                    'page_number': page_number,
                    'content': page_text or ""
                })

        pdf.close()
        return all_pages
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return []

# In document there can be tables which need to be reformatted because of their structure. So I use LLM to format them as descriptive text.
def format_with_llm(extracted_text, page_number):
    """Format extracted text using LLM for better structure"""
    try:
        client = Groq(api_key=groq_api_key)

        prompt = f"""
        You are provided with extracted text from page {page_number} of a financial policy PDF.\n
        Strictly dont change any content.\n
        Only utilize the tables and rewrite table as descriptive text instead of table formate.\n
        - Keep any table numbers/names (e.g., "Table 1.2.1") intact
        
        Here is the extracted text from page {page_number}:

        {extracted_text}

        Format this text for optimal readability and return the result.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )

        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Error formatting with LLM: {str(e)}")
        return extracted_text  

# Batch upsert function: this is used to split the data into smaller batches for efficient upserting.
def batch_upsert(index, to_upsert, batch_size=100):
    """Splits the data into smaller batches to avoid Pinecone's 4MB limit."""
    for i in range(0, len(to_upsert), batch_size):
        batch = to_upsert[i : i + batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted batch {i//batch_size + 1}/{(len(to_upsert) // batch_size) + 1}")

# Ingest file with LLM formatting
def ingest_file_with_llm_formatting(file_path):
    """Enhanced ingestion with LLM formatting for better content quality"""
    if not file_path.lower().endswith('.pdf'):
        print(f"Skipping non-PDF file: {file_path}")
        return
    
    print(f"Starting LLM-enhanced ingestion for: {file_path}")
    
    pages_data = process_pdf_with_tables(file_path)
    
    if not pages_data:
        print(f"No content extracted from {file_path}")
        return
    
    formatted_pages = []
    for page_data in pages_data:
        page_number = page_data['page_number']
        raw_content = page_data['content']
        
        if raw_content.strip():
            print(f"Formatting page {page_number} with LLM...")
            formatted_content = format_with_llm(raw_content, page_number)
            formatted_pages.append({
                'page_number': page_number,
                'content': formatted_content,
                'raw_content': raw_content
            })
        else:
            print(f"Skipping empty page {page_number}")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap, 
        separators=["\n\n", "\n", " ", ""]
    )
    # Split formatted pages into chunks
    all_chunks = []
    for page_data in formatted_pages:
        page_number = page_data['page_number']
        formatted_content = page_data['content']
        
        chunks = text_splitter.split_text(formatted_content)
        
        for chunk_order, chunk_text in enumerate(chunks):
            chunk_data = {
                'content': chunk_text,
                'page_number': page_number,
                'chunk_order': chunk_order,
                'source_file': file_path
            }
            all_chunks.append(chunk_data)
    
    print(f"Creating embeddings for {len(all_chunks)} chunks...")
    
    uuids = [str(uuid4()) for _ in range(len(all_chunks))]
    texts = [chunk['content'] for chunk in all_chunks]
    embeddings_data = model.encode(texts).tolist()

    book_id = os.path.basename(file_path)
    to_upsert = []
    
    for uuid, embedding, chunk_data in zip(uuids, embeddings_data, all_chunks):
        metadata = {
            'text': chunk_data['content'],
            'book_id': book_id,
            'page_number': chunk_data['page_number'],
            'chunk_order': chunk_data['chunk_order'],
            'llm_formatted': True
        }
        to_upsert.append((uuid, embedding, metadata))
    
    batch_upsert(index, to_upsert, batch_size=50)
    print(f"Successfully ingested {len(all_chunks)} LLM-formatted chunks from {file_path}")

# Query a specific page
def query_page(book_id, page_number):
    """Query all text chunks from a specific book and page number."""
    dummy_vector = [0.0] * model.get_sentence_embedding_dimension()
    filter_dict = {
        'book_id': {'$eq': book_id},
        'page_number': {'$eq': page_number}
    }
    
    try:
        results = index.query(
            vector=dummy_vector,
            top_k=10000,
            include_metadata=True,
            filter=filter_dict
        )
        sorted_chunks = sorted(results.matches, key=lambda x: x.metadata['chunk_order'])
        return [chunk.metadata['text'] for chunk in sorted_chunks]
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []

def main_loop():
    """Process any unprocessed files in the data folder"""
    while True:
        processed_any = False
        for filename in os.listdir(data_folder):
            if not filename.startswith("_"):
                file_path = os.path.join(data_folder, filename)
                ingest_file_with_llm_formatting(file_path)
                
                # Mark as processed
                new_filename = "_" + filename
                new_file_path = os.path.join(data_folder, new_filename)
                os.rename(file_path, new_file_path)
                processed_any = True
        
        if not processed_any:
            print("No new files to process. Waiting...")
        
        time.sleep(check_interval)

if __name__ == "__main__":
    test_file = "./data/_file-1.pdf"
    
    if os.path.exists(test_file):
        print("Testing LLM-enhanced ingestion...")
        ingest_file_with_llm_formatting(test_file)
    else:
        print("Available files in ./data/:")
        if os.path.exists("./data/"):
            for f in os.listdir("./data/"):
                print(f"  - {f}")
        
