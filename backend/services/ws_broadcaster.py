import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket


class WebSocketBroadcaster:
    """Central hub for broadcasting real-time events to WebSocket clients."""

    def __init__(self):
        self.subscriptions: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, ws: WebSocket, channels: list[str]):
        async with self._lock:
            for ch in channels:
                self.subscriptions[ch].add(ws)

    async def unsubscribe(self, ws: WebSocket):
        async with self._lock:
            for ch in list(self.subscriptions):
                self.subscriptions[ch].discard(ws)
                if not self.subscriptions[ch]:
                    del self.subscriptions[ch]

    async def broadcast(self, channel: str, data: dict):
        message = json.dumps({"channel": channel, "data": data})
        dead = []
        for ws in self.subscriptions.get(channel, set()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.unsubscribe(ws)
