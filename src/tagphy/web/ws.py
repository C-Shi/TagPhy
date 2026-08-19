import asyncio
import queue

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from tagphy.tools.scan_job import ScanJobController
from tagphy.web.utils.web_socket import ConnectionManager

router = APIRouter(prefix="/ws")

manager = ConnectionManager()
_broadcaster_task: asyncio.Task | None = None


async def _broadcast_scan_logs() -> None:
    """Single reader for the shared scan log queue; fan out to all WS clients."""
    scan_job = ScanJobController()
    while True:
        try:
            while True:
                try:
                    next_log = scan_job.scan_logs.get_nowait()
                except queue.Empty:
                    break
                await manager.broadcast_json(next_log)
            await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            raise


def start_scan_log_broadcaster() -> asyncio.Task:
    global _broadcaster_task
    if _broadcaster_task is None or _broadcaster_task.done():
        _broadcaster_task = asyncio.create_task(
            _broadcast_scan_logs(), name="scan_log_broadcaster"
        )
    return _broadcaster_task


async def stop_scan_log_broadcaster() -> None:
    global _broadcaster_task
    if _broadcaster_task is not None:
        _broadcaster_task.cancel()
        try:
            await _broadcaster_task
        except asyncio.CancelledError:
            pass
        _broadcaster_task = None


@router.websocket("/scan_log")
async def scan_log_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
