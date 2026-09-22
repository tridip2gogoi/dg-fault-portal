import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="DG Fault Portal", layout="wide")

# Upload ফোল্ডাৰ তৈয়াৰ কৰা
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ১. User Accounts
USERS = {
    "tech1": {"password": "123", "role": "Utility Technician", "name": "Utility Tech - Rahul"},
    "manager1": {"password": "123", "role": "Service Manager", "name": "Service Manager - Barman"},
    "docket1": {"password": "123", "role": "Docket Team", "name": "Docket Desk"},
    "eng1": {"password": "123", "role": "Service Engineer", "name": "Field Eng - Biren"}
}

# ২. Database Setup
conn = sqlite3.connect("dg_faults.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS faults (
    id TEXT PRIMARY KEY,
    site TEXT,
    dg TEXT,
    desc TEXT,
    status TEXT,
    docket TEXT,
    rectification TEXT,
    fault_photo TEXT,
    rect_photo TEXT,
    created_at TIMESTAMP,
    closed_at TIMESTAMP
)
""")
conn.commit()

# পুৰণি ডাটাবেচ আপডেট (যদি কলম দুটা নাথাকে যোগ কৰিবলৈ)
try:
    cursor.execute("ALTER TABLE faults ADD COLUMN fault_photo TEXT")
    cursor.execute("ALTER TABLE faults ADD COLUMN rect_photo TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

# ৩০ দিন পুৰণি CLOSED records চফা কৰা
thirty_days_ago = datetime.now() - timedelta(days=30)
cursor.execute("DELETE FROM faults WHERE status = 'CLOSED' AND closed_at < ?", (thirty_days_ago,))
conn.commit()

# ফটো Save কৰাৰ function
def save_uploaded_file(uploaded_file, ticket_id, prefix):
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1]
        filename = f"{prefix}_{ticket_id}_{int(datetime.now().timestamp())}.{file_ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.get_buffer())
        return filepath
    return ""

# ৩. Session State Init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

# ৪. LOGIN SCREEN
if not st.session_state.logged_in:
    st.title("⚡ DG Fault Management Portal")
    st.subheader("Login কৰক")

    col1, _ = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_info = USERS[username]
                st.rerun()
            else:
                st.error("ভুল Username বা Password!")
else:
    user = st.session_state.user_info
    role = user["role"]

    # Top Bar
    col_t1, col_t2 = st.columns([4, 1])
    with col_t1:
        st.title("⚡ DG Fault Management Portal")
        st.caption(f"Logged in as: **{user['name']}** | Role: **{role}**")
    with col_t2:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

    st.divider()

    # ১. Utility Technician Form (ফটো আপলোডৰ সৈতে)
    if role == "Utility Technician":
        st.subheader("নতুন Fault Log কৰক")
        with st.form("new_fault_form"):
            site = st.text_input("Site ID (যেনে: GUW-10)")
            dg = st.text_input("DG Model / Serial")
            desc = st.text_area("Fault Description")
            # ম'বাইলত এইটো টিপিলে পোনপটীয়াকৈ Camera বা Files খোল খাব
            fault_img = st.file_uploader("Fault ৰ ফটো আপলোড কৰক (কেমেৰা/গেলাৰী)", type=["jpg", "png", "jpeg"])
            submit = st.form_submit_button("Request পঠিয়াওক")

            if submit and site and dg:
                cursor.execute("SELECT COUNT(*) FROM faults")
                count = cursor.fetchone()[0]
                new_id = f"TKT-{count + 101}"
                
                photo_path = save_uploaded_file(fault_img, new_id, "fault")

                cursor.execute("""
                    INSERT INTO faults (id, site, dg, desc, status, docket, rectification, fault_photo, rect_photo, created_at, closed_at)
                    VALUES (?, ?, ?, ?, 'PENDING_SM', '', '', ?, '', ?, NULL)
                """, (new_id, site, dg, desc, photo_path, datetime.now()))
                conn.commit()
                st.success(f"Fault {new_id} সফলভাৱে পঠিওৱা হ'ল!")
                st.rerun()

        st.divider()

    st.subheader("Fault Requests & Status")

    # Fetch Active Records
    cursor.execute("""
        SELECT id, site, dg, desc, status, docket, rectification, fault_photo, rect_photo, closed_at 
        FROM faults ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        st.info("কোনো Fault ৰেকৰ্ড পোৱা নগ'ল।")

    for r in rows:
        t_id, t_site, t_dg, t_desc, t_status, t_docket, t_rect, t_fphoto, t_rphoto, t_closed = r

        with st.expander(f"{t_id} | {t_site} - {t_dg} | Status: [{t_status}]", expanded=(t_status != 'CLOSED')):
            st.write(f"**সমস্যা:** {t_desc}")
            
            # Fault Photo প্ৰদৰ্শন
            if t_fphoto and os.path.exists(t_fphoto):
                st.image(t_fphoto, caption="Reported Fault Photo", width=300)

            if t_docket:
                st.info(f"Docket No: {t_docket}")

            if t_rect:
                st.warning(f"Rectification Details: {t_rect}")

            # Rectification Photo প্ৰদৰ্শন
            if t_rphoto and os.path.exists(t_rphoto):
                st.image(t_rphoto, caption="Rectification Work Photo", width=300)

            # ২. Service Manager Actions
            if role == "Service Manager" and t_status == "PENDING_SM":
                c1, c2 = st.columns(2)
                if c1.button("Approve", key=f"sm_app_{t_id}"):
                    cursor.execute("UPDATE faults SET status = 'PENDING_DOCKET' WHERE id = ?", (t_id,))
                    conn.commit()
                    st.rerun()
                if c2.button("Reject", key=f"sm_rej_{t_id}"):
                    cursor.execute("UPDATE faults SET status = 'REJECTED' WHERE id = ?", (t_id,))
                    conn.commit()
                    st.rerun()

            # ৩. Docket Team Actions
            elif role == "Docket Team" and t_status == "PENDING_DOCKET":
                d_no = st.text_input("Enter Docket No", key=f"doc_in_{t_id}")
                if st.button("Submit Docket", key=f"doc_btn_{t_id}"):
                    if d_no:
                        cursor.execute("UPDATE faults SET docket = ?, status = 'ASSIGNED_ENG' WHERE id = ?", (d_no, t_id))
                        conn.commit()
                        st.rerun()

            # ৪. Service Engineer Actions (ফটো আপলোডৰ সৈতে)
            elif role == "Service Engineer" and t_status == "ASSIGNED_ENG":
                notes = st.text_area("Work Done / Rectification Notes", key=f"eng_in_{t_id}")
                rect_img = st.file_uploader("কাম কৰাৰ পাছৰ ফটো আপলোড কৰক", type=["jpg", "png", "jpeg"], key=f"eng_img_{t_id}")
                
                if st.button("Request Close", key=f"eng_btn_{t_id}"):
                    if notes:
                        rect_photo_path = save_uploaded_file(rect_img, t_id, "rect")
                        cursor.execute("""
                            UPDATE faults 
                            SET rectification = ?, rect_photo = ?, status = 'PENDING_UT_VERIFY' 
                            WHERE id = ?
                        """, (notes, rect_photo_path, t_id))
                        conn.commit()
                        st.rerun()

            # ৫. Utility Tech Verification Actions
            elif role == "Utility Technician" and t_status == "PENDING_UT_VERIFY":
                st.write("🔧 *Service Engineer-এ কাম সম্পূৰ্ণ কৰিছে আৰু ওপৰত ফটো দিছে। পৰীক্ষা কৰি সিদ্ধান্ত লওক:*")
                c1, c2 = st.columns(2)
                if c1.button("Approve & Close", key=f"ut_app_{t_id}"):
                    cursor.execute("UPDATE faults SET status = 'CLOSED', closed_at = ? WHERE id = ?", (datetime.now(), t_id))
                    conn.commit()
                    st.rerun()
                if c2.button("Reject", key=f"ut_rej_{t_id}"):
                    cursor.execute("UPDATE faults SET status = 'ASSIGNED_ENG' WHERE id = ?", (t_id,))
                    conn.commit()
                    st.rerun()