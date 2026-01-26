"""API dependencies for AFAS-X."""

from app.api.dependencies.auth import (
    get_api_key_user,
    get_authenticated_user,
    get_authenticated_user_optional,
    get_current_user,
    get_current_user_optional,
)

__all__ = [
    "get_api_key_user",
    "get_authenticated_user",
    "get_authenticated_user_optional",
    "get_current_user",
    "get_current_user_optional",
]
