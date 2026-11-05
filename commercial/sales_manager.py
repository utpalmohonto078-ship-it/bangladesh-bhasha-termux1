#!/usr/bin/env python3
"""BANGLADESH BHASHA — Sales and Customer Management V1."""

import argparse
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_DB = BASE / "data" / "licenses.sqlite3"
PLANS = ("Professional", "Enterprise", "Institutional")
CURRENCIES = ("BDT", "USD")


def timestamp():
    return datetime.now(timezone.utc).isoformat()


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


def init_sales_db(db_path=DEFAULT_DB):
    with db_session(db_path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan TEXT NOT NULL UNIQUE,
            currency TEXT NOT NULL DEFAULT 'BDT',
            price TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sales_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL UNIQUE,
            customer_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'unpaid',
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)

        # Upgrade the existing License Engine customer table safely.
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(customers)").fetchall()
        }
        if "name" not in columns:
            db.execute("ALTER TABLE customers ADD COLUMN name TEXT")
        if "phone" not in columns:
            db.execute("ALTER TABLE customers ADD COLUMN phone TEXT")
        if "country" not in columns:
            db.execute("ALTER TABLE customers ADD COLUMN country TEXT")

        for plan in PLANS:
            db.execute(
                "INSERT OR IGNORE INTO products(plan, currency, price, updated_at) "
                "VALUES (?, 'BDT', NULL, ?)",
                (plan, timestamp()),
            )

    try:
        Path(db_path).chmod(0o600)
    except OSError:
        pass


def valid_email(email):
    email = email.strip()
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def add_customer(email, name, phone="", country="Bangladesh", db_path=DEFAULT_DB):
    init_sales_db(db_path)
    email = email.strip().lower()
    name = name.strip()
    if not valid_email(email) or not name:
        raise ValueError("A valid email and customer name are required")

    with db_session(db_path) as db:
        existing = db.execute(
            "SELECT id FROM customers WHERE email = ?", (email,)
        ).fetchone()

        if existing:
            db.execute(
                "UPDATE customers SET name=?, phone=?, country=? WHERE id=?",
                (name, phone.strip(), country.strip(), existing["id"]),
            )
            customer_id = existing["id"]
            action = "customer_updated"
        else:
            cur = db.execute(
                "INSERT INTO customers(email, created_at, name, phone, country) "
                "VALUES (?, ?, ?, ?, ?)",
                (email, timestamp(), name, phone.strip(), country.strip()),
            )
            customer_id = cur.lastrowid
            action = "customer_created"

        db.execute(
            "INSERT INTO audit_events(event, details, created_at) VALUES (?, ?, ?)",
            (action, f"customer_id={customer_id}, email={email}", timestamp()),
        )
    return customer_id


def list_customers(db_path=DEFAULT_DB):
    init_sales_db(db_path)
    with db_session(db_path) as db:
        return db.execute(
            "SELECT id, name, email, phone, country, created_at "
            "FROM customers ORDER BY id DESC"
        ).fetchall()


def set_price(plan, amount, currency="BDT", db_path=DEFAULT_DB):
    init_sales_db(db_path)
    if plan not in PLANS or currency not in CURRENCIES:
        raise ValueError("Invalid plan or currency")
    try:
        value = Decimal(str(amount))
    except InvalidOperation:
        raise ValueError("Invalid price")
    if not value.is_finite() or value <= 0 or value > Decimal("999999999"):
        raise ValueError("Price must be positive and within the allowed limit")

    normalized = format(value.quantize(Decimal("0.01")), "f")
    with db_session(db_path) as db:
        db.execute(
            "UPDATE products SET currency=?, price=?, updated_at=? WHERE plan=?",
            (currency, normalized, timestamp(), plan),
        )
        db.execute(
            "INSERT INTO audit_events(event, details, created_at) VALUES (?, ?, ?)",
            ("product_price_updated",
             f"plan={plan}, currency={currency}, price={normalized}",
             timestamp()),
        )
    return normalized


