"""
Knowledge Retrieval Service.

Simple, transparent keyword-based retrieval over the enterprise knowledge
base — no vector database, no embeddings. Each article carries a comma
separated keyword list; the article whose keywords best overlap the ticket
text (and whose allowed_action matches the AI's proposed action, when
possible) is returned as supporting evidence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import KnowledgeArticle


def _score(article: KnowledgeArticle, lowered_text: str, proposed_action: Optional[str]) -> int:
    score = 0
    for kw in article.keywords.split(","):
        kw = kw.strip().lower()
        if kw and kw in lowered_text:
            score += 2
    if proposed_action and article.allowed_action == proposed_action:
        score += 1
    return score


def retrieve_articles(
    db: Session,
    ticket_text: str,
    proposed_action: Optional[str] = None,
    limit: int = 3,
) -> List[KnowledgeArticle]:
    lowered = ticket_text.lower()
    articles = db.query(KnowledgeArticle).all()
    scored = [(a, _score(a, lowered, proposed_action)) for a in articles]
    scored = [pair for pair in scored if pair[1] > 0]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    if not scored and proposed_action:
        # Nothing matched on keywords — fall back to any article that
        # performs the same action so the ticket still has supporting policy.
        fallback = [a for a in articles if a.allowed_action == proposed_action]
        return fallback[:limit]

    return [a for a, _ in scored[:limit]]


def best_article(
    db: Session, ticket_text: str, proposed_action: Optional[str] = None
) -> Optional[KnowledgeArticle]:
    articles = retrieve_articles(db, ticket_text, proposed_action, limit=1)
    return articles[0] if articles else None
