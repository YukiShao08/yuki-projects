"""
Banking Notes Query Tool
Loads FAISS index and performs vector search for banking documents
"""

import sys
import os
from pathlib import Path
import numpy as np
import faiss
import pickle
import requests
from typing import List, Dict, Optional
import json


class CustomEmbeddingsAPI:
    """
    Custom embeddings API client for space.ai-builders.com
    """
    
    def __init__(self, api_key: str, base_url: str = "https://space.ai-builders.com/backend/v1"):
        """
        Initialize custom embeddings API client
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the API

        将外部传入的参数(如api_key、base_url)保存为实例属性, 方便类的其他方法访问这些配置信息
        
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.embeddings_endpoint = f"{self.base_url}/embeddings"
        print(f"DEBUG: Embeddings endpoint configured as: {self.embeddings_endpoint}")
        
        # Configure proxy settings - support both HTTP_PROXY env var and PROXY_PORT
        # Defaults to Clash for Windows port 7890
        # proxy for forwarding requests to the internet
        http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        proxy_port = os.getenv("PROXY_PORT", "7890")  # Default to Clash port 7890
        
        # Configure proxy - Clash typically uses http://127.0.0.1:7890
        if not http_proxy:
            http_proxy = f"http://127.0.0.1:{proxy_port}"
        if not https_proxy:
            https_proxy = http_proxy
        
        # Store proxy settings for requests
        self.proxies = {
            "http": http_proxy,
            "https": https_proxy
        }
        
        print(f"Embeddings API initialized with proxy: {http_proxy}")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            numpy array of embedding (embedding_dim,)
        """
        try:
            print(f"DEBUG: Making request to embeddings endpoint: {self.embeddings_endpoint}")
            print(f"DEBUG: Using proxies: {self.proxies}")
            print(f"DEBUG: Base URL: {self.base_url}")
            response = requests.post(
                self.embeddings_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": "text-embedding-ada-002"
                },
                timeout=30,
                proxies=self.proxies  # Use configured proxy settings
            )
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response URL: {response.url}")
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                if "data" in data and len(data["data"]) > 0:
                    embedding = data["data"][0].get("embedding", [])
                elif "embedding" in data:
                    embedding = data["embedding"]
                else:
                    embedding = list(data.values())[0] if data else []
            elif isinstance(data, list):
                embedding = data[0] if len(data) > 0 else []
            else:
                embedding = []
            
            if not embedding:
                raise ValueError(f"No embedding returned for text: {text[:50]}...")
            
            return np.array(embedding, dtype=np.float32)
        
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request exception details:")
            print(f"  - URL attempted: {self.embeddings_endpoint}")
            print(f"  - Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  - Response status: {e.response.status_code}")
                print(f"  - Response URL: {e.response.url}")
            raise Exception(f"Error getting embedding: {e}")


