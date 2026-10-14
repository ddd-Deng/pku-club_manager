#!/usr/bin/env python3
"""A group-owned MySQL instance; no sudo, Docker, or system service changes."""

import argparse
import gzip
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.home() / "campus-club-mysql"
VERSION = "8.4.11"
ARCHIVE = f"mysql-{VERSION}-linux-glibc2.28-x86_64-minimal.tar.xz"
URL = f"https://cdn.mysql.com/Downloads/MySQL-8.4/{ARCHIVE}"
DATABASE = "campus_club"
BACKUPS = Path("/mnt/data/group7/campus-club-backups")


def write_private(path, value):
    path.write_text(value, encoding="utf-8")
    path.chmod(0o600)


def run(args, **kwargs):
    return subprocess.run(args, check=True, env=runtime_env(), **kwargs)


def runtime_env():
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(ROOT / "lib") + ":" + env.get("LD_LIBRARY_PATH", "")
    return env


def mysql(sql, database=None, output=False):
    args = [str(ROOT / "mysql/bin/mysql"), f"--defaults-file={ROOT / 'etc/root.cnf'}"]
    args += ["--batch", "--skip-column-names"]
    if database:
        args.append(database)
    result = run(args, input=sql.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode() if output else None


def status():
    return mysql(
        "SELECT VERSION(), @@port, @@innodb_buffer_pool_size, @@max_connections;", output=True
    )


def start(bootstrap=False):
    try:
        status()
        print("MySQL already running")
        return
    except subprocess.CalledProcessError:
        pass
    pidfile = ROOT / "run/mysql.pid"
    if pidfile.exists():
        pid = pidfile.read_text().strip()
        if pid.isdigit() and Path(f"/proc/{pid}").exists():
            raise SystemExit("A recorded process is still alive; inspect it before starting again")
    args = [str(ROOT / "mysql/bin/mysqld"), f"--defaults-file={ROOT / 'etc/my.cnf'}"]
    if bootstrap:
        args.append("--skip-networking")
    with (ROOT / "logs/launcher.log").open("ab") as log:
        subprocess.Popen(args, env=runtime_env(), stdout=log, stderr=log, start_new_session=True)
    for _ in range(60):
        time.sleep(1)
        try:
            status()
            print("MySQL ready")
            return
        except subprocess.CalledProcessError:
            pass
    raise SystemExit(f"MySQL did not become ready; inspect {ROOT / 'logs/mysql.log'}")


def stop():
    backup_pid = ROOT / "run/backup.pid"
    if backup_pid.exists():
        pid = backup_pid.read_text().strip()
        cmdline = Path(f"/proc/{pid}/cmdline") if pid.isdigit() else None
        if cmdline and cmdline.exists() and b"backup-loop" in cmdline.read_bytes():
            os.kill(int(pid), signal.SIGTERM)
        backup_pid.unlink()
    run(
        [str(ROOT / "mysql/bin/mysqladmin"), f"--defaults-file={ROOT / 'etc/root.cnf'}", "shutdown"]
    )
    for _ in range(30):
        if not (ROOT / "run/mysql.pid").exists():
            return
        time.sleep(1)
    raise SystemExit("MySQL has not finished shutting down")


def install():
    if os.getuid() == 0 or Path.home().name != "group7":
        raise SystemExit("Run this installer as the group7 Linux user")
    for name in ("openssl", "ldd", "tar"):
        if not shutil.which(name):
            raise SystemExit(f"Required tool missing: {name}")
    for name in ("etc", "run", "logs", "downloads", "lib", "incoming"):
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    ROOT.chmod(0o700)
    if (ROOT / "etc/provisioned.json").exists():
        start()
        return
    if (ROOT / "data").exists():
        raise SystemExit("Existing data directory: refusing to initialize or overwrite it")
    archive = ROOT / "downloads" / ARCHIVE
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    checksum = urllib.request.urlopen(URL + ".md5", timeout=30).read().decode()
    expected = re.search(r"\b[a-fA-F0-9]{32}\b", checksum)
    if not expected or hashlib.md5(archive.read_bytes()).hexdigest() != expected[0].lower():
        raise SystemExit("Official package checksum mismatch")
    target = ROOT / "mysql"
    if not target.exists():
        with tarfile.open(archive) as package:
            for item in package.getmembers():
                if item.name.startswith("/") or ".." in Path(item.name).parts:
                    raise SystemExit("Unexpected path in MySQL archive")
        target.mkdir()
        run(["tar", "-xJf", str(archive), "--strip-components=1", "-C", str(target)])
    missing = subprocess.run(
        ["ldd", str(target / "bin/mysqld")], env=runtime_env(), capture_output=True, text=True
    ).stdout
    if "libaio.so.1 => not found" in missing:
        if not shutil.which("apt-get") or not shutil.which("dpkg-deb"):
            raise SystemExit("libaio missing; ask the server maintainer for this runtime library")
        run(["apt-get", "download", "libaio1t64"], cwd=ROOT / "downloads")
        packages = list((ROOT / "downloads").glob("libaio1t64_*.deb"))
        if len(packages) != 1:
            raise SystemExit("Could not identify the downloaded libaio package")
        run(["dpkg-deb", "-x", str(packages[0]), str(ROOT / "libaio")])
        libraries = list((ROOT / "libaio").rglob("libaio.so.*"))
        actual = next((p for p in libraries if p.is_file() and not p.is_symlink()), None)
        if not actual:
            raise SystemExit("libaio runtime not found in extracted package")
        (ROOT / "lib/libaio.so.1").symlink_to(actual)
    for binary in ("mysqld", "mysql", "mysqldump", "mysqladmin"):
        check = subprocess.run(
            ["ldd", str(target / f"bin/{binary}")],
            env=runtime_env(),
            capture_output=True,
            text=True,
        )
        if "not found" in check.stdout:
            print(check.stdout)
            raise SystemExit("Missing runtime libraries; no system installation was attempted")
    port = None
    for candidate in (13307, 14307):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", candidate))
                port = candidate
                break
            except OSError:
                continue
    if port is None:
        raise SystemExit("Both project ports are occupied")
    write_private(
        ROOT / "etc/my.cnf",
        f"[mysqld]\nbasedir={target}\ndatadir={ROOT / 'data'}\n"
        f"socket={ROOT / 'run/mysql.sock'}\npid-file={ROOT / 'run/mysql.pid'}\n"
        f"log-error={ROOT / 'logs/mysql.log'}\nport={port}\nbind-address=127.0.0.1\n"
        "mysqlx=OFF\nskip-name-resolve=ON\ninnodb-dedicated-server=OFF\n"
        "innodb-buffer-pool-size=128M\ninnodb-redo-log-capacity=64M\nmax-connections=128\n"
        "table-open-cache=256\ncharacter-set-server=utf8mb4\n"
        "collation-server=utf8mb4_unicode_ci\nbinlog-expire-logs-seconds=172800\n",
    )
    write_private(ROOT / "etc/root.cnf", f"[client]\nuser=root\nsocket={ROOT / 'run/mysql.sock'}\n")
    run(
        [
            str(target / "bin/mysqld"),
            f"--defaults-file={ROOT / 'etc/my.cnf'}",
            "--initialize-insecure",
        ]
    )
    start(bootstrap=True)
    root_password, app_password, migration_password = [secrets.token_urlsafe(36) for _ in range(3)]
    mysql(f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{root_password}';")
    write_private(
        ROOT / "etc/root.cnf",
        f"[client]\nuser=root\npassword={root_password}\nsocket={ROOT / 'run/mysql.sock'}\n",
    )
    mysql("CREATE DATABASE campus_club CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    for name, password, privileges in (
        ("campus_app", app_password, "SELECT, INSERT, UPDATE, DELETE"),
        ("campus_migrate", migration_password, "ALL PRIVILEGES"),
    ):
        for host in ("127.0.0.1", "localhost"):
            mysql(f"CREATE USER '{name}'@'{host}' IDENTIFIED BY '{password}';")
            mysql(f"GRANT {privileges} ON campus_club.* TO '{name}'@'{host}';")
    for name, password in (("app", app_password), ("migration", migration_password)):
        write_private(
            ROOT / f"etc/{name}.env",
            f"DATABASE_URL=mysql+pymysql://campus_{'app' if name == 'app' else 'migrate'}:"
            f"{password}@127.0.0.1:{port}/campus_club?charset=utf8mb4\n",
        )
    write_private(ROOT / "etc/backup.key", secrets.token_urlsafe(48) + "\n")
    write_private(ROOT / "etc/provisioned.json", json.dumps({"version": VERSION, "port": port}))
    stop()
    start()
    print(f"Installed private group7 MySQL on 127.0.0.1:{port}; credentials were not printed")


def counts(database=DATABASE):
    tables = mysql(
        f"SELECT table_name FROM information_schema.tables WHERE table_schema='{database}' "
        "AND table_type='BASE TABLE' ORDER BY table_name;",
        output=True,
    ).splitlines()
    result = {}
    for table in tables:
        if not re.fullmatch(r"[A-Za-z0-9_]+", table):
            raise SystemExit("Unexpected table name")
        result[table] = int(
            mysql(f"SELECT COUNT(*) FROM `{table}`;", database, output=True).strip()
        )
    return result


def import_sql(path, database=DATABASE):
    if counts(database):
        raise SystemExit("Target database has tables; refusing to overwrite shared records")
    with path.open("rb") as file:
        run(
            [str(ROOT / "mysql/bin/mysql"), f"--defaults-file={ROOT / 'etc/root.cnf'}", database],
            stdin=file,
        )
    mysql("DELETE FROM login_sessions;", database)
    print(json.dumps(counts(database)))


def backup():
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    temp = ROOT / "incoming" / f"backup-{stamp}.sql.gz"
    output = BACKUPS / f"campus_club_{stamp}.sql.gz.enc"
    partial = output.with_suffix(".partial")
    args = [
        str(ROOT / "mysql/bin/mysqldump"),
        f"--defaults-file={ROOT / 'etc/root.cnf'}",
        "--single-transaction",
        "--set-gtid-purged=OFF",
        "--no-tablespaces",
        DATABASE,
    ]
    with subprocess.Popen(args, stdout=subprocess.PIPE, env=runtime_env()) as process:
        with gzip.open(temp, "wb") as file:
            shutil.copyfileobj(process.stdout, file)
        if process.wait() != 0:
            raise SystemExit("Database dump failed; no backup published")
    run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-pbkdf2",
            "-iter",
            "200000",
            "-salt",
            "-pass",
            f"file:{ROOT / 'etc/backup.key'}",
            "-in",
            str(temp),
            "-out",
            str(partial),
        ]
    )
    partial.replace(output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".sha256").write_text(digest + "\n")
    signature = hmac.new(
        (ROOT / "etc/backup.key").read_bytes(), output.read_bytes(), hashlib.sha256
    ).hexdigest()
    output.with_suffix(".hmac").write_text(signature + "\n")
    temp.unlink()
    for old in sorted(BACKUPS.glob("campus_club_*.sql.gz.enc"))[:-48]:
        if re.fullmatch(r"campus_club_\d{8}T\d{12}Z.sql.gz.enc", old.name):
            old.unlink()
            old.with_suffix(".sha256").unlink(missing_ok=True)
            old.with_suffix(".hmac").unlink(missing_ok=True)
    print(str(output))
    return output


