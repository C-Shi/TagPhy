from fastapi import APIRouter, HTTPException, status
from tagphy.db import SQLiteConnection
from tagphy.tools.db_operations import TagHelper, PictureHelper

router = APIRouter(prefix="/tags")
tag_helper = TagHelper(db=SQLiteConnection())
picture_helper = PictureHelper(db=SQLiteConnection())


# Tag Routes
@router.get("")
async def tag_info():
    return tag_helper.get_tags_with_details()


@router.get("/{tag_id}/pictures")
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
