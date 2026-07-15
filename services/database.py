import sqlite3
import hashlib
import os
import json
from contextlib import contextmanager
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password_hash TEXT,
    password_salt TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simulation_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    save_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    tick INTEGER NOT NULL,
    season TEXT NOT NULL,
    state_json TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS simulation_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    season TEXT NOT NULL,
    plants INTEGER NOT NULL,
    berry_bushes INTEGER NOT NULL,
    herbivores INTEGER NOT NULL,
    foxes INTEGER NOT NULL,
    water_sources INTEGER NOT NULL,
    shelters INTEGER NOT NULL,
    avg_herbivore_energy REAL,
    avg_herbivore_thirst REAL,
    avg_fox_energy REAL,
    avg_fox_hunger REAL,
    avg_fox_thirst REAL,
    danger_count INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (save_id) REFERENCES simulation_saves(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER PRIMARY KEY,
    settings_json TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "ecobalance.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _hash_password(password, salt=None):
        if salt is None:
            salt = os.urandom(16).hex()
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()
        return digest, salt

    def create_user(self, username, email="", password=""):
        password_hash, salt = (None, None)
        if password:
            password_hash, salt = self._hash_password(password)
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO users (username, email, password_hash, password_salt, created_at) VALUES (?, ?, ?, ?, ?)",
                    (username, email, password_hash, salt, datetime.now().isoformat()),
                )
                return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"A profile named '{username}' already exists.")

    def verify_user(self, username, password):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if row is None:
                return None
            if row["password_hash"]:
                digest, _ = self._hash_password(password, row["password_salt"])
                if digest != row["password_hash"]:
                    return None
            return dict(row)

    def list_users(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT id, username, email, created_at FROM users ORDER BY username").fetchall()
            return [dict(r) for r in rows]

    def delete_user(self, user_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def save_full_state(self, user_id, save_name, engine_state):
        now = datetime.now().isoformat()
        state_json = json.dumps(engine_state)
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM simulation_saves WHERE user_id = ? AND save_name = ?", (user_id, save_name)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE simulation_saves SET updated_at = ?, tick = ?, season = ?, state_json = ? WHERE id = ?",
                    (now, engine_state["tick"], engine_state["season"], state_json, existing["id"]),
                )
                return existing["id"]
            cur = conn.execute(
                "INSERT INTO simulation_saves (user_id, save_name, created_at, updated_at, tick, season, state_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, save_name, now, now, engine_state["tick"], engine_state["season"], state_json),
            )
            return cur.lastrowid

    def load_full_state(self, save_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM simulation_saves WHERE id = ?", (save_id,)).fetchone()
            if row is None:
                return None
            data = dict(row)
            data["state"] = json.loads(data["state_json"])
            return data

    def list_saves(self, user_id):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, save_name, created_at, updated_at, tick, season FROM simulation_saves WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def rename_save(self, save_id, new_name):
        with self._connect() as conn:
            conn.execute("UPDATE simulation_saves SET save_name = ? WHERE id = ?", (new_name, save_id))

    def delete_save(self, save_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM simulation_saves WHERE id = ?", (save_id,))

    def has_any_save(self, user_id):
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM simulation_saves WHERE user_id = ?", (user_id,)).fetchone()
            return row["c"] > 0

    def save_snapshot(self, save_id, stats):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO simulation_snapshots (
                    save_id, tick, season, plants, berry_bushes, herbivores, foxes,
                    water_sources, shelters, avg_herbivore_energy, avg_herbivore_thirst,
                    avg_fox_energy, avg_fox_hunger, avg_fox_thirst, danger_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    save_id, stats["tick"], stats["season"], stats["plants"], stats["berry_bushes"],
                    stats["herbivores"], stats["foxes"], stats["water_sources"], stats["shelters"],
                    stats["avg_herbivore_energy"], stats["avg_herbivore_thirst"], stats["avg_fox_energy"],
                    stats["avg_fox_hunger"], stats["avg_fox_thirst"], stats["danger_count"],
                    datetime.now().isoformat(),
                ),
            )

    def list_snapshots(self, save_id):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM simulation_snapshots WHERE save_id = ? ORDER BY tick", (save_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_settings(self, user_id, settings_dict):
        with self._connect() as conn:
            existing = conn.execute("SELECT user_id FROM settings WHERE user_id = ?", (user_id,)).fetchone()
            payload = json.dumps(settings_dict)
            if existing:
                conn.execute("UPDATE settings SET settings_json = ? WHERE user_id = ?", (payload, user_id))
            else:
                conn.execute("INSERT INTO settings (user_id, settings_json) VALUES (?, ?)", (user_id, payload))

    def load_settings(self, user_id):
        with self._connect() as conn:
            row = conn.execute("SELECT settings_json FROM settings WHERE user_id = ?", (user_id,)).fetchone()
            return json.loads(row["settings_json"]) if row else {}
