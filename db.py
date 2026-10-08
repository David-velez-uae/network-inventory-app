"""Database access layer for the network inventory app."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "inventory.db"
SCHEMA_PATH = ROOT / "schema.sql"

CATEGORIES = ["Router", "Switch", "Firewall", "Access point", "Antenna", "Server"]
STATUSES = ["Active", "In storage", "Under repair", "Retired"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
TICKET_STATUSES = ["Open", "In progress", "Resolved"]

@contextmanager
def get_conn(db_path=DB_PATH):
    """Open a connection with foreign keys enabled; commit and close on exit."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DB_PATH):
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

def query_df(sql, params=(), db_path=DB_PATH):
    with get_conn(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)

def list_sites(db_path=DB_PATH):
    return query_df("SELECT * FROM sites ORDER BY name", db_path=db_path)

def list_equipment(db_path=DB_PATH):
    return query_df(
        """
        SELECT e.equipment_id, e.asset_tag, e.category, e.vendor, e.model,
               e.serial_number, s.name AS site, s.emirate, e.status, e.install_date
        FROM equipment AS e
        JOIN sites AS s ON s.site_id = e.site_id
        ORDER BY e.asset_tag
        """,
        db_path=db_path,
    )

def list_tickets(db_path=DB_PATH):
    return query_df(
        """
        SELECT t.ticket_id, e.asset_tag, e.category, s.name AS site,
               t.title, t.priority, t.status, t.opened_at, t.resolved_at
        FROM tickets AS t
        JOIN equipment AS e ON e.equipment_id = t.equipment_id
        JOIN sites AS s ON s.site_id = e.site_id
        ORDER BY t.opened_at DESC
        """,
        db_path=db_path,
    )

def add_equipment(asset_tag, category, vendor, model, serial_number,
                  site_id, status, install_date, db_path=DB_PATH):
    """Insert a piece of equipment. Raises sqlite3.IntegrityError on invalid data."""
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO equipment
                (asset_tag, category, vendor, model, serial_number,
                 site_id, status, install_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_tag, category, vendor, model, serial_number,
             site_id, status, install_date),
        )

def add_ticket(equipment_id, title, priority, db_path=DB_PATH):
    opened_at = datetime.now().isoformat(timespec="seconds")
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO tickets (equipment_id, title, priority, opened_at)
            VALUES (?, ?, ?, ?)
            """,
            (equipment_id, title, priority, opened_at),
        )

def update_ticket_status(ticket_id, status, db_path=DB_PATH):
    resolved_at = datetime.now().isoformat(timespec="seconds") if status == "Resolved" else None
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "UPDATE tickets SET status = ?, resolved_at = ? WHERE ticket_id = ?",
            (status, resolved_at, ticket_id),
        )
        return cur.rowcount

def kpis(db_path=DB_PATH):
    with get_conn(db_path) as conn:
        def count(sql):
            return conn.execute(sql).fetchone()[0]
        return {
            "total": count("SELECT COUNT(*) FROM equipment"),
            "active": count("SELECT COUNT(*) FROM equipment WHERE status = 'Active'"),
            "repair": count("SELECT COUNT(*) FROM equipment WHERE status = 'Under repair'"),
            "open_tickets": count("SELECT COUNT(*) FROM tickets WHERE status != 'Resolved'"),
        }