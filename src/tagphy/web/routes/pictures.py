from fastapi import APIRouter, HTTPException, status, Response, Query
from typing import Annotated
from tagphy.db import SQLiteConnection
from tagphy.tools.db_operations import RecordNotFoundError, TagHelper, PictureHelper

router = APIRouter(prefix="/pictures")
tag_helper = TagHelper(db=SQLiteConnection())
picture_helper = PictureHelper(db=SQLiteConnection())


# Picture Routes
@router.get("")
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


@router.get("/{picture_id}")
async def get_picture(picture_id: int):
    try:
        # get picture info
        picture = picture_helper.get_picture(picture_id)
        # remove unrelated or unserializable fields to match UI
        picture.pop("description_embedding", None)
        picture.pop("created_at", None)
        picture.pop("updated_at", None)

        # get picture tags
        tags = tag_helper.get_tags_for_picture(picture_id)
        picture["tags"] = tags
        return picture
    except RecordNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{picture_id}/preview")
async def get_picture_preview(picture_id: int, size: int | None = None):
    try:
        if size:
            preview = picture_helper.get_picture_preview(picture_id, size)
        else:
            preview = picture_helper.get_picture_preview(picture_id)
        return Response(
            content=preview[0], media_type="image/jpeg", headers={"Alt": preview[1]}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