class BankingNotesQueryTool:
    """
    Tool for querying banking documents using FAISS vector search
    """
    
    def __init__(
        self,
        index_path: str,
        api_key: str = "sk_f4e0b32d_6f6cf1db6bd8ccf6735fab4976aaa0accd32",
        embeddings_url: str = "https://space.ai-builders.com/backend/v1"
    ):
        """
        Initialize the banking notes query tool
        
        Args:
            index_path: Path to the FAISS index file (my_notes.index)
            api_key: API key for embeddings endpoint
            embeddings_url: Base URL for embeddings API
        """
        self.index_path = Path(index_path)
        # Explicitly ensure the embeddings_url is correct
        if not embeddings_url.endswith('/backend/v1'):
            if embeddings_url.endswith('/backend'):
                embeddings_url = embeddings_url + '/v1'
            elif not embeddings_url.endswith('/v1'):
                embeddings_url = embeddings_url.rstrip('/') + '/backend/v1'
        print(f"DEBUG: BankingNotesQueryTool initialized with embeddings_url: {embeddings_url}")
        self.embeddings_api = CustomEmbeddingsAPI(api_key=api_key, base_url=embeddings_url)
        self.index = None
        self.metadata = []
        self._load_index()
    
    def _load_index(self):
        """Load the FAISS index and metadata"""
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self.index_path}. "
                f"Please ensure the index has been created in Phase B project."
            )
        
        # Load FAISS index
        self.index = faiss.read_index(str(self.index_path))
        
        # Load metadata
        # Try both naming conventions: my_notes.index.metadata.pkl and my_notes.metadata.pkl
        metadata_path1 = self.index_path.with_suffix('.metadata.pkl')  # my_notes.index.metadata.pkl
        metadata_path2 = self.index_path.parent / f"{self.index_path.stem}.metadata.pkl"  # my_notes.metadata.pkl
        
        if metadata_path1.exists():
            metadata_path = metadata_path1
        elif metadata_path2.exists():
            metadata_path = metadata_path2
        else:
            print(f"Warning: Metadata file not found at {metadata_path1} or {metadata_path2}")
            self.metadata = []
            return
        
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        
        print(f"Loaded FAISS index from {self.index_path}")
        print(f"Index contains {self.index.ntotal} vectors")
    
    def query(self, query_text: str, top_k: int = 3) -> str:
        """
        Query the banking documents using vector search
        
        Args:
            query_text: The search query
            top_k: Number of top results to return (default: 3)
            
        Returns:
            JSON string containing search results with relevance indicators
        """
        if self.index is None or self.index.ntotal == 0:
            return json.dumps({
                "error": "Index not loaded or empty",
                "query": query_text,
                "results": [],
                "has_results": False,
                "message": "The banking knowledge base is not available or empty."
            }, indent=2)
        
        try:
            # Get query embedding
            query_embedding = self.embeddings_api.get_embedding(query_text)
            
            # Ensure query is right shape
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Search
            distances, indices = self.index.search(
                query_embedding.astype(np.float32),
                min(top_k, self.index.ntotal)
            )
            
            # Format results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata) and idx >= 0:
                    result = {
                        "rank": i + 1,
                        "text": self.metadata[idx].get("text", ""),
                        "score": float(distance),
                        "relevance": "high" if distance < 1.0 else "medium" if distance < 2.0 else "low",
                        "source": self.metadata[idx].get("source", "unknown")
                    }
                    results.append(result)
            
            # Determine if results are relevant (low distance = high relevance)
            has_relevant_results = len(results) > 0 and any(r["relevance"] in ["high", "medium"] for r in results)
            
            return json.dumps({
                "query": query_text,
                "results": results,
                "count": len(results),
                "has_results": len(results) > 0,
                "has_relevant_results": has_relevant_results,
                "message": "Found relevant information in local knowledge base." if has_relevant_results else "Limited or no relevant information found in local knowledge base. Consider using web search for current information."
            }, indent=2)
        
        except Exception as e:
            # Extract more details from the error
            error_details = str(e)
            if hasattr(e, '__cause__') and e.__cause__:
                error_details += f" | Cause: {str(e.__cause__)}"
            
            # Log the actual endpoint being used
            actual_endpoint = self.embeddings_api.embeddings_endpoint
            error_details += f" | Endpoint used: {actual_endpoint}"
            
            return json.dumps({
                "error": f"Query failed: {error_details}",
                "query": query_text,
                "results": [],
                "has_results": False,
                "has_relevant_results": False,
                "message": f"Error querying knowledge base: {error_details}. Consider using web search as fallback.",
                "debug_info": {
                    "endpoint_used": actual_endpoint,
                    "expected_endpoint": "https://space.ai-builders.com/backend/v1/embeddings"
                }
            }, indent=2)


# Global instance (lazy initialization)
_banking_notes_tool = None


def reset_banking_notes_tool():
    """Reset the global banking notes tool instance (useful for testing/reloading)"""
    global _banking_notes_tool
    _banking_notes_tool = None
    print("Banking notes tool instance reset")


def banking_notes_tool_available() -> bool:
    """
    Lightweight check if banking notes tool is available (without initializing)
    Only checks if the index file exists, doesn't load it.
    
    Returns:
        True if index exists and tool can be used, False otherwise
    """
    phase_b_path = Path(r"C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseB_RAG")
    index_path = phase_b_path / "my_notes.index"
    return index_path.exists()


def get_banking_notes_tool() -> Optional[BankingNotesQueryTool]:
    """
    Get or create the global banking notes tool instance
    
    Returns:
        BankingNotesQueryTool instance or None if index not found
    """
    global _banking_notes_tool
    
    # Return cached instance if already initialized
    if _banking_notes_tool is not None:
        return _banking_notes_tool
    
    # Path to Phase B project index
    phase_b_path = Path(r"C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseB_RAG")
    index_path = phase_b_path / "my_notes.index"
    
    if not index_path.exists():
        print(f"Warning: Banking notes index not found at {index_path}")
        print("The query_my_notes tool will not be available.")
        return None
    
    try:
        _banking_notes_tool = BankingNotesQueryTool(
            index_path=str(index_path),
            api_key="sk_f4e0b32d_6f6cf1db6bd8ccf6735fab4976aaa0accd32",
            embeddings_url="https://space.ai-builders.com/backend/v1"
        )
        return _banking_notes_tool
    except Exception as e:
        print(f"Error initializing banking notes tool: {e}")
        return None


def query_my_notes(query: str, top_k: int = 3) -> str:
    """
    Query banking documents - tool function for FastAPI
    
    Args:
        query: The search query string
        top_k: Number of top results to return (default: 3, max: 10)
        
    Returns:
        JSON string containing search results
    """
    # Limit top_k to reasonable number
    top_k = min(max(1, top_k), 10)
    
    tool = get_banking_notes_tool()
    if tool is None:
        return json.dumps({
            "error": "Banking notes index not available",
            "query": query,
            "message": "The banking documents index has not been created. Please run the RAG pipeline in Phase B project first to create my_notes.index. Consider using web search as fallback.",
            "results": [],
            "has_results": False,
            "has_relevant_results": False
        }, indent=2)
    
    return tool.query(query, top_k=top_k)

