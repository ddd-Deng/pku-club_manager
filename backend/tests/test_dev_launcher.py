"""Launcher process safety checks; never starts or kills real processes."""

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

spec = importlib.util.spec_from_file_location(
    "dev_launcher", Path(__file__).resolve().parents[2] / "scripts/dev.py"
)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def backend_process(created="original"):
    return {
        "pid": 123,
        "parent": 100,
        "created": created,
        "name": "python.exe",
        "command": f'"{launcher.BACKEND}\\.venv\\Scripts\\python.exe" '
        "-m uvicorn app.main:app --port 8080",
    }


def test_process_identity_rejects_other_checkout_and_empty_command():
    process = backend_process()
    assert launcher.belongs_to_project("backend", process, 8080)
    process["command"] = process["command"].replace("backend\\", "backend-other\\")
    assert not launcher.belongs_to_project("backend", process, 8080)
    process["command"] = None
    assert not launcher.belongs_to_project("backend", process, 8080)
    assert not launcher.belongs_to_project("backend", None, 8080)


def test_ssh_identity_requires_this_server_and_forward():
    process = {
        "name": "ssh.exe",
        "command": f"ssh -N -L 127.0.0.1:13307:127.0.0.1:13307 -p 1021 {launcher.SERVER}",
    }
    assert launcher.belongs_to_project("ssh", process, 13307)
    assert not launcher.belongs_to_project("ssh", process, 14307)
    process["command"] = process["command"].replace(launcher.SERVER, "other@example.com")
    assert not launcher.belongs_to_project("ssh", process, 13307)


@pytest.mark.parametrize("current", [None, backend_process("reused-pid")])
def test_terminate_does_not_kill_reused_pid(monkeypatch, current):
    monkeypatch.setattr(launcher, "process_info", lambda pid: current)
    run = Mock()
    monkeypatch.setattr(launcher.subprocess, "run", run)
    launcher.terminate({"kind": "backend", "pid": 123, "created": "original", "port": 8080})
    run.assert_not_called()


def test_port_conflict_does_not_stop_other_process(monkeypatch):
    monkeypatch.setattr(launcher, "listener", lambda port: {"name": "other.exe", "command": ""})
    terminate = Mock()
    monkeypatch.setattr(launcher, "terminate", terminate)
    managed = []
    with pytest.raises(launcher.LaunchError, match="被其他进程占用"):
        launcher.reuse("backend", 8080, managed)
    assert not managed
    terminate.assert_not_called()


def test_failed_start_cleans_only_new_processes(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", lambda name: "node.exe")
    monkeypatch.setattr(launcher.Path, "is_file", lambda path: True)
    database = Mock(host="127.0.0.1", port=13307)
    engine = Mock()
    engine.connect.side_effect = OSError("database unreachable")
    monkeypatch.setattr(
        launcher, "check_database", lambda: (Mock(), database, lambda *a, **kw: engine, Mock())
    )
    reused = {"pid": 10}
    spawned = {"pid": 11}

    def ensure_ssh(port, owned, managed):
        managed.append(reused)
        owned.append(spawned)

    monkeypatch.setattr(launcher, "ensure_ssh", ensure_ssh)
    terminate = Mock()
    monkeypatch.setattr(launcher, "terminate", terminate)
    with pytest.raises(launcher.LaunchError, match="数据库不可用"):
        launcher.start(no_browser=True)
    terminate.assert_called_once_with(spawned)
    engine.dispose.assert_called_once()
