from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.chatbot import ChatMessageSend, ChatMessageOut, ChatSessionOut
from app.schemas.common import APIResponse
from app.services.chatbot_service import ChatbotService

router = APIRouter()


@router.post("/sessions", response_model=APIResponse)
async def create_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """開始客服對話"""
    svc = ChatbotService(db)
    session = await svc.create_session(current_user.id)
    # Reload with messages eagerly loaded
    session = await svc.get_session(session.id)
    return APIResponse(data=ChatSessionOut.model_validate(session), message="客服對話已開始")


@router.post("/sessions/{session_id}/messages", response_model=APIResponse)
async def send_message(
    session_id: str,
    data: ChatMessageSend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """發送訊息"""
    svc = ChatbotService(db)
    messages = await svc.send_message(session_id, data.content)
    return APIResponse(data=[ChatMessageOut.model_validate(m) for m in messages])


@router.get("/sessions/{session_id}", response_model=APIResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得對話歷史"""
    svc = ChatbotService(db)
    session = await svc.get_session(session_id)
    return APIResponse(data=ChatSessionOut.model_validate(session))


@router.post("/sessions/{session_id}/end", response_model=APIResponse)
async def end_session(
    session_id: str,
    rating: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """結束對話"""
    svc = ChatbotService(db)
    await svc.end_session(session_id, rating)
    return APIResponse(message="客服對話已結束")
