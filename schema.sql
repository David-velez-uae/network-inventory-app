CREATE TABLE IF NOT EXISTS sites (
    site_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    emirate   TEXT NOT NULL,
    site_type TEXT NOT NULL
        CHECK (site_type IN ('Data center', 'Cell site', 'Exchange', 'Office'))
);

CREATE TABLE IF NOT EXISTS equipment (
    equipment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_tag     TEXT NOT NULL UNIQUE,
    category      TEXT NOT NULL
        CHECK (category IN ('Router', 'Switch', 'Firewall', 'Access point', 'Antenna', 'Server')),
    vendor        TEXT NOT NULL,
    model         TEXT NOT NULL,
    serial_number TEXT NOT NULL UNIQUE,
    site_id       INTEGER NOT NULL REFERENCES sites(site_id),
    status        TEXT NOT NULL DEFAULT 'Active'
        CHECK (status IN ('Active', 'In storage', 'Under repair', 'Retired')),
    install_date  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(equipment_id),
    title        TEXT NOT NULL,
    priority     TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    status       TEXT NOT NULL DEFAULT 'Open'
        CHECK (status IN ('Open', 'In progress', 'Resolved')),
    opened_at    TEXT NOT NULL,
    resolved_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_equipment_site ON equipment(site_id);
CREATE INDEX IF NOT EXISTS idx_tickets_equipment ON tickets(equipment_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);