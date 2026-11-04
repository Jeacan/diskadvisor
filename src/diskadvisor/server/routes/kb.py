"""知识库 API。"""

from __future__ import annotations

from fastapi import APIRouter, Query

from diskadvisor.kb import KnowledgeBase
from diskadvisor.kb.validator import KBValidator

router = APIRouter()


@router.get("/kb/list")
async def list_kb() -> list[dict]:
    """列出知识库所有软件。"""
    kb = KnowledgeBase()
    entries = kb.all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "category": e.category.value,
            "recommendedInstallPath": e.recommendedInstallPath,
        }
        for e in entries
    ]


@router.get("/kb/search")
async def search_kb(q: str = Query(..., min_length=1)) -> list[dict]:
    """搜索知识库。"""
    kb = KnowledgeBase()
    results = kb.search(q)
    return [
        {
            "id": e.id,
            "name": e.name,
            "category": e.category.value,
        }
        for e in results
    ]


@router.get("/kb/validate")
async def validate_kb() -> dict:
    """校验知识库。"""
    validator = KBValidator()
    issues = validator.validate()
    return {
        "total": len(issues),
        "errors": [str(i) for i in issues if i.level == "error"],
        "warnings": [str(i) for i in issues if i.level == "warning"],
    }