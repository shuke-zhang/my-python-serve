# run.py
import os
import sys
import platform
import socket
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
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

def _quiet_werkzeug_banner() -> None:
    # 可选：降低 werkzeug 启动横幅与请求日志的噪音；想完全保留就注释掉
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

def _guess_lan_ip() -> str:
    ip = "127.0.0.1"
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
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    https = False  # 若你在 Nginx/TLS 反代后，可改 True 仅用于输出展示

    # 只在“真正运行的子进程”里打印一次（避免 Debug 重载打印两次）
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if is_reloader_child or not debug:
        _quiet_werkzeug_banner()
        _print_banner(host, port, debug, https)
        _print_routes()
        console.print("🔧 按 Ctrl+C 退出\n", style="dim")

    # 启动开发服务器
    app.run(host=host, port=port, debug=debug, use_reloader=True)