def list_products(db_path=DEFAULT_DB):
    init_sales_db(db_path)
    with db_session(db_path) as db:
        return db.execute(
            "SELECT plan, currency, price, updated_at FROM products ORDER BY id"
        ).fetchall()


def create_order(email, plan, db_path=DEFAULT_DB):
    init_sales_db(db_path)
    email = email.strip().lower()
    if not valid_email(email) or plan not in PLANS:
        raise ValueError("Valid customer email and plan are required")

    with db_session(db_path) as db:
        customer = db.execute(
            "SELECT id FROM customers WHERE email=?", (email,)
        ).fetchone()
        if customer is None:
            raise ValueError("Customer not found; register customer first")

        product = db.execute(
            "SELECT currency, price FROM products WHERE plan=?", (plan,)
        ).fetchone()
        if product is None or product["price"] is None:
            raise ValueError("Set the package price before creating an order")

        invoice = (
            "BBH-" + datetime.now(timezone.utc).strftime("%Y%m%d")
            + "-" + secrets.token_hex(4).upper()
        )
        cur = db.execute("""
            INSERT INTO sales_orders
            (invoice_no, customer_id, plan, currency, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'unpaid', ?)
        """, (
            invoice, customer["id"], plan, product["currency"],
            product["price"], timestamp(),
        ))
        order_id = cur.lastrowid

        db.execute(
            "INSERT INTO audit_events(event, details, created_at) VALUES (?, ?, ?)",
            ("sales_order_created",
             f"invoice={invoice}, customer={email}, plan={plan}",
             timestamp()),
        )

    return {"id": order_id, "invoice_no": invoice, "status": "unpaid"}


def list_orders(db_path=DEFAULT_DB):
    init_sales_db(db_path)
    with db_session(db_path) as db:
        return db.execute("""
            SELECT o.invoice_no, c.name, c.email, o.plan,
                   o.currency, o.amount, o.status, o.created_at
            FROM sales_orders o
            JOIN customers c ON c.id = o.customer_id
            ORDER BY o.id DESC
        """).fetchall()


def sales_report(db_path=DEFAULT_DB):
    init_sales_db(db_path)
    with db_session(db_path) as db:
        return db.execute("""
            SELECT currency, status, COUNT(*) AS order_count,
                   SUM(CAST(amount AS REAL)) AS total_amount
            FROM sales_orders
            GROUP BY currency, status
            ORDER BY currency, status
        """).fetchall()


def main():
    parser = argparse.ArgumentParser(description="BBH Sales Manager")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    customer = sub.add_parser("add-customer")
    customer.add_argument("--email", required=True)
    customer.add_argument("--name", required=True)
    customer.add_argument("--phone", default="")
    customer.add_argument("--country", default="Bangladesh")

    sub.add_parser("customers")

    price = sub.add_parser("set-price")
    price.add_argument("--plan", choices=PLANS, required=True)
    price.add_argument("--amount", required=True)
    price.add_argument("--currency", choices=CURRENCIES, default="BDT")

    sub.add_parser("products")

    order = sub.add_parser("create-order")
    order.add_argument("--email", required=True)
    order.add_argument("--plan", choices=PLANS, required=True)

    sub.add_parser("orders")
    sub.add_parser("report")

    args = parser.parse_args()

    if args.command == "init":
        init_sales_db(args.db)
        print("Sales database initialized.")
    elif args.command == "add-customer":
        cid = add_customer(
            args.email, args.name, args.phone, args.country, args.db
        )
        print(f"Customer saved. ID: {cid}")
    elif args.command == "customers":
        for row in list_customers(args.db):
            print(dict(row))
    elif args.command == "set-price":
        value = set_price(args.plan, args.amount, args.currency, args.db)
        print(f"Price saved: {args.plan} = {value} {args.currency}")
    elif args.command == "products":
        for row in list_products(args.db):
            print(dict(row))
    elif args.command == "create-order":
        print(create_order(args.email, args.plan, args.db))
    elif args.command == "orders":
        for row in list_orders(args.db):
            print(dict(row))
    elif args.command == "report":
        for row in sales_report(args.db):
            print(dict(row))


if __name__ == "__main__":
    main()
