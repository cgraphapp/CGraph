from fastapi import APIRouter

router = APIRouter()

@router.get("/messages")
async def list_messages():
    return {"messages": []}
