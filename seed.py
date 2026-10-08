"""Create the database and fill it with synthetic demo data."""
import random
from datetime import date, datetime, timedelta
import db

random.seed(7)

SITES = [
    ("Dubai Data Center 1", "Dubai", "Data center"),
    ("Dubai Marina Cell Site", "Dubai", "Cell site"),
    ("Deira Exchange", "Dubai", "Exchange"),
    ("Jebel Ali Cell Site", "Dubai", "Cell site"),
    ("Abu Dhabi Data Center", "Abu Dhabi", "Data center"),
    ("Yas Island Cell Site", "Abu Dhabi", "Cell site"),
    ("Sharjah Exchange", "Sharjah", "Exchange"),
    ("Sharjah Office", "Sharjah", "Office"),
]

VENDORS = ["Cisco", "Huawei", "Ericsson", "Nokia", "Juniper", "Fortinet"]
MODELS = {
    "Router": ["R-4000", "R-5000"],
    "Switch": ["S-2400", "S-3600"],
    "Firewall": ["FW-100", "FW-300"],
    "Access point": ["AP-20", "AP-30"],
    "Antenna": ["AN-5G-64", "AN-4G-32"],
    "Server": ["SRV-1U", "SRV-2U"],
}
ISSUES = [
    "Link down", "High CPU usage", "Firmware update required",
    "Hardware fault", "Packet loss detected", "Fan failure",
]

N_EQUIPMENT = 60
N_TICKETS = 18

def main():
    db.DB_PATH.unlink(missing_ok=True)
    db.init_db()

    with db.get_conn() as conn:
        conn.executemany(
            "INSERT INTO sites (name, emirate, site_type) VALUES (?, ?, ?)", SITES
        )

        for i in range(1, N_EQUIPMENT + 1):
            category = random.choice(db.CATEGORIES)
            install = date(2021, 1, 1) + timedelta(days=random.randint(0, 1700))
            conn.execute(
                """
                INSERT INTO equipment
                    (asset_tag, category, vendor, model, serial_number,
                     site_id, status, install_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"ASSET-{i:04d}",
                    category,
                    random.choice(VENDORS),
                    random.choice(MODELS[category]),
                    f"SN-{i:05d}-{random.randint(1000, 9999)}",
                    random.randint(1, len(SITES)),
                    random.choices(db.STATUSES, weights=[70, 10, 12, 8])[0],
                    install.isoformat(),
                ),
            )

        for _ in range(N_TICKETS):
            opened = datetime(2026, 9, 1) + timedelta(hours=random.randint(0, 24 * 35))
            status = random.choice(db.TICKET_STATUSES)
            resolved = None
            if status == "Resolved":
                resolved = (opened + timedelta(hours=random.randint(1, 72))).isoformat(
                    timespec="seconds"
                )

            conn.execute(
                """
                INSERT INTO tickets
                    (equipment_id, title, priority, status, opened_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    random.randint(1, N_EQUIPMENT),
                    random.choice(ISSUES),
                    random.choice(db.PRIORITIES),
                    status,
                    opened.isoformat(timespec="seconds"),
                    resolved,
                ),
            )

    with db.get_conn() as conn:
        for table in ("sites", "equipment", "tickets"):
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {n} rows")

if __name__ == "__main__":
    main()