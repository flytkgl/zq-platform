from fastapi import APIRouter

from core.chat.api import router as chat_api_router

router = APIRouter()
router.include_router(chat_api_router)
