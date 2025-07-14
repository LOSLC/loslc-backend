from fastapi import APIRouter

from app.api.routes.v1.controllers.auth import router as auth_router
from app.api.routes.v1.controllers.file import router as file_router
from app.api.routes.v1.controllers.form import router as form_router
from app.api.routes.v1.controllers.link import router as link_router
from app.api.routes.v1.controllers.miscellaneous import (
    router as miscellaneous_router,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(form_router)
router.include_router(file_router)
router.include_router(link_router)
router.include_router(miscellaneous_router)
