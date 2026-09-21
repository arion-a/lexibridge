"""LLM-backed drafting and summarization for legal work product.

Each drafting call accepts an optional `api_key` / `model` so a caller can
use their own Anthropic account and model choice instead of the server's
default — falls back to the server's ANTHROPIC_API_KEY / ANTHROPIC_MODEL
env vars when omitted.
"""

from anthropic import Anthropic

import config

_clients = {}


def _get_client(api_key: str = ""):
    key = api_key or config.ANTHROPIC_API_KEY
    if not key:
        raise RuntimeError(
            "No Anthropic API key available — pass `api_key` to the tool call, "
            "or set ANTHROPIC_API_KEY in the server's environment."
        )
    if key not in _clients:
        _clients[key] = Anthropic(api_key=key)
    return _clients[key]


def _complete(system: str, user: str, api_key: str = "", model: str = "", max_tokens: int = 1500) -> str:
    response = _get_client(api_key).messages.create(
        model=model or config.ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def draft_clause(
    instruction: str,
    clause_type: str,
    tone: str,
    reference_text: str,
    api_key: str = "",
    model: str = "",
) -> str:
    system = (
        "You are a senior transactional attorney drafting a single contract clause. "
        "Produce precise, enforceable legal language appropriate for a definitive agreement."
    )
    user = f"Clause type: {clause_type}\nTone: {tone}\nDrafting instruction: {instruction}"
    if reference_text:
        user += (
            "\n\nGround the language in this retrieved precedent where relevant, "
            f"adapting rather than copying verbatim:\n{reference_text}"
        )
    return _complete(system, user, api_key=api_key, model=model)


def draft_legal_memo(
    topic: str,
    key_facts: str,
    jurisdiction: str,
    legal_questions: str,
    research_context: str,
    api_key: str = "",
    model: str = "",
) -> str:
    system = (
        "You are a legal associate drafting an internal legal research memo. "
        "Structure the memo with these headings: Question Presented, Brief Answer, "
        "Facts, Discussion, Conclusion."
    )
    user = (
        f"Topic: {topic}\n"
        f"Jurisdiction: {jurisdiction or 'Not specified'}\n"
        f"Key facts: {key_facts}\n"
        f"Legal questions: {legal_questions or 'General analysis requested'}"
    )
    if research_context:
        user += f"\n\nGround the analysis in this retrieved research context where applicable:\n{research_context}"
    return _complete(system, user, api_key=api_key, model=model, max_tokens=2500)


def summarize_document(document_text: str, focus: str, api_key: str = "", model: str = "") -> str:
    system = (
        "You are a legal analyst. Summarize legal documents accurately and concisely, "
        "flagging obligations, deadlines, and risks a reviewing attorney should not miss."
    )
    user = f"Focus areas: {focus}\n\nDocument:\n{document_text}"
    return _complete(system, user, api_key=api_key, model=model, max_tokens=1200)
