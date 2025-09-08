# app/schemas/volc_speech_schema.py
from pydantic import BaseModel
from typing import Optional
from typing import Dict
from typing import Any

class StartSessionIn(BaseModel):
    output_audio_format: str = "pcm"
    start_session_overrides: Optional[Dict[str, Any]] = None

class TextIn(BaseModel):
    content: str