def restore(path, test=False):
    if path.parent.resolve() != BACKUPS.resolve() or not path.name.endswith(".sql.gz.enc"):
        raise SystemExit("Use an encrypted project backup in the group7 backup directory")
    digest = path.with_suffix(".sha256").read_text().strip()
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise SystemExit("Backup checksum mismatch")
    signature = hmac.new(
        (ROOT / "etc/backup.key").read_bytes(), path.read_bytes(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, path.with_suffix(".hmac").read_text().strip()):
        raise SystemExit("Backup authentication failed; no database was touched")
    target = "campus_club_restore_group7" if test else DATABASE
    if test:
        mysql(f"CREATE DATABASE {target} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    elif counts():
        raise SystemExit("Restore requires an empty database; existing data was not touched")
    compressed = ROOT / "incoming/restore.sql.gz"
    plain = ROOT / "incoming/restore.sql"
    try:
        run(
            [
                "openssl",
                "enc",
                "-d",
                "-aes-256-cbc",
                "-pbkdf2",
                "-iter",
                "200000",
                "-pass",
                f"file:{ROOT / 'etc/backup.key'}",
                "-in",
                str(path),
                "-out",
                str(compressed),
            ]
        )
        with gzip.open(compressed, "rb") as source, plain.open("wb") as output:
            shutil.copyfileobj(source, output)
        import_sql(plain, target)
        if test:
            mysql(f"DROP DATABASE {target};")
    finally:
        compressed.unlink(missing_ok=True)
        plain.unlink(missing_ok=True)


def backup_loop():
    pidfile = ROOT / "run/backup.pid"
    pidfile.write_text(str(os.getpid()))
    while True:
        time.sleep(3600)
        try:
            backup()
        except Exception as exc:
            print(f"Backup failed: {type(exc).__name__}", flush=True)


def start_backup_loop():
    pidfile = ROOT / "run/backup.pid"
    if pidfile.exists():
        pid = pidfile.read_text().strip()
        cmdline = Path(f"/proc/{pid}/cmdline") if pid.isdigit() else None
        if cmdline and cmdline.exists() and b"backup-loop" in cmdline.read_bytes():
            print("Hourly backup already running")
            return
    with (ROOT / "logs/backup.log").open("ab") as log:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "backup-loop"],
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    print("Hourly encrypted backup started; it stops when the DSW instance stops")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=[
            "install",
            "start",
            "stop",
            "status",
            "counts",
            "import",
            "backup",
            "restore",
            "restore-test",
            "backup-loop",
            "start-backups",
        ],
    )
    parser.add_argument("path", nargs="?")
    args = parser.parse_args()
    if args.action in ("import", "restore", "restore-test") and not args.path:
        parser.error("this action requires a file path")
    if args.action == "install":
        install()
    elif args.action == "start":
        start()
        start_backup_loop()
    elif args.action == "stop":
        stop()
    elif args.action == "status":
        print(status())
    elif args.action == "counts":
        print(json.dumps(counts()))
    elif args.action == "import":
        path = Path(args.path).resolve()
        if path.parent != (ROOT / "incoming").resolve():
            raise SystemExit("Import requires a project snapshot in the private incoming directory")
        expected = Path(str(path) + ".sha256").read_text().strip()
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit("Import snapshot checksum mismatch")
        import_sql(path)
    elif args.action == "backup":
        backup()
    elif args.action.startswith("restore"):
        restore(Path(args.path), args.action == "restore-test")
    elif args.action == "backup-loop":
        backup_loop()
    else:
        start_backup_loop()


if __name__ == "__main__":
    main()
