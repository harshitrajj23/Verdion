from typing import List, Optional
from fastapi import Header, HTTPException, status
from backend.app.core.config import settings
from backend.app.core.errors import UnauthorizedResolutionException


def get_current_actor(
    x_actor_address: Optional[str] = Header(None, alias="X-Actor-Address"),
    x_role: Optional[str] = Header("CASE_OWNER", alias="X-Role")
) -> dict:
    """Extracts actor address and role from request headers."""
    actor_address = x_actor_address or "0x0000000000000000000000000000000000000000"
    role = (x_role or "CASE_OWNER").upper()
    return {
        "address": actor_address,
        "role": role
    }


def require_role(allowed_roles: List[str]):
    """Enforces role-based authorization on state-changing endpoints."""
    def dependency(
        x_actor_address: Optional[str] = Header(None, alias="X-Actor-Address"),
        x_role: Optional[str] = Header("CASE_OWNER", alias="X-Role")
    ) -> dict:
        actor = get_current_actor(x_actor_address, x_role)
        role = actor["role"]
        address = actor["address"]

        # Admin override
        if role == "ADMIN" or address.lower() == settings.ADMIN_ADDRESS.lower():
            return actor

        if role not in [r.upper() for r in allowed_roles]:
            raise UnauthorizedResolutionException(
                f"Role '{role}' is not authorized. Required: {allowed_roles}",
                details={"current_role": role, "allowed_roles": allowed_roles}
            )
        return actor
    return dependency
