# run.py
import os
import sys
import platform
import socket
from app import socketio
from datetime import datetime
from typing import Iterable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.table import Table
from rich import box
import eventlet
eventlet.monkey_patch()
# 兼容你的工程：既支持 from app import app，也支持工厂函数 create_app()
try:
    from app import app  # Flask 实例
except Exception:
    from app import create_app  # 工厂
    app = create_app()

console = Console()

def _human_url(host: str, port: int, https: bool) -> str:
    scheme = "https" if https else "http"
    return f"{scheme}://{host}:{port}"

def _print_banner(host: str, port: int, debug: bool, https: bool) -> None:
    title = Text("🚀 服务已启动", style="bold green")
    subtitle = Text(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
    lan_ip = _guess_lan_ip()

    info = Table.grid(padding=(0, 2))
    info.add_row("项目", Text(os.path.basename(os.getcwd()), style="bold"))
    info.add_row("环境", Text("开发模式" if debug else "生产模式", style="yellow" if debug else "cyan"))
    info.add_row("地址(本机)", Text(_human_url(host, port, https), style="bold blue"))
    info.add_row("地址(内网)", Text(_human_url(lan_ip, port, https), style="bold blue"))
    info.add_row("Python", Text(platform.python_version()))
    info.add_row("Flask", Text(getattr(app, "import_name", "app")))
    info.add_row("PID", Text(str(os.getpid())))

    console.print(Panel.fit(info, title=title, subtitle=subtitle, border_style="green", box=box.ROUNDED))

def _print_routes() -> None:
    table = Table(title="📚 路由一览", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Rule", style="white")
    table.add_column("方法", style="magenta")
    table.add_column("端点", style="yellow")

    # 只展示常见方法并按路径排序
    common = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    for r in rules:
        methods = ",".join(sorted(m for m in r.methods if m in common))
        if not methods:
            continue
        table.add_row(r.rule, methods, r.endpoint)

    if len(table.rows) > 0:
        console.print(table)

def _build_base_url(host: str, port: int, https: bool) -> str:
    scheme = "https" if https else "http"
    return f"{scheme}://{host}:{port}"

def _safe_handlers(socketio) -> dict:
    try:
        server = socketio.server
        handlers = getattr(server, "handlers", {}) or {}
        return handlers
    except Exception:
        return {}
def print_socketio_map(socketio, console, host: str = "0.0.0.0", port: int = 5000, https: bool = False, path: str = "/socket.io") -> None:
    base = _build_base_url(host, port, https)
    handlers = _safe_handlers(socketio)
    if not handlers:
        console.print("未发现 Socket.IO 事件", style="dim")
        return
    table = Table(
        title="🧩 Socket.IO 事件一览（前端可直接调用）",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        expand=True
    )
    table.add_column("命名空间", no_wrap=True)
    table.add_column("连接地址（前端 io(...) 用）", no_wrap=False, overflow="fold", ratio=2)
    table.add_column("可用事件（emit）", no_wrap=False, overflow="fold", ratio=1)
    namespaces: Iterable[str] = sorted(handlers.keys(), key=lambda x: x or "/")
    for ns in namespaces:
        evmap = handlers.get(ns, {}) or {}
        events = sorted(e for e in evmap.keys() if e not in ("connect", "disconnect"))
        ns_suffix = "" if (ns in ("/", "", None)) else ns
        connect_url = f'{base}{ns_suffix}'
        connect_str = f'io("{connect_url}", {{ path: "{path}", transports: ["websocket"], reconnection: true }})'
        table.add_row(
            ns or "/",
            Text(connect_str, overflow="fold", no_wrap=False),
            Text(", ".join(events) or "—", overflow="fold", no_wrap=False)
        )
    console.print(table)
    for ns in namespaces:
        ns_suffix = "" if (ns in ("/", "", None)) else ns
        connect_url = f'{base}{ns_suffix}'
       
    console.print(Text(f"Engine.IO 入口：{path}", style="dim"))
def _quiet_werkzeug_banner() -> None:
    # 可选：降低 werkzeug 启动横幅与请求日志的噪音；想完全保留就注释掉
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

def _guess_lan_ip() -> str:
    ip = "0.0.0.0"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass
    return ip

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    https = False  # 若你在 Nginx/TLS 反代后，可改 True 仅用于输出展示

    # 只在“真正运行的子进程”里打印一次（避免 Debug 重载打印两次）
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if is_reloader_child or not debug:
        _quiet_werkzeug_banner()
        _print_banner(host, port, debug, https)
        _print_routes()
        print_socketio_map(socketio, console)
        console.print("🔧 按 Ctrl+C 退出\n", style="dim")

    # 启动开发服务器
    app.run(host=host, port=port, debug=debug, use_reloader=True)
