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


def test_http_ready_rejects_html_fallback_for_missing_javascript(monkeypatch):
    response = Mock(status=200)
    response.headers.get_content_type.return_value = "text/html"
    context = Mock()
    context.__enter__ = Mock(return_value=response)
    context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(launcher.urllib.request, "urlopen", lambda *a, **kw: context)
    monkeypatch.setattr(launcher.time, "monotonic", Mock(side_effect=[0, 0, 2]))
    monkeypatch.setattr(launcher.time, "sleep", Mock())
    with pytest.raises(launcher.LaunchError, match="服务未就绪"):
        launcher.http_ready(
            launcher.URL + "src/App.vue", timeout=1, content_types=("text/javascript",)
        )


def test_broken_vue_module_is_not_treated_as_ready_homepage(monkeypatch):
    response = Mock(status=200)
    response.headers.get_content_type.return_value = "text/javascript"
    context = Mock()
    context.__enter__ = Mock(return_value=response)
    context.__exit__ = Mock(return_value=False)

    def urlopen(url, **kwargs):
        if url.endswith("App.vue"):
            raise launcher.urllib.error.HTTPError(url, 500, "Vue plugin missing", {}, None)
        return context

    monkeypatch.setattr(launcher.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(launcher.time, "monotonic", Mock(side_effect=[0, 0, 0, 0, 0, 0, 2]))
    monkeypatch.setattr(launcher.time, "sleep", Mock())
    with pytest.raises(launcher.LaunchError, match="App.vue"):
        launcher.frontend_ready(timeout=1)


def test_unhealthy_frontend_is_restarted_without_touching_backend_or_ssh(monkeypatch):
    monkeypatch.setattr(launcher.Path, "is_file", lambda path: True)
    backend, ssh, stale = {"pid": 1}, {"pid": 2}, {"pid": 3}
    managed, owned = [backend, ssh], []

    def reuse(kind, port, entries):
        entries.append(stale)
        return True

    monkeypatch.setattr(launcher, "reuse", reuse)
    monkeypatch.setattr(
        launcher, "frontend_ready", Mock(side_effect=[launcher.LaunchError("module broken"), None])
    )
    terminate, spawn = Mock(), Mock()
    monkeypatch.setattr(launcher, "terminate", terminate)
    monkeypatch.setattr(launcher, "spawn", spawn)
    replacement = {"pid": 4}
    monkeypatch.setattr(launcher, "wait_port", lambda *args: replacement)
    launcher.ensure_frontend(
        "node.exe", launcher.FRONTEND / "node_modules/vite/bin/vite.js", owned, managed
    )
    terminate.assert_called_once_with(stale)
    assert managed == [backend, ssh, replacement]
    command = spawn.call_args.args[1]
    assert command[command.index("--config") + 1] == str(launcher.FRONTEND / "vite.config.ts")


def test_healthy_frontend_is_reused_without_restart(monkeypatch):
    monkeypatch.setattr(launcher.Path, "is_file", lambda path: True)
    monkeypatch.setattr(launcher, "reuse", lambda *args: True)
    monkeypatch.setattr(launcher, "frontend_ready", lambda **kwargs: None)
    terminate, spawn = Mock(), Mock()
    monkeypatch.setattr(launcher, "terminate", terminate)
    monkeypatch.setattr(launcher, "spawn", spawn)
    launcher.ensure_frontend("node.exe", "vite.js", [], [])
    terminate.assert_not_called()
    spawn.assert_not_called()
