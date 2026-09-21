"""Optional: bulk-ingest a local folder of legal documents into the vault.

Only useful if you have a folder of documents available to whatever
machine runs this script (e.g. a mounted volume on the deployed
container, or your own machine before it's deployed). Not required for
day-to-day use — the ingest_document MCP tool ingests text directly, with
no local files or repository checkout needed at all.

Usage:
    python embed_offline.py --vault-dir ./legal_vault
"""

import argparse
import sys
from pathlib import Path

import config
import vault


def main():
    parser = argparse.ArgumentParser(description="Bulk-ingest a local folder of legal documents into the vault.")
    parser.add_argument("--vault-dir", default=config.LEGAL_VAULT_DIR)
    args = parser.parse_args()

    vault_dir = Path(args.vault_dir)
    if not vault_dir.is_dir():
        print(f"Vault directory not found: {vault_dir}", file=sys.stderr)
        sys.exit(1)

    total = 0
    for path in sorted(vault_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in (".txt", ".md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            count = vault.ingest_document(path.name, text)
            print(f"{path.name}: {count} chunk(s)")
            total += count

    print(f"Done. {total} chunk(s) ingested into '{config.PINECONE_INDEX}'.")


if __name__ == "__main__":
    main()
