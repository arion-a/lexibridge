"""LexiBridge: an MCP server for faster legal research and drafting with LLMs."""

import json

from fastmcp import FastMCP

import llm
import vault

mcp = FastMCP("LexiBridge")


@mcp.tool()
def search_legal_vault(query: str, max_results: int = 4) -> str:
    """
    Semantically search the firm's legal vault (contract clauses, precedent
    language, and prior work product) for passages relevant to `query`.

    Returns a JSON list of {source_document, page, text_content, relevance_score}.
    Use this before drafting to ground new language in existing precedent.
    """
    try:
        results = vault.search_clauses(query, max_results=max_results)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Vault search error: {e}"


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
    """
    try:
        return llm.summarize_document(document_text, focus)
    except Exception as e:
        return f"Summarization error: {e}"


if __name__ == "__main__":
    mcp.run()
