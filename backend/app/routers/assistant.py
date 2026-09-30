from fastapi import APIRouter

router = APIRouter(tags=["assistant"])


@router.post("/assistant/chat")
def assistant_placeholder(payload: dict):
    return {"message": "The Part B assistant will be implemented jointly.", "received": payload}
