from fastapi import APIRouter

from online_dev.form_manager.api import router as form_manager_router
from online_dev.form_data_manager.api import router as form_data_manager_router
from online_dev.page_manager.api import router as page_manager_router



router = APIRouter()
router.include_router(form_manager_router)
router.include_router(form_data_manager_router)
router.include_router(page_manager_router)

