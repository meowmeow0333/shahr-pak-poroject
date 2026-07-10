# -*- coding: utf-8 -*-
"""
database.py
layeye dade (Data Layer) - tbgh sanad mhndsy systm faz 3:
"paygah dade markazi: ghalb tapande system baraye zakhire va bazyabi etelaat."

az SQLite be onvan paygah dade sabok baraye nemoone avaliye (Prototype) estefade shode ast.
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
    """ijad jadavel paygah dade. agar reset=True bashad, paygah dade az no sakhte mishavad."""
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
        address      TEXT,         -- faghat baraye shahrvand
        department   TEXT          -- faghat baraye operator
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
    """dadehaye nemoone baraye namayesh scenarioha (tebghe mahdoodiyat projeh: dade shabihsazi-shode)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return  # dade az ghabl mojood ast

    cur.executemany(
        "INSERT INTO users (name, phone, email, password, role, extra_id, address, department) "
        "VALUES (?,?,?,?,?,?,?,?)",
        [
            ("Ali Rezaei", "0912xxxxxxx", "ali@example.com", "1234", "citizen", 1, "Tehran, khiaban Azadi", None),
            ("Sara Ahmadi", "0935xxxxxxx", "sara@example.com", "1234", "citizen", 2, "Tehran, khiaban Enghelab", None),
            ("Mohammad Ghasemi", "0910xxxxxxx", "op1@example.com", "1234", "operator", 1, None, "Khadamat shahri - mantaghe 2"),
            ("Reza Modiriyat", "0900xxxxxxx", "manager@example.com", "1234", "manager", None, None, None),
        ],
    )

    cur.executemany(
        "INSERT INTO waste_bins (location, lat, lng, type, status, fill_level) VALUES (?,?,?,?,?,?)",
        [
            ("khiaban Azadi, nabsh kooche 5", 35.7000, 51.3300, "khanegi", "normal", 40),
            ("meydan Enghelab", 35.7010, 51.3900, "omoomi", "needs_pickup", 85),
            ("park Mellat", 35.7700, 51.4100, "omoomi", "normal", 20),
        ],
    )

    cur.executemany(
        "INSERT INTO vehicles (plate_number, capacity, status, location) VALUES (?,?,?,?)",
        [
            ("12 Iran 345b67", 500.0, "available", "paygah mantaghe 2"),
            ("45 Iran 912d22", 500.0, "on_route", "khiaban Valiasr"),
        ],
    )

    conn.commit()
    conn.close()
