from fastapi import APIRouter, HTTPException, status
from tagphy.db import SQLiteConnection
from tagphy.web.utils.tag_helper import TagHelper

router = APIRouter(prefix="/api")
tag_helper = TagHelper(db=SQLiteConnection())


@router.get("/tags")
async def tag_info():
    return tag_helper.get_tags_with_details()


@router.get("/tags/{tag_id}/pictures")
async def get_tag(tag_id: int):
    try:
        return tag_helper.get_tag_pictures(tag_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
