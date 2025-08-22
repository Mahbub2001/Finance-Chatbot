from typing import List, Dict, Any
import base64
import os
from groq import Groq
from chatbot.config import Settings

settings = Settings()

try:
    groq_client = Groq(api_key=settings.groq_api_key)
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    try:
        groq_client = Groq(
            api_key=settings.groq_api_key,
        )
    except Exception as e2:
        print(f"Alternative Groq initialization also failed: {e2}")
        groq_client = None

SYSTEM_PROMPT = """You answer questions about a financial policy document using provided context.
Rules:
- Use the supplied CONTEXT for facts. If missing, say you don't know.
- Be concise and cite page numbers like (p. 7) based on the context metadata.
- If the user asks a follow-up like "what about debt?", assume same topic as recent turn.
- Use numbered bullets when listing items.
- When referencing tables or data, be specific about the source table and include relevant values.
- If data spans multiple years, present it clearly year by year when possible.
- Always include proper citations with page numbers from the context.
- For table references like "Table 1.2.1", look for ALL items or objectives listed in that table.
- If a table contains multiple rows/items, list ALL of them comprehensively.
- Pay special attention to headings and subheadings in the context to understand the complete structure.
"""

def _format_context(contexts: List[Dict[str, Any]]) -> str:
    parts = []
    for c in contexts:
        pg = c.get("page_number") or c.get("page") or "unknown"
        book_id = c.get("book_id", "unknown")
        txt = c.get("text","").strip().replace("\n"," ")
        parts.append(f"[{book_id}, p.{pg}] {txt}")
    return "\n".join(parts[:10])

def answer_with_context(question: str, contexts: List[Dict[str, Any]], chat_history: List[Dict[str,str]], summary: str) -> str:
    if groq_client is None:
        return "Error: Groq client not properly initialized. Please check your API key and dependencies."
    
    context_block = _format_context(contexts)
    history_block = "\n".join([f"{h['role']}: {h['content']}" for h in chat_history[-6:]])
    prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
{context_block}

SUMMARY:
{summary}

CHAT_HISTORY (most recent turns):
{history_block}

USER QUESTION:
{question}

If multiple chunks contain parts of the same table, combine the information.\n
Take the {context_block} and use/utilize it to answer the question.\n
Write the best possible answer with citations to pages you used.
"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":prompt},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"

def vision_answer(prompt: str, base64_image: str) -> str:
    if groq_client is None:
        return "Error: Groq client not properly initialized. Please check your API key and dependencies."
    
    if base64_image.startswith("data:"):
        image_url = base64_image
    else:
        image_url = f"data:image/jpeg;base64,{base64_image}"

    try:
        resp = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating vision response: {e}"
