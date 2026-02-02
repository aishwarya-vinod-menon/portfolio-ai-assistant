# Data Directory

Place your PDF documents here for the RAG system to process.

## Supported Files
- `resume.pdf` - Your resume
- `linkedin.pdf` - LinkedIn profile export or summary

## How It Works
1. Place PDF files in this directory
2. The backend will automatically process them on startup
3. Text is extracted, chunked, and indexed in the vector database
4. You can also trigger re-indexing via the `/reindex` endpoint

## File Format
- Only PDF files (`.pdf` extension) are processed
- Files are processed in alphabetical order
- Each PDF is split into chunks of ~600 characters with 100 character overlap
