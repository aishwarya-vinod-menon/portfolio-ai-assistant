# Portfolio AI Assistant

An intelligent RAG-powered chatbot for portfolio websites that answers questions about skills, experience, projects, and GitHub repositories using local LLM (Ollama) with vector similarity search.

## 🚀 Features

- **RAG (Retrieval-Augmented Generation)** - Context-aware responses using semantic search
- **PDF Document Processing** - Extracts and indexes information from PDFs (resumes, profiles)
- **GitHub Integration** - Automatically fetches and indexes public repository information
- **Portfolio Project Integration** - Reads project data from portfolio website
- **Vector Database** - ChromaDB for efficient similarity search
- **Local LLM** - Uses Ollama with llama3.2:3b for fast, private inference
- **Real-time Chat Interface** - Beautiful React component with streaming support
- **Optimized Performance** - Sub-15 second response times

## 📁 Repository Structure

```
portfolio-ai-assistant/
├── backend/
│   ├── backend.py              # FastAPI server with RAG pipeline
│   ├── data_sources.py         # GitHub API and portfolio data fetching
│   ├── requirements.txt        # Python dependencies
│   ├── data/                   # PDF documents (resume, profile)
│   │   └── README.md          # Instructions for adding PDFs
│   └── .gitignore             # Excludes chroma_db, __pycache__, etc.
├── frontend/
│   └── components/
│       └── ChatBot.jsx        # React chatbot component
├── README.md                  # This file
└── .gitignore                 # Repository-level gitignore
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Ollama** - Local LLM inference (llama3.2:3b)
- **ChromaDB** - Vector database for embeddings
- **Sentence Transformers** - all-MiniLM-L6-v2 for embeddings
- **PyPDF** - PDF text extraction
- **PyGithub** - GitHub API integration

### Frontend
- **React** - UI framework
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **shadcn/ui** - UI components

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Node.js 16+** and npm/yarn installed
3. **Ollama** installed and running
   ```bash
   # Install Ollama from https://ollama.ai
   # Pull the model
   ollama pull llama3.2:3b
   ```

## 🔧 Installation

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your PDF documents:**
   - Place your resume PDF in `backend/data/`
   - Place your profile PDF in `backend/data/`
   - See `backend/data/README.md` for details

5. **Configure GitHub username:**
   - Edit `backend/data_sources.py`
   - Update `GITHUB_USERNAME = "your-github-username"`

6. **Start the backend server:**
   ```bash
   uvicorn backend:app --host 0.0.0.0 --port 8000
   ```

   The server will automatically:
   - Process PDFs in the `data/` folder
   - Fetch your GitHub repositories
   - Load portfolio projects
   - Generate embeddings and index in ChromaDB

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Configure API URL:**
   - Create or update `src/config.js`:
   ```javascript
   const config = {
     backendApiUrl: process.env.REACT_APP_BACKEND_API_URL || "http://localhost:8000",
   };
   export default config;
   ```

4. **Import and use ChatBot component:**
   ```javascript
   import ChatBot from './components/ChatBot';
   
   function App() {
     return (
       <div>
         {/* Your other components */}
         <ChatBot />
       </div>
     );
   }
   ```

5. **Start the frontend:**
   ```bash
   npm start
   # or
   yarn start
   ```

## 🎯 Usage

1. **Start Ollama** (if not running):
   ```bash
   ollama serve
   ```

2. **Start Backend:**
   ```bash
   cd backend
   uvicorn backend:app --host 0.0.0.0 --port 8000
   ```

3. **Start Frontend:**
   ```bash
   cd frontend
   npm start
   ```

4. **Open your browser** and navigate to your portfolio website. The chatbot will appear as a floating button in the bottom-right corner.

## 📝 API Endpoints

### `POST /chat`
Send a question to the AI assistant.

**Request:**
```json
{
  "question": "What projects has Aishwarya worked on?"
}
```

**Response:**
```json
{
  "answer": "Based on the provided context, Aishwarya has worked on..."
}
```

### `GET /health`
Check system health and status.

### `POST /reindex`
Manually trigger re-indexing of documents.

## ⚙️ Configuration

### Backend Configuration (`backend.py`)

```python
# Ollama settings
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"  # Change to your preferred model
OLLAMA_TIMEOUT = 120.0

# RAG settings
CHUNK_SIZE = 600              # Text chunk size
CHUNK_OVERLAP = 100           # Overlap between chunks
TOP_K_CHUNKS = 3              # Number of chunks to retrieve
MAX_CONTEXT_LENGTH = 5000     # Maximum context length
```

### Frontend Configuration

Update `src/config.js` to point to your backend API URL.

## 🔒 Security Notes

- **CORS**: Currently set to allow all origins (`allow_origins=["*"]`). In production, restrict this to your domain.
- **PDFs**: Do not commit sensitive PDFs (resumes with personal info) to public repositories. Use `.gitignore`.
- **API Keys**: GitHub token is optional but recommended for higher rate limits.

## 🐛 Troubleshooting

### Backend Issues

**"Ollama connection failed"**
- Ensure Ollama is running: `ollama serve`
- Check if model is installed: `ollama list`
- Verify Ollama URL in `backend.py`

**"No chunks indexed"**
- Check if PDFs exist in `backend/data/` folder
- Verify PDFs are readable (not corrupted)
- Check backend logs for errors

**"Slow responses"**
- Use a smaller model: `ollama pull llama3.2:3b`
- Reduce `MAX_CONTEXT_LENGTH` in `backend.py`
- Reduce `TOP_K_CHUNKS` for faster retrieval

### Frontend Issues

**"Cannot connect to backend"**
- Verify backend is running on port 8000
- Check `src/config.js` has correct API URL
- Check browser console for CORS errors

## 📚 How It Works

1. **Document Processing**: PDFs are extracted, split into chunks, and embedded using sentence transformers
2. **Indexing**: Embeddings are stored in ChromaDB vector database
3. **Query Processing**: User questions are embedded and matched against stored chunks
4. **Context Retrieval**: Top-K most relevant chunks are retrieved
5. **LLM Generation**: Retrieved context + question is sent to Ollama for answer generation
6. **Response**: Generated answer is returned to the frontend

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Aishwarya Menon**
- GitHub: [@aishwarya-vinod-menon](https://github.com/aishwarya-vinod-menon)
- LinkedIn: [aishwarya-v-menon](https://www.linkedin.com/in/aishwarya-v-menon/)

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector database
- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

⭐ If you find this project helpful, please give it a star!
