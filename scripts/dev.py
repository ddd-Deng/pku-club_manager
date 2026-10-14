"""Windows desktop launcher for this checkout's frontend, backend and SSH tunnel."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
LOCAL = ROOT / ".dev.local"
STATE = LOCAL / "processes.json"
SERVER = "group7@8.130.213.80"
URL = "http://127.0.0.1:5173/"
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class LaunchError(Exception):
    pass


def powershell(code):
    code = "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); " + code
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", code],
        capture_output=True,
        encoding="utf-8",
        creationflags=HIDDEN,
        check=True,
    )
    return json.loads(result.stdout.strip() or "null")


def process_info(pid):
    return powershell(
        f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}'; "
        "if ($p) { [pscustomobject]@{pid=$p.ProcessId;parent=$p.ParentProcessId;"
        "name=$p.Name;command=$p.CommandLine;"
        "created=$p.CreationDate.ToUniversalTime().ToString('o')} | ConvertTo-Json -Compress }"
    )


def listener(port):
    pid = powershell(
        f"$p=@(Get-NetTCPConnection -State Listen -LocalPort {int(port)} "
        "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); "
        "if ($p.Count -gt 1) { throw 'Multiple processes own the port' }; "
        "if ($p.Count -eq 1) { $p[0] | ConvertTo-Json }"
    )
    return process_info(pid) if pid else None


def belongs_to_project(kind, process, port):
    if not process:
        return False
    command = (process.get("command") or "").replace("/", "\\").lower()
    name = (process.get("name") or "").lower()
    if kind == "ssh":
        target = f"127.0.0.1:{port}:127.0.0.1:{port}"
        return name == "ssh.exe" and SERVER in command and target in command and "1021" in command
    if kind == "backend":
        return (
            name == "python.exe"
            and (str(BACKEND).lower() + "\\") in command
            and "uvicorn app.main:app" in command
            and "8080" in command
        )
    return (
        name == "node.exe"
        and (str(FRONTEND).lower() + "\\") in command
        and "vite" in command
        and "5173" in command
    )


def record(kind, process, port):
    if kind == "backend":
        parent = process_info(process["parent"])
        if belongs_to_project(kind, parent, port):
            process = parent
    return {"kind": kind, "pid": process["pid"], "created": process["created"], "port": port}


def terminate(item):
    process = process_info(item["pid"])
    if (
        not process
        or process["created"] != item["created"]
        or not belongs_to_project(item["kind"], process, item["port"])
    ):
        return
    result = subprocess.run(
        ["taskkill.exe", "/PID", str(item["pid"]), "/T", "/F"],
        capture_output=True,
        creationflags=HIDDEN,
    )
    if result.returncode and process_info(item["pid"]):
        raise LaunchError(f"停止失败：PID {item['pid']}；请查看该进程所属终端。")


def wait_port(kind, port, child, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if child.poll() is not None:
            return None
        process = listener(port)
        if process:
            if not belongs_to_project(kind, process, port):
                raise LaunchError(f"端口 {port} 被其他进程占用，未停止该进程。")
            return record(kind, process, port)
        time.sleep(0.5)
    return None


def spawn(kind, args, directory, port, owned, interactive=False):
    if interactive:
        child = subprocess.Popen(args, cwd=directory, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        env = os.environ.copy()
        if kind == "frontend":
            env.update(VITE_USE_MOCK="false", VITE_API_BASE_URL="http://127.0.0.1:8080")
        with (LOCAL / f"{kind}.log").open("ab") as log:
            child = subprocess.Popen(
                args, cwd=directory, env=env, stdout=log, stderr=log, creationflags=HIDDEN
            )
    process = process_info(child.pid)
    if process and belongs_to_project(kind, process, port):
        owned.append(record(kind, process, port))
    return child


def reuse(kind, port, managed):
    process = listener(port)
    if not process:
        return False
    if not belongs_to_project(kind, process, port):
        raise LaunchError(f"端口 {port} 被其他进程占用，未停止该进程。")
    managed.append(record(kind, process, port))
    print(f"复用已运行的 {kind}（端口 {port}）。", flush=True)
    return True


def ensure_ssh(port, owned, managed):
    if reuse("ssh", port, managed):
        return
    ssh = shutil.which("ssh")
    if not ssh:
        raise LaunchError("缺少 OpenSSH 客户端，请先在 Windows 可选功能中安装。")
    args = [
        ssh,
        "-N",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=3",
        "-o",
        "ConnectTimeout=10",
        "-L",
        f"127.0.0.1:{port}:127.0.0.1:{port}",
        "-p",
        "1021",
        SERVER,
    ]
    print("建立共享数据库 SSH 连接……", flush=True)
    child = spawn(
        "ssh",
        args + ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes"],
        ROOT,
        port,
        owned,
    )
    item = wait_port("ssh", port, child, 15)
    if not item:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)
        print("请在新打开的 SSH 窗口确认服务器指纹并输入服务器密码；等待最多 90 秒。", flush=True)
        child = spawn("ssh", args, ROOT, port, owned, interactive=True)
        item = wait_port("ssh", port, child, 90)
    if not item:
        raise LaunchError("SSH 连接未建立，请检查服务器、网络和登录权限。")
    managed.append(item)


def check_database():
    sys.path.insert(0, str(BACKEND))
    try:
        from app.config import Settings
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url

        settings = Settings()
        settings.require_database()
        settings.require_secret()
        return settings, make_url(settings.database_url), create_engine, text
    except Exception as exc:
        raise LaunchError(
            "后端依赖或 backend/.env 不完整，请按 backend/README.md 完成首次配置。"
        ) from exc


def http_ready(url, expected=None, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    if expected is None or json.load(response)["data"]["source"] == expected:
                        return
        except (OSError, ValueError, KeyError, urllib.error.URLError):
            pass
        time.sleep(0.5)
    raise LaunchError(f"服务未就绪：{url}；请查看 .dev.local 中的日志。")


def start(no_browser):
    node = shutil.which("node")
    vite = FRONTEND / "node_modules/vite/bin/vite.js"
    python = BACKEND / ".venv/Scripts/python.exe"
    if not node or not vite.is_file() or not python.is_file():
        raise LaunchError(
            "依赖尚未安装，请先完成 frontend/README.md 和 backend/README.md 的安装步骤。"
        )
    settings, database_url, create_engine, text = check_database()
    managed, owned = [], []
    try:
        if database_url.host in ("localhost", "127.0.0.1") and database_url.port in (13307, 14307):
            ensure_ssh(database_url.port, owned, managed)
        engine = create_engine(settings.database_url, connect_args={"connect_timeout": 5})
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception as exc:
            raise LaunchError(
                "数据库不可用。请确认服务器 MySQL 已运行及 backend/.env 正确；不会自动重置数据库。"
            ) from exc
        finally:
            engine.dispose()
        if not reuse("backend", 8080, managed):
            child = spawn(
                "backend",
                [
                    str(python),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8080",
                ],
                BACKEND,
                8080,
                owned,
            )
            item = wait_port("backend", 8080, child, 30)
            if not item:
                raise LaunchError("后端启动失败，请查看 .dev.local/backend.log。")
            managed.append(item)
        http_ready("http://127.0.0.1:8080/api/test/hello", expected="server")
        if not reuse("frontend", 5173, managed):
            child = spawn(
                "frontend",
                [node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
                FRONTEND,
                5173,
                owned,
            )
            item = wait_port("frontend", 5173, child, 30)
            if not item:
                raise LaunchError("前端启动失败，请查看 .dev.local/frontend.log。")
            managed.append(item)
        http_ready(URL)
        STATE.write_text(json.dumps(managed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"启动完成：{URL}\n双击 scripts/stop.cmd 可以停止本机项目服务。", flush=True)
        if not no_browser:
            webbrowser.open(URL)
    except BaseException:
        for item in reversed(owned):
            terminate(item)
        raise


def stop():
    managed = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else []
    for kind, port in (("frontend", 5173), ("backend", 8080), ("ssh", 13307), ("ssh", 14307)):
        process = listener(port)
        if belongs_to_project(kind, process, port):
            managed.append(record(kind, process, port))
    seen = set()
    for item in sorted(
        managed, key=lambda row: {"frontend": 0, "backend": 1, "ssh": 2}[row["kind"]]
    ):
        if item["pid"] not in seen:
            terminate(item)
            seen.add(item["pid"])
    remaining = []
    for kind, port in (("frontend", 5173), ("backend", 8080), ("ssh", 13307), ("ssh", 14307)):
        if belongs_to_project(kind, listener(port), port):
            remaining.append(port)
    if remaining:
        raise LaunchError(f"仍有项目端口在运行：{remaining}")
    STATE.unlink(missing_ok=True)
    print("本机前端、后端及 SSH 隧道已停止；服务器共享数据库继续运行。", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "stop"])
    parser.add_argument(
        "--no-browser", action="store_true", help="Do not open the browser after startup"
    )
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit(
            "This launcher is for Windows; use the documented commands on other systems."
        )
    LOCAL.mkdir(exist_ok=True)
    try:
        with launcher_lock():
            if args.action == "start":
                start(args.no_browser)
            else:
                stop()
    except (LaunchError, subprocess.SubprocessError, OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, LaunchError) else type(exc).__name__
        print(f"启动/停止失败：{message}", file=sys.stderr, flush=True)
        return 1
    return 0


@contextmanager
def launcher_lock():
    import msvcrt

    with (LOCAL / "launcher.lock").open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise LaunchError("已有启动或停止操作正在进行，请等待该操作完成。") from exc
        try:
            yield
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    raise SystemExit(main())
