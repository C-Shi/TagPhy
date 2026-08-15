from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from tagphy.web.utils.web_socket import ConnectionManager

router = APIRouter(prefix="/ws")

manager = ConnectionManager()


@router.websocket("/scan_log")
async def scan_log_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await manager.send_personal_message(f"Scan Log Aquired", websocket)
    except WebSocketDisconnect as e:
        manager.disconnect(websocket)
