import os

from dotenv import load_dotenv

load_dotenv()

# Anthropic — powers clause/memo drafting and summarization. This is only a
# fallback default: configure_llm can set a different key/model for the
# session, so this can be left unset if you always call configure_llm.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Embedding model (ONNX, runs on-device inside this container — no API key).
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "Xenova/paraphrase-multilingual-MiniLM-L12-v2")

# Default folder embed_offline.py looks in for a local bulk-ingest run.
# Not used by the ingest_document MCP tool, which takes text directly.
LEGAL_VAULT_DIR = os.environ.get("LEGAL_VAULT_DIR", "./legal_vault")

# Pinecone — vector store backing the legal vault.
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "legal-vault-index")
