"""Test script to verify embeddings endpoint URL"""
from banking_notes_tool import CustomEmbeddingsAPI

# Test endpoint construction
api = CustomEmbeddingsAPI(
    api_key="test",
    base_url="https://space.ai-builders.com/backend/v1"
)

print(f"Base URL: {api.base_url}")
print(f"Embeddings Endpoint: {api.embeddings_endpoint}")
print(f"Expected: https://space.ai-builders.com/backend/v1/embeddings")
print(f"Match: {api.embeddings_endpoint == 'https://space.ai-builders.com/backend/v1/embeddings'}")

