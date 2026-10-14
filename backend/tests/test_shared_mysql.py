"""Deployment guards must protect an existing shared development database."""

import hashlib
import hmac

import pytest

from scripts import shared_mysql


def test_import_refuses_existing_shared_tables(monkeypatch, tmp_path):
    monkeypatch.setattr(shared_mysql, "counts", lambda database: {"users": 5})
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        shared_mysql.import_sql(tmp_path / "snapshot.sql")


def test_restore_checks_backup_integrity_before_database_access(monkeypatch, tmp_path):
    monkeypatch.setattr(shared_mysql, "BACKUPS", tmp_path)
    backup = tmp_path / "snapshot.sql.gz.enc"
    backup.write_bytes(b"damaged encrypted backup")
    backup.with_suffix(".sha256").write_text("invalid-checksum")
    with pytest.raises(SystemExit, match="checksum mismatch"):
        shared_mysql.restore(backup)


def test_restore_refuses_existing_shared_database(monkeypatch, tmp_path):
    monkeypatch.setattr(shared_mysql, "BACKUPS", tmp_path)
    monkeypatch.setattr(shared_mysql, "ROOT", tmp_path)
    monkeypatch.setattr(shared_mysql, "counts", lambda: {"users": 5})
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/backup.key").write_bytes(b"test-backup-key")
    backup = tmp_path / "snapshot.sql.gz.enc"
    backup.write_bytes(b"encrypted backup")
    backup.with_suffix(".sha256").write_text(hashlib.sha256(backup.read_bytes()).hexdigest())
    backup.with_suffix(".hmac").write_text(
        hmac.new(b"test-backup-key", backup.read_bytes(), hashlib.sha256).hexdigest()
    )
    with pytest.raises(SystemExit, match="empty database"):
        shared_mysql.restore(backup)


def test_restore_rejects_unauthenticated_backup_before_database_access(monkeypatch, tmp_path):
    monkeypatch.setattr(shared_mysql, "BACKUPS", tmp_path)
    monkeypatch.setattr(shared_mysql, "ROOT", tmp_path)
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/backup.key").write_bytes(b"private-key")
    backup = tmp_path / "tampered.sql.gz.enc"
    backup.write_bytes(b"tampered ciphertext with a recomputed public checksum")
    backup.with_suffix(".sha256").write_text(hashlib.sha256(backup.read_bytes()).hexdigest())
    backup.with_suffix(".hmac").write_text("forged-signature")
    with pytest.raises(SystemExit, match="authentication failed"):
        shared_mysql.restore(backup)


def test_installer_refuses_root_before_creating_directories(monkeypatch):
    monkeypatch.setattr(shared_mysql.os, "getuid", lambda: 0, raising=False)
    with pytest.raises(SystemExit, match="group7"):
        shared_mysql.install()
