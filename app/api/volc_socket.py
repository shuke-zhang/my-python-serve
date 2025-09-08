# app/api/volc_socket.py
from flask import Blueprint
from flask import request
from flask_socketio import SocketIO
from flask_socketio import emit
from app.schemas.volc_speech_schema import StartSessionIn
from app.schemas.volc_speech_schema import TextIn
from app.services.volc_session_service import session_manager

bp = Blueprint("volc_socket", __name__)

NAMESPACE:str = "/doubao/speech-recognition"

def init_socketio(socketio: SocketIO) -> None:
    _bind_namespace(socketio, namespace=NAMESPACE)

def _bind_namespace(socketio: SocketIO, namespace: str) -> None:
    def on_connect() -> None:
        emit("connected", {"sid": request.sid}, namespace=namespace)
    def on_disconnect() -> None:
        session_manager.remove(request.sid)
    def on_start_session(data: dict) -> None:
        try:
            body = StartSessionIn(**(data or {}))
            sid = request.sid
            def _emit(event: str, payload) -> None:
                socketio.emit(event, payload, to=sid, namespace=namespace)
            import uuid
            session_manager.create(
                sid=sid,
                emit=_emit,
                session_id=str(uuid.uuid4()),
                output_audio_format=body.output_audio_format,
                start_session_overrides=body.start_session_overrides
            )
        except Exception as e:
            emit("error", {"message": f"start_session_failed: {e}"}, namespace=namespace)
    def on_say_hello() -> None:
        bridge = session_manager.get(request.sid)
        if not bridge:
            emit("error", {"message": "no_session"}, namespace=namespace)
            return
        bridge.say_hello()
    def on_send_text(data: dict) -> None:
        bridge = session_manager.get(request.sid)
        if not bridge:
            emit("error", {"message": "no_session"}, namespace=namespace)
            return
        try:
            body = TextIn(**(data or {}))
            bridge.send_text(body.content)
        except Exception as e:
            emit("error", {"message": f"text_failed: {e}"}, namespace=namespace)
    def on_send_audio(data) -> None:
        bridge = session_manager.get(request.sid)
        if not bridge:
            emit("error", {"message": "no_session"}, namespace=namespace)
            return
        if isinstance(data, (bytes, bytearray)):
            bridge.send_audio(bytes(data))
            return
        emit("error", {"message": "audio_should_be_binary"}, namespace=namespace)
    def on_finish() -> None:
        sid = request.sid
        bridge = session_manager.get(sid)
        if not bridge:
            emit("error", {"message": "no_session"}, namespace=namespace)
            return
        try:
            bridge.finish()
            session_manager.remove(sid)
            emit("finished", {"ok": True}, namespace=namespace)
        except Exception as e:
            emit("error", {"message": f"finish_failed: {e}"}, namespace=namespace)

    socketio.on_event("connect", on_connect, namespace=namespace)
    socketio.on_event("disconnect", on_disconnect, namespace=namespace)
    socketio.on_event("start_session", on_start_session, namespace=namespace)
    socketio.on_event("say_hello", on_say_hello, namespace=namespace)
    socketio.on_event("send_text", on_send_text, namespace=namespace)
    socketio.on_event("send_audio", on_send_audio, namespace=namespace)
    socketio.on_event("finish", on_finish, namespace=namespace)
