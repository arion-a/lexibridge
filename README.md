# lexibridge

An MCP (Model Context Protocol) server that speeds up legal research and
drafting by giving LLM clients (Claude Desktop, Claude Code, etc.) tools to
search a firm's precedent vault and draft clauses, memos, and summaries.

Research is a hybrid local/cloud pipeline designed so raw legal text never
leaves the local machine (see [SPECIFICATION.md](SPECIFICATION.md)); drafting
runs on Claude directly. Bilingual: chunking and embedding both handle
English and Hindi text.

## Architecture

```
 local machine                                    cloud (e.g. Railway)
 ┌───────────────────────────┐                     ┌───────────────────────┐
 │ legal_vault/ (synced       │                     │                       │
 │ Google Drive folder)       │                     │                       │
 │        │ embed_offline.py  │                     │                       │
 │        ▼ (ONNX MiniLM,     │   vectors only,     │  server_cloud.py      │
 │ my_manual_vector.json ─────┼── no text ─────────▶│  (query_vault_with_   │
 │ (id, text, vector — local  │                     │   precomputed_vector) │
 │  only, gitignored)         │                     │        │              │
 │                            │                     │        ▼              │
 │ server.py (search_legal_   │   query vector ────▶│  Pinecone Serverless  │
 │  vault, draft_clause,      │◀── ids + scores ─────  (legal-vault-index)  │
 │  draft_legal_memo,         │                     │                       │
 │  summarize_document)       │                     │                       │
 └───────────────────────────┘                     └───────────────────────┘
```

- **`embed_offline.py`** chunks documents from a local legal vault directory
  (a Google Drive Desktop / rclone sync works) and computes 384-dim
  embeddings entirely on-device with an ONNX multilingual MiniLM model — no
  API key, no network call to embed. Results go to `my_manual_vector.json`
  (local only). `--push` additionally upserts *vectors plus a filename/page
  locator, never the text itself* to Pinecone.
- **`server_cloud.py`** is the only thing deployed to the cloud. It exposes
  one tool, `query_vault_with_precomputed_vector`, which takes a vector and
  returns matching ids/scores from Pinecone — it never embeds anything and
  never stores or returns document text.
- **`vault.py`** (used by the local `search_legal_vault` tool) embeds the
  query locally, sends only the vector to `server_cloud.py`, and re-hydrates
  the matched clause text from the local `my_manual_vector.json` by id.

## Tools

- `search_legal_vault(query, max_results=4)` — semantic search over the
  legal vault, as described above.
- `draft_clause(instruction, clause_type, tone, reference_text)` — drafts a
  single contract clause with an LLM, optionally grounded in retrieved
  precedent.
- `draft_legal_memo(topic, key_facts, jurisdiction, legal_questions, research_context)`
  — drafts a structured legal research memo (Question Presented, Brief
  Answer, Facts, Discussion, Conclusion).
- `summarize_document(document_text, focus)` — summarizes a legal document,
  flagging obligations, deadlines, and risks.

A typical flow: an MCP client calls `search_legal_vault` to pull relevant
precedent, then feeds the results into `draft_clause` or `draft_legal_memo`
as `reference_text` / `research_context` so the drafted language is grounded
in the firm's own prior work.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY` and
   `PINECONE_API_KEY` (plus your Pinecone index name, if it differs from the
   default). `EMBEDDING_MODEL` has a working default and needs no key.
3. Deploy `server_cloud.py` (e.g. to Railway — a `Procfile` is included) and
   set `CLOUD_SERVER_URL` to its `/mcp` endpoint.
4. Point `LEGAL_VAULT_DIR` at a local copy of the legal vault, then ingest it:
   ```bash
   python embed_offline.py --push
   ```
5. Run the local server: `python server.py`
6. Point an MCP client at it, e.g. add to `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "lexibridge": {
         "command": "python",
         "args": ["/absolute/path/to/lexibridge/server.py"]
       }
     }
   }
   ```

**Disclaimer:** output is a drafting aid, not legal advice — a licensed
attorney should review anything generated here before it's relied on or
filed.
