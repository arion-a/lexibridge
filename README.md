# lexibridge

An MCP (Model Context Protocol) server that speeds up legal research and
drafting by giving LLM clients (Claude Desktop, Claude Code, etc.) tools to
search a legal vault and draft clauses, memos, and summaries.

Runs as a single container, deployed to the cloud (Railway) — embedding,
vault storage/search, and drafting all happen inside that one process.
There is no local machine or repo checkout required to use it day to day:
connect an MCP client to the deployed URL and call its tools directly.

**Note on `SPECIFICATION.md`:** that document describes a different design
— local on-device embedding with only vectors crossing to a cloud vector
store, so raw text never leaves your machine. This deployment deliberately
collapses that into one cloud container instead (by explicit choice, for
simplicity of a fully-hosted setup with nothing to install locally). The
tradeoff: document text now lives in Pinecone, not only on a local
machine. If you want the original zero-text-exposure design back, say so
and it can be split apart again.

## Tools

- `search_legal_vault(query, max_results=4)` — semantic search over the
  vault for passages relevant to `query`. Returns JSON:
  `{source_document, page, text_content, relevance_score}`.
- `ingest_document(source_document, text)` — chunks and embeds `text` and
  stores it in the vault. This is how you populate the vault: no local
  files needed, just call this tool with a document's contents.
- `draft_clause(instruction, clause_type, tone, reference_text, api_key, model)`
  — drafts a single contract clause with an LLM, optionally grounded in
  retrieved precedent.
- `draft_legal_memo(topic, key_facts, jurisdiction, legal_questions, research_context, api_key, model)`
  — drafts a structured legal research memo (Question Presented, Brief
  Answer, Facts, Discussion, Conclusion).
- `summarize_document(document_text, focus, api_key, model)` — summarizes a
  legal document, flagging obligations, deadlines, and risks.

A typical flow: `ingest_document` to populate the vault, `search_legal_vault`
to pull relevant precedent, then feed the results into `draft_clause` or
`draft_legal_memo` as `reference_text` / `research_context` so the drafted
language is grounded in prior work.

### Bring your own key

This server runs as **one shared container**, so `api_key` is a
per-call argument on the three drafting tools rather than something set
once for a session — that keeps different people's Anthropic accounts
from leaking into each other's requests when multiple clients use the
same deployment. Each call:
```json
{ "instruction": "...", "api_key": "sk-ant-...", "model": "claude-opus-5" }
```
`model` is optional. If a call omits `api_key`, it falls back to the
server's `ANTHROPIC_API_KEY` (if the deployment has one set) — if neither
is present, the tool returns a clear error rather than failing silently.

## Deploy (Railway)

1. **railway.app** → **New Project → Deploy from GitHub repo** → pick this
   repo and the branch you're working on. Railway detects the `Dockerfile`
   and builds it automatically.
2. In the service's **Variables** tab, add:
   - `PINECONE_API_KEY`
   - `PINECONE_INDEX` (defaults to `legal-vault-index` if unset)
   - `VOYAGE_API_KEY` (get one at **dash.voyageai.com** — used to embed
     text; see the memory note below for why this replaced local embedding)
   - `ANTHROPIC_API_KEY` (optional server-wide fallback — leave unset if
     every caller will always pass their own `api_key`)
   - `ANTHROPIC_MODEL` (optional, defaults to `claude-sonnet-5`)
3. **Settings → Networking → Generate Domain** to get a public URL.
4. Your MCP endpoint is `https://<your-app>.up.railway.app/mcp`.

No manual Pinecone dashboard step needed — `vault.py` creates the index
itself (cosine metric, 1024 dimensions to match `voyage-law-2`'s fixed
output) the first time `ingest_document` or `search_legal_vault` runs, if
`PINECONE_INDEX` doesn't already exist. If you point `VOYAGE_MODEL` at a
different model with a different output size, or if an index with that
name already exists at the wrong dimension, the tool call fails with an
error naming the exact mismatch and a one-line fix (delete the index —
Pinecone won't let its dimension change in place — and the next call
recreates it correctly).

### Why embeddings moved to a hosted API

The first deployment loaded an ONNX embedding model in-process
(`optimum`/`transformers`), which pulled in enough of an ML stack to
OOM-kill the Railway container the moment a tool actually tried to embed
text — `ingest_document`/`search_legal_vault` would return an empty
response and silently restart the whole server. Since this deployment
already sends document text to Pinecone rather than keeping it strictly
local, there was no remaining benefit to paying that memory cost, so
embedding now goes through Voyage AI's API (`voyage-law-2`, a legal-domain
model) instead of running in-process.

## Connect an MCP client

For Claude Desktop (or any client supporting remote MCP servers), add:
```json
{
  "mcpServers": {
    "lexibridge": {
      "url": "https://<your-app>.up.railway.app/mcp"
    }
  }
}
```

Then call `ingest_document` a few times to populate the vault, and the
other tools are ready to use.

## Local Docker testing (optional)

```bash
cp .env.example .env   # fill in PINECONE_API_KEY at minimum
docker build -t lexibridge .
docker run --env-file .env -p 8000:8000 lexibridge
```

## Optional: bulk-ingest a local folder

If you do have a folder of documents on whatever machine you're running
this from, `embed_offline.py` walks it and calls the same ingestion path
as `ingest_document`:
```bash
python embed_offline.py --vault-dir ./legal_vault
```
Not required — most setups can just call the `ingest_document` MCP tool
directly instead.

**Disclaimer:** output is a drafting aid, not legal advice — a licensed
attorney should review anything generated here before it's relied on or
filed.
