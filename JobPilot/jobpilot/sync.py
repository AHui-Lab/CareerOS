from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from . import db

SYNC_DIR = db.DATA_DIR / "sync-repo"
CONFIG_PATH = db.DATA_DIR / "private" / "sync-config.json"
PASSPHRASE_PATH = db.DATA_DIR / "private" / "sync-passphrase"
ARCHIVE_NAME = "careeros-data.enc"
CAREEROS_ROOT = db.ROOT.parent
VAULT_ROOT = CAREEROS_ROOT / "CareerVault" / "vault"
VAULT_PRIVATE = CAREEROS_ROOT / "CareerVault" / "private"


def _read_config() -> dict[str, Any]:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"branch": "main", "auto_start_check": True, "auto_close_sync": True}


def _write_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def configure(remote_url: str, branch: str = "main", passphrase: str = "", auto_start_check: bool = True, auto_close_sync: bool = True) -> dict[str, Any]:
    remote_url = remote_url.strip()
    if not remote_url or len(passphrase) < 8:
        raise ValueError("请填写私有 Git 仓库地址，并设置至少 8 位同步口令。")
    config = _read_config()
    config.update({"remote_url": remote_url, "branch": branch.strip() or "main", "auto_start_check": bool(auto_start_check), "auto_close_sync": bool(auto_close_sync)})
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PASSPHRASE_PATH.write_text(passphrase, encoding="utf-8")
    _write_config(config)
    return status()


def _passphrase() -> str:
    try:
        return PASSPHRASE_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(SYNC_DIR), *args], text=True, capture_output=True, timeout=45)
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "Git 操作失败").strip()[-800:])
    return (result.stdout or "").strip()


def _ensure_repo() -> None:
    config = _read_config()
    remote = str(config.get("remote_url") or "").strip()
    if not remote:
        raise ValueError("请先在设置和帮助中配置私有 Git 仓库。")
    SYNC_DIR.mkdir(parents=True, exist_ok=True)
    if not (SYNC_DIR / ".git").exists():
        _git("init", check=True)
        _git("remote", "add", "origin", remote)
    else:
        _git("remote", "set-url", "origin", remote)
    if not _git("config", "user.email", check=False):
        _git("config", "user.email", "careeros-sync@users.noreply.github.com")
    if not _git("config", "user.name", check=False):
        _git("config", "user.name", "CareerOS Sync")


