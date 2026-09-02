from fastapi import APIRouter, Body, HTTPException, status
from typing import Any
from tagphy.db import SQLiteConnection
from tagphy.web.utils import SettingsStore

router = APIRouter(prefix="/settings")
settings_store = SettingsStore(db=SQLiteConnection())


# Settings Routes
@router.get("")
async def get_settings():
    return settings_store.load()


@router.put("/{config}")
async def update_setting(config: str, payload: dict[str, Any] = Body(...)):
    try:
        return settings_store.set(config, payload.get("value"))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
