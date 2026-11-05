#!/usr/bin/env python3
"""BANGLADESH BHASHA — local license management prototype."""

import argparse
import hashlib
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_DB = BASE / "data" / "licenses.sqlite3"
PLANS = ("Professional", "Enterprise", "Institutional")


def now_utc():
    return datetime.now(timezone.utc)


def connect(db_path=DEFAULT_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


@contextmanager
def db_session(db_path=DEFAULT_DB):
    db = connect(db_path)
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db(db_path=DEFAULT_DB):
    with db_session(db_path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            key_hash TEXT NOT NULL UNIQUE,
            plan TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
    try:
        Path(db_path).chmod(0o600)
    except OSError:
        pass


def key_digest(key):
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def issue_license(email, plan="Professional", days=365, db_path=DEFAULT_DB):
    if plan not in PLANS:
        raise ValueError("Unknown plan")
    if not email.strip() or days < 1:
        raise ValueError("Valid email and positive days are required")

    init_db(db_path)
    issued = now_utc()
    expires = issued + timedelta(days=days)
    key = f"BBH-{plan[:3].upper()}-{secrets.token_urlsafe(32)}"

    with db_session(db_path) as db:
        db.execute(
            "INSERT OR IGNORE INTO customers(email, created_at) VALUES (?, ?)",
            (email.strip().lower(), issued.isoformat()),
        )
        customer = db.execute(
            "SELECT id FROM customers WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

        db.execute("""
            INSERT INTO licenses
            (customer_id, key_hash, plan, issued_at, expires_at, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        """, (
            customer["id"], key_digest(key), plan,
            issued.isoformat(), expires.isoformat(),
        ))
        db.execute(
            "INSERT INTO audit_events(event, details, created_at) VALUES (?, ?, ?)",
            ("license_issued", f"email={email.strip().lower()}, plan={plan}",
             issued.isoformat()),
        )

    return {"key": key, "plan": plan, "expires_at": expires.isoformat()}


def verify_license(key, db_path=DEFAULT_DB):
    init_db(db_path)
    with db_session(db_path) as db:
        row = db.execute(
            "SELECT plan, expires_at, status FROM licenses WHERE key_hash = ?",
            (key_digest(key),),
        ).fetchone()

    if row is None:
        return {"valid": False, "reason": "invalid_key"}
    if row["status"] != "active":
        return {"valid": False, "reason": row["status"]}
    if datetime.fromisoformat(row["expires_at"]) <= now_utc():
        return {"valid": False, "reason": "expired"}

    return {
        "valid": True,
        "reason": "active",
        "plan": row["plan"],
        "expires_at": row["expires_at"],
    }


def revoke_license(key, db_path=DEFAULT_DB):
    init_db(db_path)
    with db_session(db_path) as db:
        cur = db.execute(
            "UPDATE licenses SET status = 'revoked' "
            "WHERE key_hash = ? AND status = 'active'",
            (key_digest(key),),
        )
        if cur.rowcount:
            db.execute(
                "INSERT INTO audit_events(event, details, created_at) "
                "VALUES (?, ?, ?)",
                ("license_revoked", "license revoked by local administrator",
                 now_utc().isoformat()),
            )
        return cur.rowcount == 1


def list_licenses(db_path=DEFAULT_DB):
    init_db(db_path)
    with db_session(db_path) as db:
        return db.execute("""
            SELECT c.email, l.plan, l.issued_at, l.expires_at, l.status
            FROM licenses l
            JOIN customers c ON c.id = l.customer_id
            ORDER BY l.id DESC
        """).fetchall()


def main():
    parser = argparse.ArgumentParser(description="BBH License Engine")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    issue = sub.add_parser("issue")
    issue.add_argument("--email", required=True)
    issue.add_argument("--plan", choices=PLANS, default="Professional")
    issue.add_argument("--days", type=int, default=365)

    verify = sub.add_parser("verify")
    verify.add_argument("--key", required=True)

    revoke = sub.add_parser("revoke")
    revoke.add_argument("--key", required=True)

    sub.add_parser("list")
    args = parser.parse_args()

    if args.command == "init":
        init_db(args.db)
        print("Database initialized.")
    elif args.command == "issue":
        result = issue_license(args.email, args.plan, args.days, args.db)
        print("LICENSE CREATED — save this key securely; it is shown only once.")
        print("KEY:", result["key"])
        print("PLAN:", result["plan"])
        print("EXPIRES:", result["expires_at"])
    elif args.command == "verify":
        print(verify_license(args.key, args.db))
    elif args.command == "revoke":
        print("Revoked." if revoke_license(args.key, args.db)
              else "No active matching license.")
    elif args.command == "list":
        for row in list_licenses(args.db):
            print(dict(row))


if __name__ == "__main__":
    main()
