"""
Utility functions for RLM framework.

This module provides helper functions for text processing, chunking,
and context formatting.
"""

from typing import List, Union, Any
import os
import fitz  # PyMuPDF


def chunk_text(text: str, chunk_size: int, overlap: int = 0) -> List[str]:
    """
    Split text into chunks with optional overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        
        if end == text_length:
            break
        
        start += chunk_size - overlap
    
    return chunks


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.
    
    Uses a simple heuristic: ~4 characters per token on average.
    For more accurate estimation, use tiktoken or similar libraries.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    return len(text) // 4


def format_context_info(context: Any) -> dict:
    """
    Format context information for display in prompts.
    
    Args:
        context: The context to format (can be string, list, dict, etc.)
        
    Returns:
        Dictionary with context_type, context_total_length, and context_lengths
    """
    if isinstance(context, str):
        return {
            "context_type": "string",
            "context_total_length": len(context),
            "context_lengths": str([len(context)])
        }
    elif isinstance(context, list):
        lengths = [len(str(item)) for item in context]
        total_length = sum(lengths)
        return {
            "context_type": "list",
            "context_total_length": total_length,
            "context_lengths": str(lengths)
        }
    elif isinstance(context, dict):
        # For dict, compute total length of all values
        total_length = sum(len(str(v)) for v in context.values())
        lengths = [len(str(v)) for v in context.values()]
        return {
            "context_type": "dict",
            "context_total_length": total_length,
            "context_lengths": str(lengths)
        }
    else:
        # For other types, convert to string
        context_str = str(context)
        return {
            "context_type": type(context).__name__,
            "context_total_length": len(context_str),
            "context_lengths": str([len(context_str)])
        }


def load_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content as string
        
    Raises:
        ValueError: If PDF cannot be read or is password-protected
        FileNotFoundError: If the file does not exist
    """
    # Check if file exists before attempting to open
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    try:
        # Open the PDF file
        doc = fitz.open(file_path)
        
        # Check if PDF is encrypted/password-protected
        if doc.is_encrypted:
            doc.close()
            raise ValueError("PDF is password-protected and cannot be read")
        
        # Extract text from all pages
        text_content = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():  # Only add non-empty pages
                text_content.append(text)
        
        # Close the document
        doc.close()
        
        # Combine all pages with double newline separator
        combined_text = "\n\n".join(text_content)
        
        if not combined_text.strip():
            raise ValueError("PDF contains no extractable text")
        
        return combined_text
        
    except ValueError:
        # Re-raise our custom ValueError messages
        raise
    except Exception as e:
        # Catch any other PDF reading errors
        raise ValueError(f"Failed to read PDF: {str(e)}")


def load_document(file_path: str) -> str:
    """
    Load a document from a file.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Document content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def truncate_output(text: str, max_length: int) -> str:
    """
    Truncate text to maximum length with indicator.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with indicator if truncated
    """
    if len(text) <= max_length:
        return text
    
    truncated_msg = f"\n\n[Output truncated. Showing first {max_length} characters of {len(text)} total]"
    return text[:max_length] + truncated_msg
