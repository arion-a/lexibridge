"""LexiBridge: an MCP server for faster legal research and drafting with LLMs."""

import json

from fastmcp import FastMCP

import llm
import vault

mcp = FastMCP("LexiBridge")


@mcp.tool()
async def search_legal_vault(query: str, max_results: int = 4) -> str:
    """
    Semantically search the firm's legal vault (contract clauses, precedent
    language, and prior work product) for passages relevant to `query`.

    The query is embedded on-device and only the vector is sent to the
    cloud bridge for matching; the actual clause text is re-hydrated from
    the local vector store, so raw text never leaves this machine.

    Returns a JSON list of {source_document, page, text_content, relevance_score}.
    Use this before drafting to ground new language in existing precedent.
    """
    try:
        results = await vault.search_clauses(query, max_results=max_results)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Vault search error: {e}"


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

    `api_key` lets the caller use their own Anthropic API key instead of the
    server's default (falls back to the server's ANTHROPIC_API_KEY env var
    if omitted). `model` lets the caller pick which Claude model to use
    (falls back to the server's ANTHROPIC_MODEL default if omitted).
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

    `api_key` lets the caller use their own Anthropic API key instead of the
    server's default (falls back to the server's ANTHROPIC_API_KEY env var
    if omitted). `model` lets the caller pick which Claude model to use
    (falls back to the server's ANTHROPIC_MODEL default if omitted).
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

    `api_key` lets the caller use their own Anthropic API key instead of the
    server's default (falls back to the server's ANTHROPIC_API_KEY env var
    if omitted). `model` lets the caller pick which Claude model to use
    (falls back to the server's ANTHROPIC_MODEL default if omitted).
    """
    try:
        return llm.summarize_document(document_text, focus, api_key=api_key, model=model)
    except Exception as e:
        return f"Summarization error: {e}"


if __name__ == "__main__":
    mcp.run()
