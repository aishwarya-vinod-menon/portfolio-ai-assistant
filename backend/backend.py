"""
FastAPI Backend for Portfolio Chat Assistant with RAG (Retrieval-Augmented Generation)
Connects to local Ollama LLM (llama3 model) with vector database for context-aware responses.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple
import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# RAG-related imports
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Portfolio Chat Assistant API (RAG)",
    description="RAG-powered API for chatting with an AI assistant about Aishwarya Menon's portfolio",
    version="2.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration constants
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"  # Smaller, faster model (was "llama3")
OLLAMA_TIMEOUT = 120.0  # 120 seconds timeout for LLM responses

# RAG Configuration
DATA_DIR = Path(__file__).parent / "data"
CHROMA_DB_PATH = Path(__file__).parent / "chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 600  # Target chunk size in characters
CHUNK_OVERLAP = 100  # Overlap between chunks in characters
TOP_K_CHUNKS = 3  # Number of relevant chunks to retrieve (reduced for speed)

# System prompt for RAG
RAG_SYSTEM_PROMPT = """You are Aishwarya Menon's portfolio assistant. Your role is to provide accurate information about her skills, projects, work experience, and technical expertise.

IMPORTANT INSTRUCTIONS:
1. Answer questions using ONLY the provided context below
2. When asked about projects, list ALL projects mentioned in the context with their descriptions and technologies
3. When asked about skills or technologies, be comprehensive and include all relevant information from the context
4. If the context contains the answer, provide it in full detail
5. If the context does not contain enough information, politely say you don't have that specific information
6. Never make up or hallucinate information not present in the context
7. Be conversational and helpful in your responses"""

# Global variables for RAG components
embedding_model: Optional[SentenceTransformer] = None
chroma_client: Optional[chromadb.ClientAPI] = None
chroma_collection: Optional[chromadb.Collection] = None


# Request/Response models
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., min_length=1, description="The question to ask the assistant")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="The assistant's response")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


# ============================================================================
# PDF Processing Functions
# ============================================================================

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
        
    Raises:
        Exception: If PDF reading fails
    """
    try:
        logger.info(f"Extracting text from PDF: {pdf_path.name}")
        
        # Open PDF with explicit binary mode for Windows compatibility
        with open(pdf_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_parts = []
            
            logger.info(f"PDF has {len(reader.pages)} pages")
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text)
                        logger.debug(f"Extracted {len(text)} characters from page {page_num}")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    continue
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(full_text)} characters from {pdf_path.name}")
            return full_text
        
    except Exception as e:
        logger.exception(f"Failed to extract text from {pdf_path}: {str(e)}")
        raise


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Splits text into overlapping chunks of specified size.
    
    Args:
        text: The text to split
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    iterations = 0
    max_iterations = len(text) // (chunk_size - overlap) + 10  # Safety limit
    
    while start < len(text) and iterations < max_iterations:
        iterations += 1
        
        # Calculate end position
        end = min(start + chunk_size, len(text))
        
        # If not the last chunk, try to break at a sentence or word boundary
        if end < len(text):
            # Try to find a sentence boundary (period, newline, etc.)
            for boundary in ['. ', '.\n', '\n\n', '\n', ' ']:
                boundary_pos = text.rfind(boundary, start, end)
                if boundary_pos != -1 and boundary_pos > start:
                    end = boundary_pos + len(boundary)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap, ensuring we always advance
        new_start = end - overlap
        if new_start <= start:
            # Ensure we always move forward to avoid infinite loops
            new_start = start + max(1, chunk_size - overlap)
        
        start = new_start
    
    if iterations >= max_iterations:
        logger.warning(f"Hit iteration limit while chunking text (created {len(chunks)} chunks)")
    
    logger.info(f"Split text into {len(chunks)} chunks")
    return chunks


# ============================================================================
# Vector Database Functions
# ============================================================================

def initialize_embedding_model() -> SentenceTransformer:
    """
    Initializes and loads the sentence transformer model for embeddings.
    
    Returns:
        Loaded SentenceTransformer model
    """
    global embedding_model
    
    if embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        try:
            embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    return embedding_model


def initialize_chroma_db() -> Tuple[chromadb.ClientAPI, chromadb.Collection]:
    """
    Initializes ChromaDB client and collection.
    
    Returns:
        Tuple of (chroma_client, chroma_collection)
    """
    global chroma_client, chroma_collection
    
    try:
        # Create ChromaDB client with persistent storage
        chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        collection_name = "portfolio_documents"
        try:
            chroma_collection = chroma_client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            chroma_collection = chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Portfolio documents for Aishwarya Menon"}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        return chroma_client, chroma_collection
        
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {str(e)}")
        raise


