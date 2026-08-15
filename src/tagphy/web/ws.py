import queue, asyncio
from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from tagphy.web.utils.web_socket import ConnectionManager
from tagphy.tools.scan_job import ScanJobController, ScanLog

router = APIRouter(prefix="/ws")

manager = ConnectionManager()


@router.websocket("/scan_log")
async def scan_log_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    scan_job = ScanJobController()
    try:
        while True:
            try:
                next_log: ScanLog = scan_job.scan_logs.get_nowait()
                await manager.send_json(next_log, websocket)

            except queue.Empty as e:
                await asyncio.sleep(2)  # avoid busy-waiting

    except WebSocketDisconnect as e:
        manager.disconnect(websocket)
