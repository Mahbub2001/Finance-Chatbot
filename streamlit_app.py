import streamlit as st
import requests
import json
from typing import Dict, List, Any
import time
import plotly.express as px
import pandas as pd

# Enhanced page configuration
st.set_page_config(
    page_title="Finance Policy AI Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@financebot.com',
        'Report a bug': 'mailto:bugs@financebot.com',
        'About': "# Finance Policy AI Assistant\nPowered by advanced RAG technology"
    }
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f2ff 100%);
    }
    
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #2196f3;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-left: 4px solid #9c27b0;
        margin-right: 2rem;
    }
    
    .source-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #ff9800;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e9ecef;
        text-align: center;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    .status-connected {
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        display: inline-block;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        display: inline-block;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }
    
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        border: 1px solid #dee2e6;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stChatInputContainer {
        position: sticky !important;
        bottom: 0 !important;
        background: transparent !important;
        z-index: 999 !important;
        padding: 10px 0 !important;
        border-top: none !important;
        margin-top: 20px !important;
    }
    
    .stChatMessage {
        margin-bottom: 10px !important;
    }
    
    [data-testid="stChatInput"] {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 1000 !important;
        background: transparent !important;
        padding: 10px 0 !important;
    }
    
    [data-testid="stChatInput"] > div {
        background: transparent !important;
    }
    
    [data-testid="stChatInput"] input {
        background: transparent !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 25px !important;
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://localhost:8000"

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"user-{int(time.time())}"
    if "total_queries" not in st.session_state:
        st.session_state.total_queries = 0
    if "api_status" not in st.session_state:
        st.session_state.api_status = "unknown"

def check_api_status():
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=3)
        if response.status_code == 200:
            st.session_state.api_status = "connected"
            return True
        else:
            st.session_state.api_status = "error"
            return False
    except:
        st.session_state.api_status = "disconnected"
        return False

def call_chat_api(question: str, session_id: str) -> Dict:
    try:
        with st.spinner("🧠 AI is analyzing your question..."):
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "question": question,
                    "session_id": session_id
                },
                timeout=45
            )
            response.raise_for_status()
            st.session_state.total_queries += 1
            return response.json()
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. The AI might be processing a complex query.")
        return {"answer": "Sorry, the request timed out. Please try a simpler question.", "sources": []}
    except requests.exceptions.RequestException as e:
        st.error(f"🔌 Connection Error: {e}")
        return {"answer": "Error: Could not connect to the AI backend. Please check if the server is running.", "sources": []}

