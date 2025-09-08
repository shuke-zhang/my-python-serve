"""
占位提示：
请把官方 Demo 里的 protocol.py 内容原样粘贴到本文件。
该文件定义了 generate_header、parse_response、常量 CLIENT_AUDIO_ONLY_REQUEST、NO_SERIALIZATION 等。
没有真实实现时，下面的占位函数会抛出异常，提醒你替换。
"""

CLIENT_AUDIO_ONLY_REQUEST = 0
NO_SERIALIZATION = 0

def generate_header(message_type: int = 0, serial_method: int = 0) -> bytes:
    raise RuntimeError("protocol.py 是占位版本。请用官方 Demo 的完整实现替换本文件。")

def parse_response(data: bytes):
    raise RuntimeError("protocol.py 是占位版本。请用官方 Demo 的完整实现替换本文件。")
