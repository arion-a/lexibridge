"""LexiBridge: an MCP server for faster legal research and drafting with LLMs.

Runs as a single cloud-deployed container — embedding, vault storage/
search, and drafting all happen inside this one process. See README.md for
how this differs from SPECIFICATION.md's original local-embedding split.
"""

import json
import os

from fastmcp import FastMCP

import llm
import vault

mcp = FastMCP("LexiBridge")


@mcp.tool()
def search_legal_vault(query: str, max_results: int = 4) -> str:
    """
    Semantically search the legal vault (contract clauses, precedent
    language, and prior work product ingested via ingest_document) for
    passages relevant to `query`.

    Returns a JSON list of {source_document, page, text_content, relevance_score}.
    Use this before drafting to ground new language in existing precedent.
    """
    try:
        results = vault.search_clauses(query, max_results=max_results)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Vault search error: {e}"


@mcp.tool()
def ingest_document(source_document: str, text: str) -> str:
    """
    Chunk and embed `text` (e.g. the full contents of a contract or
    precedent document, named by `source_document`) and store it in the
    vault for future search_legal_vault calls.

    Runs entirely inside this deployed container — no local files or
    repository checkout needed to populate the vault.
    """
    try:
        count = vault.ingest_document(source_document, text)
        return f"Ingested {count} chunk(s) from '{source_document}' into the vault."
    except Exception as e:
        return f"Ingestion error: {e}"


@mcp.tool()
def configure_llm(api_key: str, model: str = "") -> str:
    """
    Choose which Anthropic API key and Claude model draft_clause,
    draft_legal_memo, and summarize_document use for the rest of this
    session. `model` is optional — omit it to keep the server's default
    model.

    Caution: this server runs as a single shared process. If more than one
    client connects to the same deployment, configure_llm's choice is
    process-wide, not per-connection — a later call from any client can
    change which key/model everyone's drafting calls use.
    """
    return llm.configure(api_key, model)


@mcp.tool()
def draft_clause(
    instruction: str,
    clause_type: str = "general",
    tone: str = "formal",
    reference_text: str = "",
) -> str:
    """
    Draft a single contract clause with an LLM.

    `instruction` describes what the clause needs to accomplish. `clause_type`
    names the kind of clause (e.g. "indemnification", "limitation of liability").
    `reference_text` is optional retrieved precedent (e.g. from
    search_legal_vault) to ground the drafted language in.

    Uses whichever API key/model was set via configure_llm, or the server's
    default if configure_llm hasn't been called.
    """
    try:
        return llm.draft_clause(instruction, clause_type, tone, reference_text)
    except Exception as e:
        return f"Clause drafting error: {e}"


@mcp.tool()
def draft_legal_memo(
    topic: str,
    key_facts: str,
    jurisdiction: str = "",
    legal_questions: str = "",
    research_context: str = "",
) -> str:
    """
    Draft a structured legal research memo (Question Presented, Brief Answer,
    Facts, Discussion, Conclusion) with an LLM.

    `research_context` is optional retrieved material (e.g. from
    search_legal_vault or outside research) to ground the analysis in.

    Uses whichever API key/model was set via configure_llm, or the server's
    default if configure_llm hasn't been called.
    """
    try:
        return llm.draft_legal_memo(topic, key_facts, jurisdiction, legal_questions, research_context)
    except Exception as e:
        return f"Memo drafting error: {e}"


@mcp.tool()
def summarize_document(document_text: str, focus: str = "key obligations, deadlines, and risks") -> str:
    """
    Summarize a legal document with an LLM, flagging obligations, deadlines,
    and risks a reviewing attorney should not miss.

    Uses whichever API key/model was set via configure_llm, or the server's
    default if configure_llm hasn't been called.
    """
    try:
        return llm.summarize_document(document_text, focus)
    except Exception as e:
        return f"Summarization error: {e}"


if __name__ == "__main__":
    port = os.environ.get("PORT")
    if port:
        # Deployed (Railway sets PORT): serve MCP over HTTP so remote
        # clients can connect to https://<app>.up.railway.app/mcp
        mcp.run(transport="http", host="0.0.0.0", port=int(port))
    else:
        # Local dev/testing only: stdio, launched directly by an MCP client.
        mcp.run()
