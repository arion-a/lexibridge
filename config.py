import os

from dotenv import load_dotenv

load_dotenv()

# Anthropic — powers clause/memo drafting and summarization
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Local embedding model (ONNX, runs on-device — no API key, no network
# calls at embed time, and raw text never has to leave the machine).
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "Xenova/paraphrase-multilingual-MiniLM-L12-v2")

# Offline ingestion: where the local legal vault lives, and where its
# embeddings + original text are cached locally (never committed/pushed).
LEGAL_VAULT_DIR = os.environ.get("LEGAL_VAULT_DIR", "./legal_vault")
LOCAL_VECTOR_STORE = os.environ.get("LOCAL_VECTOR_STORE", "./my_manual_vector.json")

# Cloud bridge (server_cloud.py, deployed e.g. on Railway) that the local
# client sends precomputed query vectors to — never raw text.
CLOUD_SERVER_URL = os.environ.get("CLOUD_SERVER_URL")

# Pinecone — vector store backing the legal vault. Used by embed_offline.py
# (to push vectors) and by server_cloud.py (to query them).
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "legal-vault-index")
