"""Start and stop this checkout's local services on macOS."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
DATA = ROOT / ".local-data" / "jobpilot"
SERVICES = (("CareerVault", 8776), ("JobPilot", 8765))
HTTP = build_opener(ProxyHandler({}))


def health(name: str, port: int) -> bool:
    try:
        with HTTP.open(f"http://127.0.0.1:{port}/api/health", timeout=3) as response:
            data = json.load(response)
        location = data.get("root") if name == "CareerVault" else data.get("db")
        expected = ROOT / name if name == "CareerVault" else DATA / "jobpilot.db"
        return bool(data.get("ok")) and Path(location or "").resolve() == expected
    except (OSError, ValueError):
        return False


def owned_pid(name: str) -> int | None:
    try:
        pid = int((RUNTIME / f"{name}.pid").read_text())
        if pid <= 1:
            return None
        command = subprocess.check_output(
            ["/bin/ps", "-p", str(pid), "-o", "command="], text=True
        )
        return pid if str(ROOT / name / "run.py") in command else None
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None


def start_service(name: str, port: int) -> None:
    if health(name, port):
        print(f"[OK] {name} 已在运行。")
        return
    with socket.socket() as connection:
        if connection.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError(f"端口 {port} 已被占用，请先检查或停止原有服务。")
    env = os.environ.copy()
    env.update(JOBPILOT_DATA_DIR=str(DATA), JOBPILOT_HOST="127.0.0.1",
               JOBPILOT_PORT="8765", CAREERVAULT_URL="http://127.0.0.1:8776")
    git_dir = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback"
    if (git_dir / "git").is_file():
        env["PATH"] = str(git_dir) + os.pathsep + env.get("PATH", "")
    log_path = RUNTIME / f"{name}.log"
    with log_path.open("a") as log:
        process = subprocess.Popen(
            [str(ROOT / ".venv/bin/python"), str(ROOT / name / "run.py")],
            cwd=ROOT / name, env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=log, start_new_session=True,
        )
    pid_path = RUNTIME / f"{name}.pid"
    pid_path.write_text(str(process.pid))
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if health(name, port):
            print(f"[OK] {name}: http://127.0.0.1:{port}")
            return
        if process.poll() is not None:
            break
        time.sleep(0.3)
    if process.poll() is None:
        process.terminate()
        process.wait(timeout=10)
    pid_path.unlink(missing_ok=True)
    raise RuntimeError(f"{name} 启动失败，请查看 {log_path}")


def stop_service(name: str, port: int) -> None:
    pid = owned_pid(name)
    if pid is None:
        print(f"[OK] {name} 没有本启动器管理的运行进程。")
        return
    if name == "JobPilot" and health(name, port):
        try:
            with HTTP.open(f"http://127.0.0.1:{port}/api/sync/status", timeout=3) as response:
                sync = json.load(response)
            if sync.get("configured") and sync.get("auto_close_sync"):
                with HTTP.open(Request(
                    f"http://127.0.0.1:{port}/api/sync/commit?reason=shutdown", method="POST"
                ), timeout=20) as response:
                    response.read()
        except OSError as exc:
            print(f"[提示] 关闭同步未完成：{exc}")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 10
    while owned_pid(name) is not None and time.monotonic() < deadline:
        time.sleep(0.2)
    if owned_pid(name) is not None:
        raise RuntimeError(f"{name} 尚未退出，请查看日志或稍后重试。")
    (RUNTIME / f"{name}.pid").unlink(missing_ok=True)
    print(f"[OK] {name} 已停止。")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "stop"))
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    RUNTIME.mkdir(exist_ok=True)
    if args.action == "start":
        for name, port in SERVICES:
            start_service(name, port)
        if not args.no_open:
            subprocess.run(["/usr/bin/open", "http://127.0.0.1:8765"], check=True)
    else:
        for name, port in reversed(SERVICES):
            stop_service(name, port)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