def process_and_index_documents() -> int:
    """
    Processes PDFs in the data directory and indexes them in ChromaDB.
    Also includes GitHub repos and portfolio projects.
    
    Returns:
        Number of chunks indexed
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(DATA_DIR.glob("*.pdf"))
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to process")
    
    # Import additional data sources
    try:
        from data_sources import get_additional_sources_text
        additional_sources = get_additional_sources_text()
        logger.info(f"Loaded {len(additional_sources)} additional data sources")
    except Exception as e:
        logger.warning(f"Could not load additional sources: {str(e)}")
        additional_sources = {}
    
    # Initialize components
    model = initialize_embedding_model()
    _, collection = initialize_chroma_db()
    
    all_chunks = []
    all_metadata = []
    
    # Process each PDF
    for pdf_path in pdf_files:
        try:
            logger.info(f"Processing PDF: {pdf_path.name}")
            
            # Extract text
            try:
                text = extract_text_from_pdf(pdf_path)
            except Exception as e:
                logger.exception(f"[ERROR] Failed to extract text from {pdf_path.name}: {str(e)}")
                continue
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from {pdf_path.name}, skipping")
                continue
            
            logger.info(f"Extracted {len(text)} characters, now splitting into chunks...")
            
            # Split into chunks
            try:
                chunks = split_text_into_chunks(text)
            except Exception as e:
                logger.exception(f"[ERROR] Failed to split {pdf_path.name} into chunks: {str(e)}")
                continue
            
            if not chunks:
                logger.warning(f"No chunks created from {pdf_path.name}, skipping")
                continue
            
            logger.info(f"Created {len(chunks)} chunks, adding metadata...")
            
            # Create metadata for each chunk
            try:
                for idx, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        "source": pdf_path.name,
                        "chunk_index": idx,
                        "total_chunks": len(chunks)
                    })
            except Exception as e:
                logger.exception(f"[ERROR] Failed to create metadata for {pdf_path.name}: {str(e)}")
                continue
            
            logger.info(f"[OK] Processed {pdf_path.name}: {len(chunks)} chunks from {len(text)} characters")
            
        except Exception as e:
            logger.exception(f"[ERROR] Unexpected error processing {pdf_path.name}: {str(e)}")
            # Continue with next PDF instead of failing completely
            continue
    
    # Process additional sources (GitHub repos, portfolio projects)
    for source_name, source_text in additional_sources.items():
        try:
            logger.info(f"Processing additional source: {source_name}")
            
            if not source_text or not source_text.strip():
                logger.warning(f"No content in {source_name}, skipping")
                continue
            
            logger.info(f"Extracted {len(source_text)} characters from {source_name}, now splitting into chunks...")
            
            # Split into chunks
            try:
                chunks = split_text_into_chunks(source_text)
            except Exception as e:
                logger.exception(f"[ERROR] Failed to split {source_name} into chunks: {str(e)}")
                continue
            
            if not chunks:
                logger.warning(f"No chunks created from {source_name}, skipping")
                continue
            
            logger.info(f"Created {len(chunks)} chunks from {source_name}, adding metadata...")
            
            # Create metadata for each chunk
            try:
                for idx, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        "source": source_name,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "source_type": "additional"
                    })
            except Exception as e:
                logger.exception(f"[ERROR] Failed to create metadata for {source_name}: {str(e)}")
                continue
            
            logger.info(f"[OK] Processed {source_name}: {len(chunks)} chunks from {len(source_text)} characters")
            
        except Exception as e:
            logger.exception(f"[ERROR] Unexpected error processing {source_name}: {str(e)}")
            continue
    
    if not all_chunks:
        logger.warning("No chunks to index")
        return 0
    
    # Generate embeddings
    logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    
    # Check if collection already has data
    existing_count = collection.count()
    
    if existing_count > 0:
        logger.info(f"Collection already has {existing_count} documents. Clearing and re-indexing...")
        chroma_client.delete_collection(name=collection.name)
        collection = chroma_client.create_collection(
            name=collection.name,
            metadata={"description": "Portfolio documents for Aishwarya Menon"}
        )
        # Update global collection reference
        global chroma_collection
        chroma_collection = collection
    
    # Add to ChromaDB
    ids = [f"chunk_{i}" for i in range(len(all_chunks))]
    try:
        collection.add(
            embeddings=embeddings.tolist(),
            documents=all_chunks,
            metadatas=all_metadata,
            ids=ids
        )
        # Verify the data was added
        final_count = collection.count()
        logger.info(f"Successfully indexed {len(all_chunks)} chunks in ChromaDB. Collection now has {final_count} total chunks.")
        
        if final_count == 0:
            logger.error("WARNING: Chunks were added but collection count is 0. There may be an indexing issue.")
        
        return len(all_chunks)
    except Exception as e:
        logger.error(f"Error adding chunks to ChromaDB: {str(e)}")
        raise


def retrieve_relevant_chunks(query: str, top_k: int = TOP_K_CHUNKS) -> List[str]:
    """
    Retrieves the most relevant text chunks for a given query.
    Dynamically adjusts the number of chunks based on query type.
    
    Args:
        query: The search query
        top_k: Number of chunks to retrieve (can be overridden for certain queries)
        
    Returns:
        List of relevant text chunks
    """
    try:
        # Initialize components if not already done
        model = initialize_embedding_model()
        _, collection = initialize_chroma_db()
        
        # Check if collection has data
        collection_count = collection.count()
        logger.info(f"Querying collection with {collection_count} chunks for query: '{query[:50]}...'")
        
        if collection_count == 0:
            logger.warning("Collection is empty - no documents have been indexed")
            return []
        
        # Adjust top_k for comprehensive queries (reduced for faster response)
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ['all projects', 'list projects', 'what projects', 'projects has', 'projects did']):
            # For project listing queries, retrieve more chunks to ensure we get all projects
            top_k = min(8, collection_count)
            logger.info(f"Detected project listing query, increasing retrieval to {top_k} chunks")
        elif any(keyword in query_lower for keyword in ['all skills', 'technologies', 'tech stack', 'what does', 'what can']):
            # For skills/tech queries, also retrieve more chunks
            top_k = min(6, collection_count)
            logger.info(f"Detected skills/tech query, increasing retrieval to {top_k} chunks")
        
        # Generate query embedding
        query_embedding = model.encode([query])[0]
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, collection_count)  # Don't request more than available
        )
        
        # Extract documents from results
        if results.get('documents') and len(results['documents']) > 0 and len(results['documents'][0]) > 0:
            chunks = results['documents'][0]
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            return chunks
        else:
            logger.warning(f"No relevant chunks found. Results structure: {list(results.keys())}")
            return []
            
    except Exception as e:
        logger.exception(f"Error retrieving chunks: {str(e)}")
        return []


# ============================================================================
# Ollama Integration
# ============================================================================

async def call_ollama_api_with_context(context: str, question: str) -> str:
    """
    Calls the Ollama API with RAG context.
    
    Args:
        context: Retrieved context chunks
        question: The user's question
        
    Returns:
        The generated response from the LLM
        
    Raises:
        HTTPException: If the API call fails
    """
    # Construct the prompt with system message, context, and question
    prompt = f"""{RAG_SYSTEM_PROMPT}

