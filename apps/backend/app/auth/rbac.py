from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_admin
from app.models.admin import Admin
from app.models.enums import AdminRole


def require_roles(*roles: AdminRole) -> Callable:
    async def checker(admin: Admin = Depends(get_current_admin)) -> Admin:
        if admin.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Бұл әрекетке рұқсатыңыз жоқ",
            )
        return admin

    return checker


require_super_admin = require_roles(AdminRole.SUPER_ADMIN)
require_dispatcher_or_above = require_roles(AdminRole.SUPER_ADMIN, AdminRole.DISPATCHER)
require_any_admin = require_roles(AdminRole.SUPER_ADMIN, AdminRole.DISPATCHER, AdminRole.OPERATOR)
