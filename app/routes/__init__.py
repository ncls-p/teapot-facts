from fastapi import APIRouter

from .completions import router as completions_router
from .fact_check import router as fact_check_router
from .health import router as health_router
from .models import router as models_router

router = APIRouter()

router.include_router(completions_router, prefix="/v1", tags=["completions"])
router.include_router(fact_check_router, tags=["fact-check"])
router.include_router(health_router, tags=["health"])
router.include_router(models_router, prefix="/v1", tags=["models"])
