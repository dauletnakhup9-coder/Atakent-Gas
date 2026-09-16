from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.auth.jwt import decode_access_token
from app.services.realtime import manager

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/applications")
async def applications_ws(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        decode_access_token(token)
    except ValueError:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
