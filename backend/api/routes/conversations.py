from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.security.authentication.rbac import get_current_user_token as verify_token_dependency
from database.supabase_client import SupabaseDB

router = APIRouter(prefix="/conversations", tags=["User Conversations"])


class ConversationResponse(BaseModel):
    id: str
    title: str | None
    created_at: str
    updated_at: str


class MessageCreate(BaseModel):
    conversation_id: str
    role: str
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(user: dict = Depends(verify_token_dependency)):
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = SupabaseDB()
    try:
        response = (
            await db.client.table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return [ConversationResponse(**row) for row in response.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    title: str | None = None, user: dict = Depends(verify_token_dependency)
):
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = SupabaseDB()
    try:
        response = (
            await db.client.table("conversations")
            .insert({"user_id": user_id, "title": title or "New Conversation"})
            .execute()
        )
        return ConversationResponse(**response.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str, message: MessageCreate, user: dict = Depends(verify_token_dependency)
):
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = SupabaseDB()
    try:
        # AUD-2.3/2.5: verify the requesting user actually owns the conversation
        # before writing into it. The service-role client used here bypasses RLS,
        # so the previous "database policy should ensure" assumption did not hold.
        ownership = (
            await db.client.table("conversations")
            .select("id")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not ownership.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        response = (
            await db.client.table("messages")
            .insert(
                {
                    "conversation_id": conversation_id,
                    "role": message.role,
                    "content": message.content,
                }
            )
            .execute()
        )

        # Update conversation timestamp
        await (
            db.client.table("conversations")
            .update({"updated_at": "now()"})
            .eq("id", conversation_id)
            .execute()
        )

        return MessageResponse(**response.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
