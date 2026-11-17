from fastapi import APIRouter, Depends
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.models import ChatRequest, ChatResponse, Citation, UserResponse
from app.services.rag_engine import ask_knowledge_base
from app.api.dependencies import get_current_user

router = APIRouter()

class LegacyChatRequest(BaseModel):
    user_id: str
    question: str

@router.post("/query", response_model=ChatResponse)
async def query_knowledge_base(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    result = ask_knowledge_base(
        user_id=current_user.id,
        user_role=current_user.role.value,
        question=request.query,
        filter_documents=request.filter_documents
    )

    formatted_citations = []
    for c in result.get("citations", []):
        formatted_citations.append(Citation(
            document_name=c.get("file_name") or c.get("document_name", "Document"),
            page_number=c.get("page_number", 1),
            snippet=c.get("snippet", ""),
            score=c.get("score")
        ))

    return ChatResponse(
        answer=result.get("answer", "No response generated."),
        citations=formatted_citations,
        model_used=result.get("model_used", "gemini-3.1-flash-lite")
    )

@router.post("/ask")
async def chat_with_docs(
    request: LegacyChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    result = ask_knowledge_base(
        user_id=current_user.id,
        user_role=current_user.role.value,
        question=request.question
    )
    return result
