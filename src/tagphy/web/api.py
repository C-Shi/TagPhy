from fastapi import APIRouter, Body, HTTPException, status, Response, Query
from fastapi.responses import JSONResponse
from typing import Annotated, Any
from tagphy.db import SQLiteConnection
from tagphy.web.utils import SettingsStore, PictureHelper, TagHelper, BrowseHelper
from tagphy.tools import ScanJobController, BusyError, ImageProcessingPipeline

router = APIRouter(prefix="/api")
tag_helper = TagHelper(db=SQLiteConnection())
picture_helper = PictureHelper(db=SQLiteConnection())
settings_store = SettingsStore(db=SQLiteConnection())
scan_job = ScanJobController(ImageProcessingPipeline())
browse_helper = BrowseHelper()


# Tag Routes
@router.get("/tags")
async def tag_info():
    return tag_helper.get_tags_with_details()


@router.get("/tags/{tag_id}/pictures")
async def get_tag(tag_id: int):
    try:
        tag_pictures_response = tag_helper.get_tag_pictures(tag_id)
        # get all direct and indirect images

        image_tag_ids = [child["id"] for child in tag_pictures_response["children"]]
        image_tag_ids.append(tag_id)
        # called with OR logic because image_tag_ids is a list of tag sharing the same parent
        images = picture_helper.get_pictures_for_tags(image_tag_ids, logic="OR")
        tag_pictures_response["pictures"] = [dict(image) for image in images]
        return tag_pictures_response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Picture Routes
@router.get("/pictures")
async def get_pictures(
    pagination: int = 1, tag_ids: Annotated[list[int], Query()] = []
):
    # this query implement the AND logic for multiple tags - picture selections
    try:
        # get all selected tags and their children tags
        selected_tag_ids = []
        for tag_id in tag_ids:
            # get all descendants tags including the current tag
            descendants = tag_helper.get_descendants_tags(tag_id)
            descendants_ids = [descendant["id"] for descendant in descendants]
            descendants_ids.append(tag_id)
            # append them into separate lists
            selected_tag_ids.append(descendants_ids)
        pictures = picture_helper.get_pictures_for_tags(
            page=pagination, tag_ids=selected_tag_ids
        )
        return pictures
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/pictures/{picture_id}/preview")
async def get_picture_preview(picture_id: int):
    try:
        preview = picture_helper.get_picture_preview(picture_id)
        return Response(
            content=preview[0], media_type="image/jpeg", headers={"Alt": preview[1]}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Scan Routes
@router.get("/scan/browse")
async def scan_browse(path: str = ""):
    try:
        return browse_helper.list_directory(path)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/scan")
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


@router.post("/scan_stop")
async def scan_stop():
    return scan_job.stop()


@router.get("/scan/status")
async def scan_status():
    return {"status": scan_job.job_state}


# Settings Routes
@router.get("/settings")
async def get_settings():
    return settings_store.load()


@router.put("/settings/{config}")
async def update_setting(config: str, payload: dict[str, Any] = Body(...)):
    try:
        return settings_store.set(config, payload.get("value"))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
