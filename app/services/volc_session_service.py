# app/services/volc_session_service.py
import asyncio
import threading
import json
from typing import Optional
from typing import Dict
from typing import Any
from typing import Callable

import config
from app.vendors.volc.realtime_dialog_client import RealtimeDialogClient



EmitFunc = Callable[[str, Any], None]

class SessionBridge:
    def __init__(self, sid: str, emit: EmitFunc) -> None:
        self.sid = sid
        self.emit = emit
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.client: Optional[RealtimeDialogClient] = None
        self.session_id: Optional[str] = None
        self.running = False

    def start(self, session_id: str, output_audio_format: str, start_session_overrides: Optional[Dict[str, Any]]) -> None:
        def runner() -> None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._start_async(session_id, output_audio_format, start_session_overrides))
        self.thread = threading.Thread(target=runner, daemon=True)
        self.thread.start()

    async def _start_async(self, session_id: str, output_audio_format: str, start_session_overrides: Optional[Dict[str, Any]]) -> None:
        self.session_id = session_id
        ws_cfg = { "base_url": config.VOLC_BASE_URL, "headers": config.build_ws_headers() }
        self.client = RealtimeDialogClient(config=ws_cfg, session_id=session_id, output_audio_format=output_audio_format)
        if start_session_overrides:
            import copy
            import config as cfg
            self._bak_req = copy.deepcopy(cfg.start_session_req) if hasattr(cfg, "start_session_req") else None
            cfg.start_session_req = start_session_overrides
        try:
            await self.client.connect()
            self.running = True
            self.emit("session_started", { "session_id": session_id, "logid": self.client.logid })
            await self._reader_loop()
        except Exception as e:
            self.emit("error", { "message": f"connect_or_loop_failed: {e}" })
        finally:
            if start_session_overrides and hasattr(config, "start_session_req"):
                try:
                    import config as cfg2
                    if getattr(self, "_bak_req", None) is not None:
                        cfg2.start_session_req = self._bak_req
                except Exception:
                    pass

    async def _reader_loop(self) -> None:
        assert self.client is not None
        while True:
            try:
                data = await self.client.receive_server_response()
                if not data:
                    continue
                if isinstance(data, dict) and data.get("message_type") == "SERVER_ACK" and isinstance(data.get("payload_msg"), (bytes, bytearray)):
                    self.emit("server_audio", data["payload_msg"])
                else:
                    self.emit("server_event", data)
            except Exception as e:
                self.emit("error", { "message": f"receive_failed: {e}" })
                break
        self.running = False

    def say_hello(self) -> None:
        if not self.loop or not self.client:
            return
        fut = asyncio.run_coroutine_threadsafe(self.client.say_hello(), self.loop)
        fut.result()

    def send_text(self, content: str) -> None:
        if not self.loop or not self.client:
            return
        fut = asyncio.run_coroutine_threadsafe(self.client.chat_text_query(content), self.loop)
        fut.result()

    def send_audio(self, chunk: bytes) -> None:
        if not self.loop or not self.client:
            return
        fut = asyncio.run_coroutine_threadsafe(self.client.task_request(chunk), self.loop)
        fut.result()

    def finish(self) -> None:
        if not self.loop or not self.client:
            return
        try:
            fut1 = asyncio.run_coroutine_threadsafe(self.client.finish_session(), self.loop)
            fut1.result(timeout=5)
        except Exception:
            pass
        try:
            fut2 = asyncio.run_coroutine_threadsafe(self.client.finish_connection(), self.loop)
            fut2.result(timeout=5)
        except Exception:
            pass
        try:
            fut3 = asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)
            fut3.result(timeout=5)
        except Exception:
            pass
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass

class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionBridge] = {}

    def create(self, sid: str, emit: EmitFunc, session_id: str, output_audio_format: str, start_session_overrides: Optional[Dict[str, Any]]) -> None:
        bridge = SessionBridge(sid=sid, emit=emit)
        self._sessions[sid] = bridge
        bridge.start(session_id=session_id, output_audio_format=output_audio_format, start_session_overrides=start_session_overrides)

    def get(self, sid: str) -> Optional[SessionBridge]:
        return self._sessions.get(sid)

    def remove(self, sid: str) -> None:
        if sid in self._sessions:
            try:
                self._sessions[sid].finish()
            except Exception:
                pass
            self._sessions.pop(sid, None)

session_manager = SessionManager()
