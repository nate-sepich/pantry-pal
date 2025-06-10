from fastapi import APIRouter, Depends, HTTPException
from auth.auth_service import get_user_id_from_token
from models.models import ChatMeta, Chat
from storage.utils import (
    read_chat_meta,
    upsert_chat_meta,
    read_chat,
    upsert_chat,
    delete_chat,
)

chat_router = APIRouter(prefix="/chats")

@chat_router.get("/", response_model=list[ChatMeta])
def list_chats(user_id: str = Depends(get_user_id_from_token)):
    return read_chat_meta(user_id)

@chat_router.post("/", status_code=204)
def save_chat(meta: ChatMeta, user_id: str = Depends(get_user_id_from_token)):
    upsert_chat_meta(user_id, meta)
    return None


@chat_router.get("/{chat_id}", response_model=Chat)
def get_chat(chat_id: str, user_id: str = Depends(get_user_id_from_token)):
    chat = read_chat(user_id, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@chat_router.put("/{chat_id}", status_code=204)
def save_chat_detail(chat_id: str, chat: Chat, user_id: str = Depends(get_user_id_from_token)):
    chat.id = chat_id
    upsert_chat(user_id, chat)
    meta = ChatMeta(id=chat.id, title=chat.title, updatedAt=chat.updatedAt, length=len(chat.messages))
    upsert_chat_meta(user_id, meta)
    return None


@chat_router.delete("/{chat_id}", status_code=204)
def delete_chat_api(chat_id: str, user_id: str = Depends(get_user_id_from_token)):
    delete_chat(user_id, chat_id)
    return None
