# Portfolio Chat Assistant Backend

FastAPI backend that connects to a local Ollama LLM (llama3 model) to provide an AI assistant for Aishwarya Menon's portfolio.

## Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running locally
3. **llama3 model** pulled in Ollama

### Setting up Ollama

1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Start Ollama service (usually runs automatically)
3. Pull the llama3 model:
   ```bash
   ollama pull llama3
   ```
4. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Installation

1. Navigate to the backend directory:
   ```bash
   cd Portfolio/backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Option 1: Using uvicorn directly (Recommended)

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

- `--host 0.0.0.0`: Makes the server accessible from all network interfaces
- `--port 8000`: Runs on port 8000 (default)
- `--reload`: Enables auto-reload on code changes (development mode)

### Option 2: Running as a Python module

```bash
python backend.py
```

This will start the server with default settings (host: 0.0.0.0, port: 8000, reload enabled).

### Option 3: Production mode (no reload)

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check
- **GET** `/` - Basic health check
- **GET** `/health` - Detailed health check (includes Ollama status)

### Chat
- **POST** `/chat` - Send a question to the AI assistant

#### Request Body:
```json
{
  "question": "What are Aishwarya's technical skills?"
}
```

#### Response:
```json
{
  "answer": "Aishwarya has expertise in..."
}
```

## Testing the API

### Using curl:

```bash
# Health check
curl http://localhost:8000/

# Chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about Aishwarya\'s projects"}'
```

### Using Python requests:

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"question": "What technologies does Aishwarya use?"}
)
print(response.json())
```

### Using the interactive API docs:

Visit `http://localhost:8000/docs` in your browser for Swagger UI documentation.

## Error Handling

The API handles various error scenarios:

- **503 Service Unavailable**: Ollama is not running or not accessible
- **504 Gateway Timeout**: Ollama took too long to respond
- **502 Bad Gateway**: Ollama returned an error
- **500 Internal Server Error**: Unexpected server error
- **400 Bad Request**: Invalid request format

## Configuration

You can modify these constants in `backend.py`:

- `OLLAMA_API_URL`: Ollama API endpoint (default: `http://localhost:11434/api/generate`)
- `OLLAMA_MODEL`: Model name (default: `llama3`)
- `OLLAMA_TIMEOUT`: Request timeout in seconds (default: 60.0)
- `SYSTEM_PROMPT`: System prompt for the AI assistant

## Troubleshooting

### Ollama not running
- Ensure Ollama is installed and running
- Check if Ollama is accessible: `curl http://localhost:11434/api/tags`
- Restart Ollama service if needed

### Model not found
- Pull the llama3 model: `ollama pull llama3`
- Verify model exists: `ollama list`

### Port already in use
- Change the port: `uvicorn backend:app --port 8001`
- Or stop the process using port 8000

### CORS issues
- The current configuration allows all origins (`allow_origins=["*"]`)
- For production, update the CORS settings in `backend.py` to restrict origins

## Production Deployment

For production deployment:

1. Remove `--reload` flag
2. Use multiple workers: `--workers 4`
3. Use a reverse proxy (nginx, Apache)
4. Set up proper CORS origins
5. Use environment variables for configuration
6. Set up logging and monitoring
7. Use HTTPS

Example production command:
```bash
uvicorn backend:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```
