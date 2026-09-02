from fastapi import APIRouter

from tagphy.web.routes.tags import router as tag_router
from tagphy.web.routes.pictures import router as picture_router
from tagphy.web.routes.scan import router as scan_router
from tagphy.web.routes.settings import router as settings_router
from tagphy.web.routes.agents import router as agent_router

router = APIRouter(prefix="/api")
router.include_router(tag_router)
router.include_router(picture_router)
router.include_router(scan_router)
router.include_router(settings_router)
router.include_router(agent_router)
