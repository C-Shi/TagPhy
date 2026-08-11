from fastapi import APIRouter, HTTPException, status, Response, Query
from typing import Annotated
from tagphy.db import SQLiteConnection
from tagphy.web.utils.tag_helper import TagHelper
from tagphy.web.utils.picture_helper import PictureHelper

router = APIRouter(prefix="/api")
tag_helper = TagHelper(db=SQLiteConnection())
picture_helper = PictureHelper(db=SQLiteConnection())


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
        images = picture_helper.get_pictures_for_tags_flatted(image_tag_ids)
        tag_pictures_response["pictures"] = [dict(image) for image in images]
        return tag_pictures_response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Picture Routes
@router.get("/pictures")
async def get_pictures(
    pagination: int = 1, tag_ids: Annotated[list[int], Query()] = []
):
    try:
        # get all selected tags and their children tags
        selected_tag_ids = [*tag_ids]
        for tag_id in tag_ids:
            descendants = tag_helper.get_descendants_tags(tag_id)
            selected_tag_ids.extend([descendant["id"] for descendant in descendants])
        selected_tag_ids = tuple(set(selected_tag_ids))
        pictures = picture_helper.get_pictures_for_tags_flatted(
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
