from fastapi import APIRouter, Depends
from auth.auth_service import get_user_id_from_token
from models.models import ChatMeta
from storage.utils import read_chat_meta, upsert_chat_meta

chat_router = APIRouter(prefix="/chats")


@chat_router.get("/", response_model=list[ChatMeta])
def list_chats(user_id: str = Depends(get_user_id_from_token)):
    return read_chat_meta(user_id)


@chat_router.post("/", status_code=204)
def save_chat(meta: ChatMeta, user_id: str = Depends(get_user_id_from_token)):
    upsert_chat_meta(user_id, meta)
    return None
