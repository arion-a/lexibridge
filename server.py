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
def draft_clause(
    instruction: str,
    clause_type: str = "general",
    tone: str = "formal",
    reference_text: str = "",
    api_key: str = "",
    model: str = "",
) -> str:
    """
    Draft a single contract clause with an LLM.

    `instruction` describes what the clause needs to accomplish. `clause_type`
    names the kind of clause (e.g. "indemnification", "limitation of liability").
    `reference_text` is optional retrieved precedent (e.g. from
    search_legal_vault) to ground the drafted language in.

    `api_key` is your own Anthropic API key (falls back to the server's
    ANTHROPIC_API_KEY if omitted — ask whoever runs this deployment whether
    one is set). `model` optionally picks which Claude model to use.
    """
    try:
        return llm.draft_clause(instruction, clause_type, tone, reference_text, api_key=api_key, model=model)
    except Exception as e:
        return f"Clause drafting error: {e}"


@mcp.tool()
def draft_legal_memo(
    topic: str,
    key_facts: str,
    jurisdiction: str = "",
    legal_questions: str = "",
    research_context: str = "",
    api_key: str = "",
    model: str = "",
) -> str:
    """
    Draft a structured legal research memo (Question Presented, Brief Answer,
    Facts, Discussion, Conclusion) with an LLM.

    `research_context` is optional retrieved material (e.g. from
    search_legal_vault or outside research) to ground the analysis in.

    `api_key` is your own Anthropic API key (falls back to the server's
    ANTHROPIC_API_KEY if omitted). `model` optionally picks which Claude
    model to use.
    """
    try:
        return llm.draft_legal_memo(
            topic, key_facts, jurisdiction, legal_questions, research_context, api_key=api_key, model=model
        )
    except Exception as e:
        return f"Memo drafting error: {e}"


@mcp.tool()
def summarize_document(
    document_text: str,
    focus: str = "key obligations, deadlines, and risks",
    api_key: str = "",
    model: str = "",
) -> str:
    """
    Summarize a legal document with an LLM, flagging obligations, deadlines,
    and risks a reviewing attorney should not miss.

    `api_key` is your own Anthropic API key (falls back to the server's
    ANTHROPIC_API_KEY if omitted). `model` optionally picks which Claude
    model to use.
    """
    try:
        return llm.summarize_document(document_text, focus, api_key=api_key, model=model)
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
