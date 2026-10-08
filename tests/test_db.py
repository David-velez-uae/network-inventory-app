import sqlite3
import pytest
import db

@pytest.fixture
def test_db(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    with db.get_conn(path) as conn:
        conn.execute(
            "INSERT INTO sites (name, emirate, site_type) "
            "VALUES ('Test Site', 'Dubai', 'Office')"
        )
    return path

def add_sample(path, tag="ASSET-1", serial="SN-1", category="Router"):
    db.add_equipment(
        tag, category, "Cisco", "R-4000", serial, 1, "Active", "2024-01-01",
        db_path=path,
    )

def test_add_and_list_equipment(test_db):
    add_sample(test_db)
    df = db.list_equipment(db_path=test_db)
    assert len(df) == 1
    assert df.loc[0, "asset_tag"] == "ASSET-1"

def test_duplicate_asset_tag_is_rejected(test_db):
    add_sample(test_db)
    with pytest.raises(sqlite3.IntegrityError):
        add_sample(test_db, serial="SN-2")

def test_invalid_category_is_rejected(test_db):
    with pytest.raises(sqlite3.IntegrityError):
        add_sample(test_db, category="Toaster")

def test_ticket_requires_existing_equipment(test_db):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_ticket(999, "Link down", "High", db_path=test_db)

def test_resolving_a_ticket_sets_resolution_time(test_db):
    add_sample(test_db)
    db.add_ticket(1, "Link down", "High", db_path=test_db)
    ticket_id = int(db.list_tickets(db_path=test_db).loc[0, "ticket_id"])
    db.update_ticket_status(ticket_id, "Resolved", db_path=test_db)
    ticket = db.list_tickets(db_path=test_db).loc[0]
    assert ticket["status"] == "Resolved"
    assert isinstance(ticket["resolved_at"], str)