def call_page_api(book_id: str, page_number: int) -> Dict:
    """Call the FastAPI page extraction endpoint"""
    try:
        with st.spinner(f"📖 Extracting content from page {page_number}..."):
            response = requests.post(
                f"{API_BASE_URL}/page",
                json={
                    "book_id": book_id,
                    "page_number": page_number
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error extracting page: {e}")
        return {"book_id": book_id, "page_number": page_number, "chunks": []}

def display_sources(sources: List[Dict]):
    """Enhanced source display with better formatting"""
    if sources:
        st.markdown("### 📚 **Source Documents**")
        
        for i, source in enumerate(sources, 1):
            with st.expander(f"📄 Source {i}: {source.get('book_id', 'Unknown')} (Page {source.get('page_number', 'N/A')})", expanded=i==1):
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    similarity = source.get('similarity', 0)
                    if similarity > 0.7:
                        st.success(f"**Relevance:** {similarity:.1%}")
                    elif similarity > 0.5:
                        st.warning(f"**Relevance:** {similarity:.1%}")
                    else:
                        st.info(f"**Relevance:** {similarity:.1%}")
                
                with col2:
                    st.metric("Page", source.get('page_number', 'N/A'))
                
                with col3:
                    chunk_id = source.get('chunk_id', 'N/A')
                    if len(chunk_id) > 20:
                        chunk_id = chunk_id[:17] + "..."
                    st.code(f"ID: {chunk_id}", language="text")
                
                st.markdown("**Content Preview:**")
                content = source.get('snippet', source.get('text', 'No content available'))
                st.markdown(f"> {content[:400]}{'...' if len(content) > 400 else ''}")

def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header fade-in">
        <h1>💰 Finance Policy AI Assistant</h1>
        <p>Ask intelligent questions about financial policy documents using advanced AI</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ **Control Panel**")
        
        # API Status
        api_connected = check_api_status()
        status_html = f"""
        <div class="{'status-connected' if api_connected else 'status-error'}">
            {'🟢 API Connected' if api_connected else '🔴 API Disconnected'}
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Session Management
        st.markdown("### 👤 **Session**")
        new_session_id = st.text_input(
            "Session ID:", 
            value=st.session_state.session_id,
            help="Change this to start a new conversation"
        )
        
        if new_session_id != st.session_state.session_id:
            st.session_state.session_id = new_session_id
            st.session_state.messages = []
            st.success("New session started!")
            time.sleep(1)
            st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New Chat", use_container_width=True):
                st.session_state.messages = []
                st.success("Chat cleared!")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 📊 **Session Stats**")
        
        metrics_data = [
            ("💬", "Messages", len(st.session_state.messages)),
            ("❓", "Questions", len([m for m in st.session_state.messages if m["role"] == "user"])),
            ("🔍", "Total Queries", st.session_state.total_queries)
        ]
        
        for icon, label, value in metrics_data:
            st.metric(f"{icon} {label}", value)
        
        st.markdown("---")
        
        st.markdown("### ⚡ **Quick Actions**")
        
        quick_questions = [
            "What are the short term financial objectives?",
            "What is the government's debt policy?",
            "Show me budget estimates for 2005-06",
            "What are the key financial measures?"
        ]
        
        for question in quick_questions:
            if st.button(f"💡 {question[:35]}...", key=f"quick_{hash(question)}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()

def chat_interface():
    st.markdown("## 💬 **AI Chat Assistant**")
    st.markdown("*Ask questions about financial policies and get intelligent, sourced answers*")
    
    chat_container = st.container()
    
    with chat_container:
        if hasattr(st.session_state, 'pending_question'):
            question = st.session_state.pending_question
            delattr(st.session_state, 'pending_question')
            
            st.session_state.messages.append({"role": "user", "content": question})
            
            response = call_chat_api(question, st.session_state.session_id)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response["answer"],
                "sources": response.get("sources", [])
            })
        
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    display_sources(message["sources"])
    

    input_container = st.container()
    
    with input_container:
        st.markdown("<br>", unsafe_allow_html=True)
        
        prompt = st.chat_input("Ask me anything about financial policies... 💭", key="main_chat_input")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            response = call_chat_api(prompt, st.session_state.session_id)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response["answer"],
                "sources": response.get("sources", [])
            })
            
            st.rerun()

def page_extraction_interface():
    st.markdown("## 📄 **Document Page Extractor**")
    st.markdown("*Extract and view complete content from specific document pages*")
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            book_id = st.selectbox(
                "📚 Select Document:",
                options=["_file-1.pdf", "custom"],
                help="Choose a document to extract from"
            )
            
            if book_id == "custom":
                book_id = st.text_input("Enter custom document ID:")
        
        with col2:
            page_number = st.number_input(
                "📖 Page Number:", 
                min_value=1, 
                max_value=1000,
                value=1,
                help="Enter the page number to extract"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            extract_btn = st.button("🔍 **Extract Page**", type="primary", use_container_width=True)
    
    if extract_btn and book_id:
        result = call_page_api(book_id, page_number)
        
        if result.get("chunks"):
            st.success(f"✅ Successfully extracted {len(result['chunks'])} chunks from page {page_number}")
            
            st.markdown(f"### 📖 **Content from {book_id} - Page {page_number}**")
            
            tab1, tab2 = st.tabs(["📝 Formatted View", "🔍 Raw Chunks"])
            
            with tab1:
                combined_content = "\n\n".join(result["chunks"])
                st.markdown("**Complete Page Content:**")
                st.markdown(combined_content)
            
            with tab2:
                for i, chunk in enumerate(result["chunks"], 1):
                    with st.expander(f"📋 Chunk {i} ({len(chunk)} characters)", expanded=i==1):
                        st.markdown(chunk)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button(f"📋 Copy Chunk {i}", key=f"copy_{i}"):
                                st.code(chunk, language="text")
                        with col2:
                            if st.button(f"🔍 Analyze Chunk {i}", key=f"analyze_{i}"):
                                st.info(f"**Word Count:** {len(chunk.split())} | **Character Count:** {len(chunk)}")
        else:
            st.error(f"❌ No content found for page {page_number} in {book_id}")
            st.info("💡 Try a different page number or check if the document ID is correct.")

def analytics_interface():
    st.markdown("## 📊 **Analytics Dashboard**")
    st.markdown("*View conversation statistics and system performance*")
    
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("💬", "Total Messages", len(st.session_state.messages), "messages"),
        ("❓", "User Questions", len([m for m in st.session_state.messages if m["role"] == "user"]), "questions"),
        ("🤖", "AI Responses", len([m for m in st.session_state.messages if m["role"] == "assistant"]), "responses"),
        ("🔍", "Total Queries", st.session_state.total_queries, "queries")
    ]
    
    for i, (icon, label, value, key) in enumerate(metrics):
        with [col1, col2, col3, col4][i]:
            st.metric(f"{icon} {label}", value, delta=None)
    
    if st.session_state.messages:
        st.markdown("---")
        
        st.markdown("### 📈 **Conversation Timeline**")
        
        timeline_data = []
        for i, msg in enumerate(st.session_state.messages):
            timeline_data.append({
                "Message": i + 1,
                "Role": msg["role"].title(),
                "Length": len(msg["content"]),
                "Sources": len(msg.get("sources", []))
            })
        
        df = pd.DataFrame(timeline_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(df, x="Message", y="Length", color="Role", 
                         title="Message Length by Turn",
                         color_discrete_map={"User": "#667eea", "Assistant": "#764ba2"})
            fig1.update_layout(height=400)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            assistant_msgs = df[df["Role"] == "Assistant"]
            if not assistant_msgs.empty:
                fig2 = px.line(assistant_msgs, x="Message", y="Sources", 
                              title="Sources Referenced Over Time",
                              markers=True)
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("### 💬 **Conversation History**")
        
        for i, message in enumerate(st.session_state.messages):
            role_icon = "🧑" if message["role"] == "user" else "🤖"
            role_color = "blue" if message["role"] == "user" else "violet"
            
            with st.expander(f"{role_icon} {message['role'].title()} - Message {i+1}", expanded=False):
                st.markdown(f"**Content:** {message['content'][:200]}{'...' if len(message['content']) > 200 else ''}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Length:** {len(message['content'])} chars")
                with col2:
                    st.info(f"**Words:** {len(message['content'].split())}")
                with col3:
                    if "sources" in message:
                        st.info(f"**Sources:** {len(message['sources'])}")

def main():
    initialize_session_state()
    
    render_header()
    
    render_sidebar()
    
    tab1, tab2, tab3, tab4 = st.tabs(["💬 **AI Chat**", "📄 **Page Extract**", "📊 **Analytics**", "ℹ️ **About**"])
    
    with tab1:
        chat_interface()
    
    with tab2:
        page_extraction_interface()
    
    with tab3:
        analytics_interface()
    
    with tab4:
        st.markdown("## ℹ️ **About Finance Policy AI Assistant**")
        st.markdown("""
        This application uses advanced **Retrieval-Augmented Generation (RAG)** technology to provide 
        intelligent answers about financial policy documents.
        
        ### 🔧 **Technology Stack:**
        - **Frontend:** Streamlit with custom CSS
        - **Backend:** FastAPI with async processing
        - **AI Model:** Groq (Llama 3.3 70B)
        - **Vector Database:** Pinecone
        - **Embeddings:** Sentence Transformers
        - **Document Processing:** PDFPlumber + LLM Enhancement
        
        ### 📋 **Features:**
        - ✅ Intelligent document Q&A
        - ✅ Source citation with page numbers
        - ✅ Page-specific content extraction
        - ✅ Conversation memory
        - ✅ Real-time analytics
        - ✅ Quick question suggestions
        
        ### 🚀 **Getting Started:**
        1. Ask questions in natural language
        2. Get AI-powered answers with sources
        3. Extract specific pages for detailed review
        4. View analytics to track your usage
        
        ### 🔗 **Links:**
        - [FastAPI Backend]({API_BASE_URL}/docs) - API Documentation
        - [Source Code](https://github.com/your-repo) - GitHub Repository
        """)
    
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <strong>Finance Policy AI Assistant</strong> | 
            Powered by <a href='https://groq.com/' target='_blank'>Groq</a> + 
            <a href='https://pinecone.io/' target='_blank'>Pinecone</a> + 
            <a href='https://streamlit.io/' target='_blank'>Streamlit</a>
            <br>
            <small>Version 2.0 | Built with ❤️ for financial analysis</small>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
