"""Network inventory app (Streamlit UI)."""
import sqlite3
from datetime import date
import streamlit as st
import db

st.set_page_config(page_title="Network Inventory", page_icon="📡", layout="wide")
db.init_db()

st.sidebar.title("📡 Network Inventory")
page = st.sidebar.radio("Navigation", ["Dashboard", "Equipment", "Tickets"])
st.sidebar.caption("Synthetic demo data. Run `python seed.py` to reset it.")

if page == "Dashboard":
    st.title("Dashboard")
    k = db.kpis()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total equipment", k["total"])
    c2.metric("Active", k["active"])
    c3.metric("Under repair", k["repair"])
    c4.metric("Open tickets", k["open_tickets"])

    equipment = db.list_equipment()
    left, right = st.columns(2)
    left.subheader("Equipment by category")
    left.bar_chart(equipment["category"].value_counts())

    right.subheader("Equipment by status")
    right.bar_chart(equipment["status"].value_counts())

    st.subheader("Open tickets by priority")
    tickets = db.list_tickets()
    open_tickets = tickets[tickets["status"] != "Resolved"]
    st.bar_chart(open_tickets["priority"].value_counts())

elif page == "Equipment":
    st.title("Equipment")
    with st.expander("➕ Add equipment"):
        sites = db.list_sites()
        site_ids = dict(zip(sites["name"], sites["site_id"]))
        with st.form("add_equipment", clear_on_submit=True):
            a, b = st.columns(2)
            asset_tag = a.text_input("Asset tag (e.g. ASSET-0100)")
            serial = b.text_input("Serial number")
            category = a.selectbox("Category", db.CATEGORIES)
            vendor = b.text_input("Vendor")
            model = a.text_input("Model")
            site = b.selectbox("Site", list(site_ids))
            status = a.selectbox("Status", db.STATUSES)
            installed = b.date_input("Install date", value=date.today())
            submitted = st.form_submit_button("Save")

        if submitted:
            if not all([asset_tag.strip(), serial.strip(), vendor.strip(), model.strip()]):
                st.error("Please fill in all fields.")
            else:
                try:
                    db.add_equipment(
                        asset_tag.strip(), category, vendor.strip(), model.strip(),
                        serial.strip(), int(site_ids[site]), status, installed.isoformat(),
                    )
                    st.success(f"{asset_tag.strip()} added.")
                except sqlite3.IntegrityError:
                    st.error("That asset tag or serial number already exists.")

    equipment = db.list_equipment()
    f1, f2, f3 = st.columns(3)
    categories = f1.multiselect("Category", db.CATEGORIES)
    statuses = f2.multiselect("Status", db.STATUSES)
    emirates = f3.multiselect("Emirate", sorted(equipment["emirate"].unique()))

    filtered = equipment
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if statuses:
        filtered = filtered[filtered["status"].isin(statuses)]
    if emirates:
        filtered = filtered[filtered["emirate"].isin(emirates)]

    st.caption(f"{len(filtered)} of {len(equipment)} items")
    st.dataframe(filtered.drop(columns="equipment_id"), hide_index=True)

else:
    st.title("Tickets")
    equipment = db.list_equipment()
    tag_to_id = dict(zip(equipment["asset_tag"], equipment["equipment_id"]))

    with st.expander("➕ Open a ticket"):
        with st.form("new_ticket", clear_on_submit=True):
            tag = st.selectbox("Equipment", list(tag_to_id))
            title = st.text_input("Issue")
            priority = st.selectbox("Priority", db.PRIORITIES, index=1)
            opened = st.form_submit_button("Open ticket")

        if opened:
            if not title.strip():
                st.error("Please describe the issue.")
            else:
                db.add_ticket(int(tag_to_id[tag]), title.strip(), priority)
                st.success("Ticket opened.")

    with st.expander("✏️ Update ticket status"):
        current = db.list_tickets()
        with st.form("update_ticket"):
            ticket_id = st.selectbox("Ticket", current["ticket_id"].tolist())
            new_status = st.selectbox("New status", db.TICKET_STATUSES)
            updated = st.form_submit_button("Update")

        if updated:
            db.update_ticket_status(int(ticket_id), new_status)
            st.success(f"Ticket {ticket_id} set to {new_status}.")

    tickets = db.list_tickets()
    shown = st.multiselect(
        "Show statuses", db.TICKET_STATUSES, default=["Open", "In progress"]
    )
    view = tickets[tickets["status"].isin(shown)] if shown else tickets
    st.caption(f"{len(view)} of {len(tickets)} tickets")
    st.dataframe(view, hide_index=True)