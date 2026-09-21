# server_cloud.py
from fastmcp import FastMCP
from pinecone import Pinecone
import json

# 1. Initialize the Cloud MCP Server
mcp = FastMCP("LexiBridge-Cloud-Vault")

# 2. Connect directly to your cloud hosted database via secure API keys
pc = Pinecone(api_key="your-pinecone-api-key")
index = pc.Index("legal-vault-index")

@mcp.tool()
def search_cloud_vault(query: str, max_results: int = 4) -> str:
    """
    Queries the remote enterprise secure cloud vector database 
    for conceptually matching contract clauses and legal references.
    """
    try:
        # The database handles the math search on their remote servers
        raw_response = index.query(
            vector=[0.1] * 384,  # Your embedding vector generated via cloud API
            top_k=max_results,
            include_metadata=True
        )
        
        extracted_data = []
        for match in raw_response.get("matches", []):
            metadata = match.get("metadata", {})
            extracted_data.append({
                "source_document": metadata.get("filename", "Unknown File"),
                "page": metadata.get("page_number", 1),
                "text_content": metadata.get("text", "")
            })
            
        return json.dumps(extracted_data, indent=2)
        
    except Exception as e:
        return f"Cloud lookup database error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