def _derive(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def _make_archive() -> bytes:
    if not db.DB_PATH.exists():
        raise ValueError("本地数据库不存在。")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        db.backup_database(keep=20)
        zip_path = root / "snapshot.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(db.DB_PATH, "jobpilot.db")
            private = db.DATA_DIR / "private"
            if private.exists():
                for item in private.rglob("*"):
                    if item.is_file() and item.name not in {"sync-passphrase", "sync-config.json"}:
                        archive.write(item, str(Path("private") / item.relative_to(private)))
            if VAULT_ROOT.exists():
                for item in VAULT_ROOT.rglob("*"):
                    if item.is_file() and ".git" not in item.parts:
                        archive.write(item, str(Path("careervault-vault") / item.relative_to(VAULT_ROOT)))
            if VAULT_PRIVATE.exists():
                for item in VAULT_PRIVATE.rglob("*"):
                    if item.is_file():
                        archive.write(item, str(Path("careervault-private") / item.relative_to(VAULT_PRIVATE)))
            manifest = {"version": 1, "created_at": datetime.now().isoformat(timespec="seconds"), "sha256": hashlib.sha256(db.DB_PATH.read_bytes()).hexdigest(), "data_status": db.data_status()}
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        salt = os.urandom(16)
        token = Fernet(_derive(_passphrase(), salt)).encrypt(zip_path.read_bytes())
        return b"CAREEROS-SYNC-V1\n" + base64.b64encode(salt) + b"\n" + token


def _unpack_archive(payload: bytes, target: Path) -> dict[str, Any]:
    if not _passphrase():
        raise ValueError("本机没有同步口令。")
    try:
        _, salt_line, token = payload.split(b"\n", 2)
        plain = Fernet(_derive(_passphrase(), base64.b64decode(salt_line))).decrypt(token)
    except (ValueError, InvalidToken, Exception) as exc:
        raise ValueError("无法解密远程数据，请确认两台电脑使用同一个同步口令。") from exc
    target.mkdir(parents=True, exist_ok=True)
    zip_path = target / "snapshot.zip"
    zip_path.write_bytes(plain)
    with zipfile.ZipFile(zip_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        archive.extractall(target / "content")
    return manifest


def _make_accept_backup() -> str:
    backup = db.BACKUP_DIR / f"sync-accept-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    backup.mkdir(parents=True, exist_ok=True)
    db.backup_database(keep=20)
    shutil.copy2(db.DB_PATH, backup / "jobpilot.db")
    for source, name in ((VAULT_ROOT, "careervault-vault"), (VAULT_PRIVATE, "careervault-private"), (db.DATA_DIR / "private", "jobpilot-private")):
        if source.exists(): shutil.copytree(source, backup / name, dirs_exist_ok=True)
    return str(backup)


def _remote_head() -> str:
    _ensure_repo()
    branch = str(_read_config().get("branch") or "main")
    result = _git("ls-remote", "origin", f"refs/heads/{branch}", check=True)
    return result.split()[0] if result else ""


def status() -> dict[str, Any]:
    config = _read_config()
    return {"configured": bool(config.get("remote_url") and _passphrase()), "remote_url": config.get("remote_url", ""), "branch": config.get("branch", "main"), "auto_start_check": bool(config.get("auto_start_check", True)), "auto_close_sync": bool(config.get("auto_close_sync", True)), "last_checked_at": config.get("last_checked_at", ""), "last_sync_at": config.get("last_sync_at", ""), "pending_remote": bool(config.get("pending_remote")), "pending_head": config.get("pending_head", ""), "last_error": config.get("last_error", ""), "rollback_available": bool(config.get("rollback_backup")) and Path(str(config.get("rollback_backup"))).exists()}


def check() -> dict[str, Any]:
    config = _read_config()
    if not config.get("remote_url") or not _passphrase():
        return status()
    try:
        head = _remote_head()
        config["last_checked_at"] = datetime.now().isoformat(timespec="seconds")
        config["pending_remote"] = bool(head and head != config.get("last_sync_head", ""))
        config["pending_head"] = head if config["pending_remote"] else ""
        config["last_error"] = ""
        _write_config(config)
    except Exception as exc:
        config["last_error"] = str(exc); _write_config(config)
    return status()


def commit(reason: str = "manual") -> dict[str, Any]:
    _ensure_repo(); config = _read_config()
    if reason == "shutdown" and not config.get("auto_close_sync", True):
        return status()
    current = _remote_head()
    if current and config.get("pending_remote"):
        raise ValueError("远程有尚未确认的更新，请先预览并接受，或在另一台电脑完成处理。")
    (SYNC_DIR / ARCHIVE_NAME).write_bytes(_make_archive())
    (SYNC_DIR / "README.md").write_text("CareerOS 加密数据同步仓库。请勿删除 careeros-data.enc，也不要把此仓库改为公开。\n", encoding="utf-8")
    _git("add", ARCHIVE_NAME, "README.md")
    if _git("diff", "--cached", "--name-only", check=False):
        _git("commit", "-m", f"sync: {reason}")
    branch = str(config.get("branch") or "main")
    _git("branch", "-M", branch)
    _git("push", "-u", "origin", branch)
    config.update({"last_sync_at": datetime.now().isoformat(timespec="seconds"), "last_sync_head": _git("rev-parse", "HEAD"), "pending_remote": False, "pending_head": "", "last_error": ""})
    _write_config(config)
    return status()


def accept() -> dict[str, Any]:
    _ensure_repo(); config = _read_config(); branch = str(config.get("branch") or "main")
    _git("fetch", "origin", branch)
    _git("checkout", "-B", branch, f"origin/{branch}")
    payload = (SYNC_DIR / ARCHIVE_NAME).read_bytes()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp); manifest = _unpack_archive(payload, root)
        backup = _make_accept_backup()
        private = db.DATA_DIR / "private"
        restore_private = root / "content" / "private"
        if restore_private.exists():
            for item in private.iterdir() if private.exists() else []:
                if item.name not in {"sync-config.json", "sync-passphrase"}:
                    shutil.rmtree(item) if item.is_dir() else item.unlink()
            shutil.copytree(restore_private, private, dirs_exist_ok=True)
        for source_root, target_root in ((root / "content" / "careervault-vault", VAULT_ROOT), (root / "content" / "careervault-private", VAULT_PRIVATE)):
            if source_root.exists():
                target_root.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source_root, target_root, dirs_exist_ok=True)
        source = root / "content" / "jobpilot.db"
        shutil.copy2(source, db.DB_PATH)
        db.init_db()
        config.update({"rollback_backup": backup, "last_sync_head": _git("rev-parse", "HEAD"), "pending_remote": False, "pending_head": "", "last_error": ""})
        _write_config(config)
    return {**status(), "manifest": manifest}


def rollback() -> dict[str, Any]:
    config = _read_config(); backup = Path(str(config.get("rollback_backup") or ""))
    if not backup.exists(): raise ValueError("没有可回滚的上次接受版本。")
    db.backup_database(keep=20); shutil.copy2(backup / "jobpilot.db", db.DB_PATH)
    for source, target in ((backup / "careervault-vault", VAULT_ROOT), (backup / "careervault-private", VAULT_PRIVATE)):
        if source.exists(): shutil.copytree(source, target, dirs_exist_ok=True)
    private = backup / "jobpilot-private"
    if private.exists():
        (db.DATA_DIR / "private").mkdir(parents=True, exist_ok=True)
        for item in private.iterdir():
            if item.name not in {"sync-config.json", "sync-passphrase"}:
                destination = db.DATA_DIR / "private" / item.name
                if item.is_dir(): shutil.copytree(item, destination, dirs_exist_ok=True)
                else: shutil.copy2(item, destination)
    db.init_db()
    config["rollback_backup"] = ""; _write_config(config)
    return status()
