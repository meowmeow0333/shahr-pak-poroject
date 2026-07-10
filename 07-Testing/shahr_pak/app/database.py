# -*- coding: utf-8 -*-
"""
database.py
لایه‌ی داده (Data Layer) - طبق سند مهندسی سیستم فاز ۳:
"پایگاه داده مرکزی: قلب تپنده سیستم برای ذخیره و بازیابی اطلاعات."

از SQLite به عنوان پایگاه داده‌ی سبک برای نمونه اولیه (Prototype) استفاده شده است.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "shahr_pak.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(reset: bool = False):
    """ایجاد جداول پایگاه داده. اگر reset=True باشد، پایگاه داده از نو ساخته می‌شود."""
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL,
        phone        TEXT,
        email        TEXT UNIQUE,
        password     TEXT NOT NULL,
        role         TEXT NOT NULL,
        extra_id     INTEGER,      -- citizen_id / operator_id
        address      TEXT,         -- فقط برای شهروند
        department   TEXT          -- فقط برای اپراتور
    );

    CREATE TABLE IF NOT EXISTS waste_bins (
        bin_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        location    TEXT NOT NULL,
        lat         REAL,
        lng         REAL,
        type        TEXT,
        status      TEXT NOT NULL DEFAULT 'normal',
        fill_level  INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS vehicles (
        vehicle_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number  TEXT NOT NULL,
        capacity      REAL,
        status        TEXT NOT NULL DEFAULT 'available',
        location      TEXT
    );

    CREATE TABLE IF NOT EXISTS reports (
        report_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        title         TEXT NOT NULL,
        description   TEXT,
        location      TEXT,
        lat           REAL,
        lng           REAL,
        status        TEXT NOT NULL,
        date          TEXT NOT NULL,
        image_url     TEXT,
        citizen_id    INTEGER,
        reviewed_by   INTEGER,
        bin_id        INTEGER,
        FOREIGN KEY (citizen_id) REFERENCES users(user_id),
        FOREIGN KEY (reviewed_by) REFERENCES users(user_id),
        FOREIGN KEY (bin_id) REFERENCES waste_bins(bin_id)
    );
    """)
    conn.commit()
    conn.close()


def seed_demo_data():
    """داده‌های نمونه برای نمایش سناریوها (طبق محدودیت پروژه: داده شبیه‌سازی‌شده)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return  # داده از قبل موجود است

    cur.executemany(
        "INSERT INTO users (name, phone, email, password, role, extra_id, address, department) "
        "VALUES (?,?,?,?,?,?,?,?)",
        [
            ("علی رضایی", "0912xxxxxxx", "ali@example.com", "1234", "citizen", 1, "تهران، خیابان آزادی", None),
            ("سارا احمدی", "0935xxxxxxx", "sara@example.com", "1234", "citizen", 2, "تهران، خیابان انقلاب", None),
            ("محمد قاسمی", "0910xxxxxxx", "op1@example.com", "1234", "operator", 1, None, "خدمات شهری - منطقه ۲"),
            ("رضا مدیریت", "0900xxxxxxx", "manager@example.com", "1234", "manager", None, None, None),
        ],
    )

    cur.executemany(
        "INSERT INTO waste_bins (location, lat, lng, type, status, fill_level) VALUES (?,?,?,?,?,?)",
        [
            ("خیابان آزادی، نبش کوچه ۵", 35.7000, 51.3300, "خانگی", "normal", 40),
            ("میدان انقلاب", 35.7010, 51.3900, "عمومی", "needs_pickup", 85),
            ("پارک ملت", 35.7700, 51.4100, "عمومی", "normal", 20),
        ],
    )

    cur.executemany(
        "INSERT INTO vehicles (plate_number, capacity, status, location) VALUES (?,?,?,?)",
        [
            ("۱۲ ایران ۳۴۵ب۶۷", 500.0, "available", "پایگاه منطقه ۲"),
            ("۴۵ ایران ۹۱۲د۲۲", 500.0, "on_route", "خیابان ولیعصر"),
        ],
    )

    conn.commit()
    conn.close()
