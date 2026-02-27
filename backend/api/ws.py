import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    from backend.main import broadcaster

    await ws.accept()
    try:
        while True:
            text = await ws.receive_text()
            try:
                msg = json.loads(text)
            except json.JSONDecodeError:
                continue

            action = msg.get("action")
            channels = msg.get("channels", [])

            if action == "subscribe" and channels:
                await broadcaster.subscribe(ws, channels)
                await ws.send_text(json.dumps({"action": "subscribed", "channels": channels}))
            elif action == "unsubscribe" and channels:
                await broadcaster.unsubscribe(ws)
                await ws.send_text(json.dumps({"action": "unsubscribed"}))
    except WebSocketDisconnect:
        await broadcaster.unsubscribe(ws)
