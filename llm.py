"""LLM-backed drafting and summarization for legal work product."""

from anthropic import Anthropic

import config

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _complete(system: str, user: str, max_tokens: int = 1500) -> str:
    response = _get_client().messages.create(
        model=config.ANTHROPIC_MODEL,
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
