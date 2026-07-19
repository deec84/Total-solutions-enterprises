"""Root API router."""

from fastapi import APIRouter

from app.presentation.api.routes.admin import router as admin_router
from app.presentation.api.routes.auth import router as auth_router
from app.presentation.api.routes.community import router as community_router
from app.presentation.api.routes.health import router as health_router
from app.presentation.api.routes.notifications import router as notifications_router
from app.presentation.api.routes.parking import router as parking_router
from app.presentation.api.routes.parking_ai import router as parking_ai_router
from app.presentation.api.routes.privacy import router as privacy_router
from app.presentation.api.routes.recommendations import router as recommendations_router
from app.presentation.api.routes.recovery import router as recovery_router
from app.presentation.api.routes.sign_scanner import router as sign_scanner_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(parking_router, prefix="/parking", tags=["parking-map"])
api_router.include_router(parking_ai_router, prefix="/ai", tags=["parking-ai"])
api_router.include_router(sign_scanner_router, prefix="/signs", tags=["sign-scanner"])
api_router.include_router(community_router, prefix="/reports", tags=["community-reports"])
api_router.include_router(admin_router, prefix="/admin", tags=["administration"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(recovery_router, prefix="/recovery", tags=["towing-recovery"])
api_router.include_router(
    recommendations_router, prefix="/recommendations", tags=["parking-recommendations"]
)
api_router.include_router(privacy_router, prefix="/privacy", tags=["privacy"])
