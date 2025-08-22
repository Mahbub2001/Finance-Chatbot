""" 
This script is for testing best practices in PDF table extraction and formatting.
"""

import pdfplumber
import pandas as pd
from pdfplumber.utils import extract_text, get_bbox_overlap, obj_to_bbox
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def process_pdf(pdf_path):
    try:
        pdf = pdfplumber.open(pdf_path)
        all_text = []
        
        table_settings = {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "min_words_vertical": 1,
            "min_words_horizontal": 1
        }

        for page in pdf.pages:
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
                all_text.append(f"\n\n---\n📄 Page {page.page_number}\n\n{page_text}")
            except Exception as e:
                all_text.append(f"\n\n---\n📄 Page {page.page_number}\n\nError processing page: {str(e)}")

        pdf.close()
        return "\n".join(all_text)
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def format_with_llm(extracted_text):
    try:
        client = Groq(api_key=GROQ_API_KEY)

        prompt = """
        You are provided with extracted text from a PDF. Your task is to format the text for clarity while keeping all content exactly the same. Specifically:
        - Preserve all text, including page markers (e.g., ---, 📄 Page X).
        - Ensure tables are formatted using points (e.g., - Item) for each row value under headers.
        - Do not add, remove, or modify any content; only improve the formatting for readability.
        - Maintain the structure of sections, headers, and data as is.
        - If tables are already formatted with points, keep them as is but ensure consistent indentation and spacing.

        Here is the extracted text:

        {extracted_text}

        Format this text and return the result.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt.format(extracted_text=extracted_text)
                }
            ],
        )

        return completion.choices[0].message.content
    except Exception as e:
        return f"Error formatting with LLM: {str(e)}"

pdf_path = r"data/_file-1.pdf"
extracted_text = process_pdf(pdf_path)

if not extracted_text.startswith("Error"):
    formatted_text = format_with_llm(extracted_text)
    print(formatted_text)
else:
    print(extracted_text)