Context:
{context}

Question: {question}

Answer:"""
    
    # Prepare the request payload for Ollama
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
        }
    }
    
    logger.info(f"Calling Ollama API with model: {OLLAMA_MODEL}, prompt length: {len(prompt)} chars")
    
    try:
        # Make async HTTP request to Ollama
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                OLLAMA_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Log response details for debugging
            logger.info(f"Ollama response status: {response.status_code}")
            
            # Check if request was successful
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Ollama API error response: {error_text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Ollama API error: {response.status_code} - {error_text[:200]}"
                )
            
            # Parse the response
            result = response.json()
            
            # Extract the response text from Ollama's response format
            if "response" in result:
                return result["response"].strip()
            else:
                logger.error(f"Unexpected Ollama response format: {result}")
                raise ValueError("Invalid response format from Ollama API")
                
    except httpx.TimeoutException:
        logger.error("Ollama API request timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI service took too long to respond. Please try again."
        )
    except httpx.ConnectError:
        logger.error("Failed to connect to Ollama API - is Ollama running?")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to Ollama service. Please ensure Ollama is running on localhost:11434"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama API returned error status: {e.response.status_code}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error calling Ollama API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request"
        )


# ============================================================================
# FastAPI Endpoints
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize RAG components on startup"""
    try:
        logger.info("Initializing RAG system...")
        
        # Initialize embedding model
        initialize_embedding_model()
        
        # Initialize ChromaDB
        initialize_chroma_db()
        
        # Process and index documents
        chunk_count = process_and_index_documents()
        
        if chunk_count > 0:
            logger.info(f"RAG system initialized successfully with {chunk_count} chunks")
        else:
            logger.warning("RAG system initialized but no documents indexed. Add PDFs to the data/ folder.")
            
    except Exception as e:
        logger.error(f"Error initializing RAG system: {str(e)}")
        logger.warning("Server will start but RAG functionality may be limited")


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    try:
        _, collection = initialize_chroma_db()
        chunk_count = collection.count()
    except:
        chunk_count = 0
    
    return {
        "message": "Portfolio Chat Assistant API (RAG) is running",
        "status": "healthy",
        "ollama_model": OLLAMA_MODEL,
        "indexed_chunks": chunk_count,
        "embedding_model": EMBEDDING_MODEL_NAME
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint"""
    # Check Ollama
    ollama_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                ollama_status = "available"
            else:
                ollama_status = "unavailable"
    except Exception as e:
        logger.warning(f"Ollama health check failed: {str(e)}")
        ollama_status = "unavailable"
    
    # Check ChromaDB
    chroma_status = "unknown"
    chunk_count = 0
    try:
        _, collection = initialize_chroma_db()
        chunk_count = collection.count()
        chroma_status = "available"
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {str(e)}")
        chroma_status = "unavailable"
    
    return {
        "status": "healthy",
        "ollama": {
            "status": ollama_status,
            "model": OLLAMA_MODEL,
            "url": OLLAMA_API_URL
        },
        "rag": {
            "status": chroma_status,
            "indexed_chunks": chunk_count,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "data_directory": str(DATA_DIR)
        }
    }


@app.post("/reindex", tags=["Admin"])
async def reindex_documents():
    """
    Manually trigger re-indexing of documents in the data folder.
    Useful after adding new PDFs.
    """
    try:
        logger.info("Manual re-indexing triggered")
        chunk_count = process_and_index_documents()
        
        # Verify indexing
        _, collection = initialize_chroma_db()
        actual_count = collection.count()
        
        return {
            "success": True,
            "message": f"Successfully indexed {chunk_count} chunks",
            "chunks_indexed": chunk_count,
            "collection_count": actual_count
        }
    except Exception as e:
        logger.exception(f"Error during re-indexing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-index documents: {str(e)}"
        )


@app.get("/debug/collection", tags=["Admin"])
async def debug_collection():
    """
    Debug endpoint to check what's in the ChromaDB collection.
    """
    try:
        _, collection = initialize_chroma_db()
        count = collection.count()
        
        # Get a sample of documents
        sample_results = collection.get(limit=min(3, count)) if count > 0 else None
        
        return {
            "collection_name": collection.name,
            "total_chunks": count,
            "sample_documents": sample_results["documents"][:3] if sample_results and sample_results.get("documents") else [],
            "sample_metadata": sample_results["metadatas"][:3] if sample_results and sample_results.get("metadatas") else []
        }
    except Exception as e:
        logger.exception(f"Error checking collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check collection: {str(e)}"
        )


@app.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Chat"],
    summary="Chat with the portfolio assistant (RAG-powered)",
    description="Send a question to the AI assistant about Aishwarya Menon's portfolio. Uses RAG to retrieve relevant context from documents."
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint with RAG. Retrieves relevant context and generates answer.
    
    Args:
        request: ChatRequest containing the user's question
        
    Returns:
        ChatResponse containing the assistant's answer
        
    Raises:
        HTTPException: If the request cannot be processed
    """
    try:
        logger.info(f"Received chat request: {request.question[:100]}...")
        
        # Validate question
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        question = request.question.strip()
        
        # Retrieve relevant chunks from vector database
        relevant_chunks = retrieve_relevant_chunks(question, top_k=TOP_K_CHUNKS)
        
        if not relevant_chunks:
            # No relevant context found - return polite message
            logger.warning("No relevant context found for question")
            return ChatResponse(
                answer="I apologize, but I don't have enough information in my knowledge base to answer that question. "
                       "Please try asking about Aishwarya's skills, experience, projects, or other portfolio-related topics."
            )
        
        # Deduplicate chunks (remove very similar ones)
        unique_chunks = []
        seen_content = set()
        for chunk in relevant_chunks:
            # Use first 100 chars as a simple deduplication key
            chunk_key = chunk[:100].strip()
            if chunk_key not in seen_content:
                unique_chunks.append(chunk)
                seen_content.add(chunk_key)
        
        # Combine chunks into context, but limit total size
        MAX_CONTEXT_LENGTH = 5000  # Limit context to 5000 chars for faster processing
        context_parts = []
        current_length = 0
        
        for chunk in unique_chunks:
            if current_length + len(chunk) > MAX_CONTEXT_LENGTH:
                break
            context_parts.append(chunk)
            current_length += len(chunk) + 2  # +2 for newlines
        
        context = "\n\n".join(context_parts)
        logger.info(f"Using {len(context_parts)} unique chunks as context (total: {len(context)} chars, deduplicated from {len(relevant_chunks)})")
        
        # Call Ollama with context
        answer = await call_ollama_api_with_context(context, question)
        
        logger.info(f"Successfully generated response (length: {len(answer)} chars)")
        
        return ChatResponse(answer=answer)
        
    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.exception(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )
