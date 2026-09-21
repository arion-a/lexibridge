# lexibridge

An MCP (Model Context Protocol) server that speeds up legal research and
drafting by giving LLM clients (Claude Desktop, Claude Code, etc.) tools to
search a firm's precedent vault and draft clauses, memos, and summaries.

## Tools

- `search_legal_vault(query, max_results=4)` — semantic search over a
  Pinecone-backed vault of contract clauses and precedent language, embedded
  with Voyage AI's `voyage-law-2` model.
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
2. Copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY`,
   `VOYAGE_API_KEY`, and `PINECONE_API_KEY` (plus your Pinecone index name,
   if it differs from the default).
3. Run the server: `python server.py`
4. Point an MCP client at it, e.g. add to `claude_desktop_config.json`:
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
