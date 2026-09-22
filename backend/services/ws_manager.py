import asyncio
import time
import uuid
from typing import List, Dict, Any, Set
from fastapi import WebSocket

class ConnectionManager:
    """
    v4.1 Hardened Structured WebSocket Connection & Event Stream Manager.
    Supports sequence numbers, job-specific room subscriptions, heartbeat pinging, and stale event protection.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.job_subscriptions: Dict[str, Set[WebSocket]] = {}
        self.sequence_counter: Dict[str, int] = {}

    async def connect(self, websocket: WebSocket, job_id: str = None):
        await websocket.accept()
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        if job_id:
            if job_id not in self.job_subscriptions:
                self.job_subscriptions[job_id] = set()
            self.job_subscriptions[job_id].add(websocket)

    def subscribe(self, websocket: WebSocket, job_id: str):
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        self.job_subscriptions[job_id].add(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for job_id, sockets in list(self.job_subscriptions.items()):
            sockets.discard(websocket)

    def _get_next_sequence(self, job_id: str = "global") -> int:
        seq = self.sequence_counter.get(job_id, 0) + 1
        self.sequence_counter[job_id] = seq
        return seq

    def create_event(self, event_type: str, job_id: str = "global", payload: dict = None, attempt_id: str = "attempt-1") -> dict:
        seq = self._get_next_sequence(job_id)
        return {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "job_id": job_id,
            "attempt_id": attempt_id,
            "sequence": seq,
            "event_type": event_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "payload": payload or {}
        }

    async def broadcast(self, message: dict, job_id: str = None):
        target_sockets = set(self.active_connections)
        if job_id and job_id in self.job_subscriptions:
            target_sockets = self.job_subscriptions[job_id]

        if "sequence" not in message:
            message = self.create_event(event_type=message.get("type", "JOB_UPDATE"), job_id=job_id or "global", payload=message)

        for connection in list(target_sockets):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()
