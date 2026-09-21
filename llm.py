"""LLM-backed drafting and summarization for legal work product.

The Anthropic API key and model are chosen once via `configure()` (exposed
as the `configure_llm` MCP tool) rather than passed to every drafting call.
Falls back to the server's ANTHROPIC_API_KEY / ANTHROPIC_MODEL env vars
until configured.
"""

from anthropic import Anthropic

import config

_clients = {}
_chosen_api_key = None
_chosen_model = None


def configure(api_key: str, model: str = "") -> str:
    """Set the API key / model the drafting tools use for the rest of this session."""
    global _chosen_api_key, _chosen_model
    _chosen_api_key = api_key or None
    _chosen_model = model or None
    return f"LexiBridge drafting tools will now use model '{_resolve_model()}'."


def _resolve_key() -> str:
    return _chosen_api_key or config.ANTHROPIC_API_KEY


def _resolve_model() -> str:
    return _chosen_model or config.ANTHROPIC_MODEL


def _get_client():
    key = _resolve_key()
    if not key:
        raise RuntimeError(
            "No Anthropic API key configured — call configure_llm(api_key=...) first, "
            "or set ANTHROPIC_API_KEY in the server's environment."
        )
    if key not in _clients:
        _clients[key] = Anthropic(api_key=key)
    return _clients[key]


def _complete(system: str, user: str, max_tokens: int = 1500) -> str:
    response = _get_client().messages.create(
        model=_resolve_model(),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def draft_clause(instruction: str, clause_type: str, tone: str, reference_text: str) -> str:
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
    return _complete(system, user)


def draft_legal_memo(
    topic: str,
    key_facts: str,
    jurisdiction: str,
    legal_questions: str,
    research_context: str,
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
    return _complete(system, user, max_tokens=2500)


def summarize_document(document_text: str, focus: str) -> str:
    system = (
        "You are a legal analyst. Summarize legal documents accurately and concisely, "
        "flagging obligations, deadlines, and risks a reviewing attorney should not miss."
    )
    user = f"Focus areas: {focus}\n\nDocument:\n{document_text}"
    return _complete(system, user, max_tokens=1200)
