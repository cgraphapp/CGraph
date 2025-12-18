from fastapi import APIRouter

router = APIRouter()

@router.get("/forums")
async def list_forums():
    return {"forums": []}
