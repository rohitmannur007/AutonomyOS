from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import KnowledgeArticle
from app import schemas

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("", response_model=list[schemas.KnowledgeArticleOut])
def list_knowledge(db: Session = Depends(get_db)):
    return db.query(KnowledgeArticle).order_by(KnowledgeArticle.category, KnowledgeArticle.title).all()
