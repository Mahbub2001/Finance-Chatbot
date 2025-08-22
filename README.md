# 💰 Finance Policy AI Assistant

> An intelligent chatbot that helps you understand financial policy documents through advanced AI-powered conversations

Ever struggled to find specific information in lengthy financial policy documents? This AI assistant makes it easy! Ask questions in natural language and get accurate, sourced answers from your financial documents instantly.

## ✨ What makes this special?

- **Smart Conversations**: Ask follow-up questions and the AI remembers context
- **Always Cited**: Every answer includes page numbers and source references
- **Table-Aware**: Understands complex financial tables and data. Better approach for utilizes the tables data.
- **Multiple Interfaces**: Choose between web chat or interactive Streamlit app
- **Lightning Fast**: Powered by Groq's ultra-fast LLM inference
- **Multimodal Support**: Support image input also

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone and navigate to the project
git clone <your-repo-url>
cd finance-policy-chatbot

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your API Keys
Create a `.env` file in the root directory:
```env
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=finance-policy
GROQ_API_KEY=your_groq_api_key_here
```

> **💡 Tip**: Get your free API keys from [Pinecone](https://pinecone.io) and [Groq](https://groq.com)

### 3. Prepare Your Documents
Drop your PDF files into the `data/` folder:
```
data/
├── financial_policy_2024.pdf
```

### 4. Process Your Documents
# At first create a pinecone index like -> finance-policy
# Then embed and store in pinecone-
```bash
# Enhanced processing with AI formatting
python ingest.py
```

### 5. Start the Application
# Ati first run the FastApi Backend
```bash
# FastAPI Backend + Web Interface
uvicorn app:app --reload --port 8000
# Open http://localhost:8000
```
# Then Streamlit Interface 
streamlit run streamlit_app.py
# Open http://localhost:8501

## 🎯 How to Use

### Ask Natural Questions
Instead of searching through pages manually, just ask:

- *"What are the short term financial objectives?"*
- *"How much was allocated for infrastructure in 2024?"*
- *"Show me the debt management strategy"*
- *"What changed between 2023 and 2024 budgets?"*

### Get Detailed Page Content
Need the complete content from a specific page?
```bash
curl -X POST http://localhost:8000/page \
  -H "Content-Type: application/json" \
  -d '{"book_id": "budget_2024.pdf", "page_number": 15}'
```

### Conversation Memory
The AI remembers your conversation context:
```
You: "What are the main financial objectives?"
AI: "The main objectives include maintaining AAA credit rating..."

You: "How do they plan to achieve the first one?"
AI: "To maintain the AAA credit rating, the strategy includes..." 
```

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Streamlit with custom CSS, FastAPI with HTML
- **AI Model**: Groq (Llama 3.3 70B) for ultra-fast responses
- **Vector Database**: Pinecone for semantic search
- **Document Processing**: PDFPlumber + AI enhancement
- **Embeddings**: Sentence Transformers (384-dim)

## 📁 Project Structure

```
finance-policy-chatbot/
├── 📄 README.md                    # You are here
├── ⚙️ requirements.txt             # Dependencies
├── 🔧 .env                         # API keys (create this)
├── 
├── 🤖 chatbot/                     # Core AI components
│   ├── config.py                   # Configuration management
│   ├── llm.py                      # Groq AI integration
│   ├── retrieval.py                # Smart document retrieval
│   ├── vectorstore.py              # Pinecone operations
│   └── memory.py                   # Conversation memory
├── 
├── 🌐 Interface Files
│   ├── streamlit_app.py            # Modern Streamlit interface
│   ├── app.py                      # FastAPI backend
│   └── static/index.html           # Simple Web interface
├── 
├── 📊 Processing & Data
│   ├── ingest.py                   # Document ingestion
│   ├── test.py                     # Document extraction testing
│   └── data/                       # Your PDF documents go here
├── 
└── 🔍 Utilities
    ├── debug_table.py              # Debug table extraction
    └── sessions/                   # Conversation storage
```

## 🎨 Interface Options

### 1. Streamlit App (Recommended)
- **Modern UI** with gradient styling and responsive design
- **Real-time chat** with conversation history
- **Analytics dashboard** showing usage statistics
- **Page extraction tool** for detailed document review
- **Quick question suggestions** to get started

### 2. FastAPI + Web Interface
- **RESTful API** for integration with other systems
- **Interactive documentation** at `/docs`
- **Simple web chat** interface
- **Perfect for developers** and API integrations

### 3. API Integration
```python
import requests

# Chat with the AI
response = requests.post("http://localhost:8000/chat", json={
    "question": "What's the budget for 2024?",
    "session_id": "user123"
})

print(response.json()["answer"])
```

## 🔧 Advanced Features

### Enhanced Document Processing
For better table extraction and content formatting:
```bash
# Processes PDFs with AI-powered table formatting
python ingest.py
```

This enhanced processor:
- Uses AI to format tables into readable text
- Improves content structure for better embeddings
- Handles complex financial data more accurately

### Dual Retrieval System
The system supports two types of retrieval:

1. **Semantic Search**: Find relevant content across all documents
2. **Page Extraction**: Get complete content from specific pages

### Configuration Options
Customize in `chatbot/config.py`:
- Embedding model selection
- Chunk size and overlap
- Response formatting
- API endpoints

## 📊 Example Conversations

**Budget Analysis:**
```
User: What were the main budget priorities for 2024?
AI: According to the 2024 Budget Document (p. 12), the main priorities include:
1. Infrastructure development - $2.5B allocation
2. Healthcare improvements - $1.8B 
3. Education expansion - $1.2B
[Sources: budget_2024.pdf, pages 12-15]
```

**Financial Strategy Questions:**
```
User: How does the government plan to maintain its credit rating?
AI: The AAA credit rating maintenance strategy involves several key measures (p. 8):
- Maintaining debt-to-GDP ratio below 15%
- Ensuring operating surpluses over the economic cycle
- Regular financial performance monitoring
[Source: financial_strategy.pdf, page 8]
```

**Follow-up Context:**
```
User: What specific metrics do they track for this?
AI: Building on the credit rating strategy mentioned earlier, they track:
- Quarterly debt ratios
- Operating balance trends
- Revenue forecasting accuracy
[Source: financial_strategy.pdf, page 9]
```

## 🛠️ Setup Details

### Creating Pinecone Index
First time setup requires creating a Pinecone index:
```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your_api_key")
pc.create_index(
    name="finance-policy",
    dimension=384,  # matches sentence-transformers model
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

### Environment Variables
Required in your `.env` file:
```env
PINECONE_API_KEY=pk-xxxxx
PINECONE_INDEX=finance-policy
GROQ_API_KEY=gsk_xxxxx
```

### Document Preparation
- Place PDF files in the `data/` directory
- Supported formats: PDF (with text and tables)
- Recommended: Financial reports, policy documents, budget files

## 💡 Tips & Best Practices

### Getting Better Answers
- **Be specific**: "What's the 2024 infrastructure budget?" vs "Tell me about money"
- **Ask follow-ups**: The AI remembers context within sessions
- **Reference tables**: "Show me Table 2.1" or "What's in the budget breakdown table?"

### Using Page Extraction
- Perfect for getting complete sections or appendices
- Use when you need full context from specific pages
- Helpful for reviewing detailed tables or charts

### Conversation Management
- Use consistent session IDs for context continuity
- Start new sessions for different topics
- Check the Streamlit analytics to track usage patterns

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-improvement`
3. **Make your changes** and test thoroughly
4. **Add tests** if applicable
5. **Commit your changes**: `git commit -m "Add amazing improvement"`
6. **Push to the branch**: `git push origin feature/amazing-improvement`
7. **Create a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start development server
uvicorn app:app --reload
```

## 🆘 Troubleshooting

### Common Issues

**API Connection Problems**
- Verify your `.env` file has correct API keys
- Check if Groq and Pinecone services are accessible
- Ensure you have internet connectivity

**No Search Results**
- Make sure documents are processed: `python ingest.py`
- Check if your Pinecone index exists and contains data
- Try broader search terms in your questions

**Slow Performance**
- Groq should provide fast responses - check your API quota
- Consider your document size and chunk settings
- Monitor Pinecone query performance

**Table Extraction Issues**
- Use the enhanced ingestion: `python ingest.py`
- This uses AI to format tables properly
- Check `debug_table.py` for extraction analysis

### Getting Help
- Check the FastAPI docs at `http://localhost:8000/docs`
- Review conversation logs in the `sessions/` directory
- Enable debug mode in `config.py` for detailed logging

## 🔮 Future Enhancements

Some ideas we're considering:
- Advanced chart and graph understanding
- Integration with more document formats
- Enhanced conversation analytics
- Custom AI model fine-tuning options


## 🙏 Acknowledgments

- **Groq** for providing lightning-fast AI inference
- **Pinecone** for excellent vector search capabilities
- **Streamlit** for making beautiful web apps simple
- **The open-source community** for amazing tools and libraries

---

<div align="center">

**Made with ❤️ for better financial document analysis**

[⭐ Star this repo](../../stargazers) • [🐛 Report Bug](../../issues) • [💡 Request Feature](../../issues)

*Transform how you interact with financial documents today!*

</div>
