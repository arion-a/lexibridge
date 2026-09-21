import os

from dotenv import load_dotenv

load_dotenv()

# Anthropic — powers clause/memo drafting and summarization
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Voyage AI — embeddings for the legal vault search
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY")
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-law-2")

# Pinecone — vector store backing the legal vault
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "legal-vault-index")
