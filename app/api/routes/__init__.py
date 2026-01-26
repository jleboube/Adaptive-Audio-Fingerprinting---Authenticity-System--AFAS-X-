"""API routes for AFAS-X."""

from fastapi import APIRouter

from app.api.routes import auth, fingerprint, health, provenance, verify

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(fingerprint.router, prefix="/fingerprint", tags=["fingerprint"])
router.include_router(verify.router, prefix="/verify", tags=["verify"])
router.include_router(provenance.router, prefix="/provenance", tags=["provenance"])
