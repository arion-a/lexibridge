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
   - `ANTHROPIC_API_KEY` (optional server-wide fallback — leave unset if
     every caller will always pass their own `api_key`)
   - `ANTHROPIC_MODEL` (optional, defaults to `claude-sonnet-5`)
3. **Settings → Networking → Generate Domain** to get a public URL.
4. Your MCP endpoint is `https://<your-app>.up.railway.app/mcp`.

You'll also need a Pinecone index: at **app.pinecone.io**, create one with
**384 dimensions** and **cosine** metric (must match the embedding model).

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
