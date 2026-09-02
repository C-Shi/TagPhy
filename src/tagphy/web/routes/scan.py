from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from tagphy.db import SQLiteConnection
from tagphy.web.utils import SettingsStore, BrowseHelper
from tagphy.tools import ScanJobController, BusyError, ImageProcessingPipeline

router = APIRouter(prefix="/scan")
browse_helper = BrowseHelper()
scan_job = ScanJobController(ImageProcessingPipeline())
settings_store = SettingsStore(db=SQLiteConnection())


# Scan Routes
@router.get("/browse")
async def scan_browse(path: str = ""):
    try:
        return browse_helper.list_directory(path)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("")
async def scan(path: str = Body(..., embed=True, description="The path to scan")):
    try:
        precheck = settings_store.privacy_pre_check_enabled()
        return scan_job.start(path, config={"privacy_pre_check": precheck})
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": scan_job.job_state, "message": str(e)},
        )
    except BusyError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": scan_job.job_state, "message": str(e)},
        )


@router.post("/stop")
async def scan_stop():
    return scan_job.stop()


@router.get("/status")
async def scan_status():
    return {"status": scan_job.job_state}
