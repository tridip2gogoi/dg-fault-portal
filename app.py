import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="DG Fault Portal", layout="wide")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- USER ACCOUNTS -----------------
USERS = {
    "tech1": {"password": "123", "role": "Utility Technician", "name": "Anupam Kumer Shing (Tech)"},
    "tech2": {"password": "123", "role": "Utility Technician", "name": "Jul Hussain (Tech)"},
    "tech3": {"password": "123", "role": "Utility Technician", "name": "Shariful Islam (Tech)"},
    "tech4": {"password": "123", "role": "Utility Technician", "name": "Aminul Islam (Tech)"},
    "tech5": {"password": "123", "role": "Utility Technician", "name": "Md Rizwan (Tech)"},
    "tech6": {"password": "123", "role": "Utility Technician", "name": "Amresh Kumar (Tech)"},
    "tech7": {"password": "123", "role": "Utility Technician", "name": "Hazrat Ali (Tech)"},
    "tech8": {"password": "123", "role": "Utility Technician", "name": "Avinash Kumar (Tech)"},
    "tech9": {"password": "123", "role": "Utility Technician", "name": "Anurag Kumar (Tech)"},
    "tech10": {"password": "123", "role": "Utility Technician", "name": "Md Tazirul Islam (Tech)"},
    "tech11": {"password": "123", "role": "Utility Technician", "name": "Manseng Marak (Tech)"},
    "tech12": {"password": "123", "role": "Utility Technician", "name": "Babidul Islam (Tech)"},
    "tech13": {"password": "123", "role": "Utility Technician", "name": "Brindabon Hajong (Tech)"},
    "tech14": {"password": "123", "role": "Utility Technician", "name": "Gaganjyoti Das (Tech)"},
    "tech15": {"password": "123", "role": "Utility Technician", "name": "Golap Rabbani (Tech)"},
    "tech16": {"password": "123", "role": "Utility Technician", "name": "Hakibul Islam (Tech)"},
    "tech17": {"password": "123", "role": "Utility Technician", "name": "Sengjal D Sangma (Tech)"},
    "tech18": {"password": "123", "role": "Utility Technician", "name": "Namsrang R Sangma (Tech)"},
    "tech19": {"password": "123", "role": "Utility Technician", "name": "Nazrul Ahmed (Tech)"},
    "tech20": {"password": "123", "role": "Utility Technician", "name": "Ashutosh Kumar (Tech)"},
    "tech21": {"password": "123", "role": "Utility Technician", "name": "Santosh Kumar Yadav (Tech)"},
    "tech22": {"password": "123", "role": "Utility Technician", "name": "Sengba G Sangma (Tech)"},
    "tech23": {"password": "123", "role": "Utility Technician", "name": "Shanjibul Ahmed (Tech)"},
    "tech24": {"password": "123", "role": "Utility Technician", "name": "Vikash Kumar (Tech)"},
    "tech25": {"password": "123", "role": "Utility Technician", "name": "Walseng B Marak (Tech)"},
    "tech26": {"password": "123", "role": "Utility Technician", "name": "Zeaul Hoque (Tech)"},
    "tech27": {"password": "123", "role": "Utility Technician", "name": "Dharamveer (Tech)"},
    "manager1": {"password": "2026", "role": "Service Manager", "name": "Ajay Sharma (SM)"},
    "manager2": {"password": "2026", "role": "Service Manager", "name": "Rakesh Ahmed (SM)"},
    "manager3": {"password": "2026", "role": "Service Manager", "name": "Saharul (SM)"},
    "docket": {"password": "2027", "role": "Docket Team", "name": "Docket Desk"},
    "eng1": {"password": "124", "role": "Service Engineer", "name": "Harnual Roshid (Engineer)"},
    "eng2": {"password": "124", "role": "Service Engineer", "name": "Krishna Kanta Hazarika (Engineer)"},
    "eng3": {"password": "124", "role": "Service Engineer", "name": "Shaha Alom (Engineer)"},
    "eng4": {"password": "124", "role": "Service Engineer", "name": "Suman Kumar (Engineer)"},
    "eng5": {"password": "124", "role": "Service Engineer", "name": "Belikson Momin (Engineer)"},
    "eng6": {"password": "124", "role": "Service Engineer", "name": "Sengvear Momin (Engineer)"},
    "eng7": {"password": "124", "role": "Service Engineer", "name": "Ramij Ali (Engineer)"},
    "eng8": {"password": "124", "role": "Service Engineer", "name": "George Momin (Engineer)"},
    "eng9": {"password": "124", "role": "Service Engineer", "name": "Mofidul Islam (Engineer)"},
    "eng10": {"password": "124", "role": "Service Engineer", "name": "Binod Sangma (Engineer)"},
    "eng11": {"password": "124", "role": "Service Engineer", "name": "Rakibul Islam (Engineer)"},
    "eng12": {"password": "124", "role": "Service Engineer", "name": "Alexbirth Sangma (Engineer)"},
    "eng13": {"password": "124", "role": "Service Engineer", "name": "Habizul Rahman (Engineer)"},
    "eng14": {"password": "124", "role": "Service Engineer", "name": "Stebirth Sangma (Engineer)"},
    "eng15": {"password": "124", "role": "Service Engineer", "name": "Khairul Islam (Engineer)"},
}

ENGINEERS_LIST = {u: USERS[u]["name"] for u in USERS if USERS[u]["role"] == "Service Engineer"}

# ----------------- DATABASE SETUP -----------------
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
    assigned_eng TEXT,
    logged_by TEXT,
    logged_by_selfie TEXT,
    logged_by_loc TEXT,
    action_by_selfie TEXT,
    action_by_loc TEXT,
    rectification TEXT,
    fault_photo TEXT,
    rect_photo TEXT,
    created_at TIMESTAMP,
    closed_at TIMESTAMP
)
""")
conn.commit()

for col in ["logged_by_selfie", "logged_by_loc", "action_by_selfie", "action_by_loc"]:
    try:
        cursor.execute(f"ALTER TABLE faults ADD COLUMN {col} TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

thirty_days_ago = datetime.now() - timedelta(days=30)
cursor.execute("DELETE FROM faults WHERE status = 'CLOSED' AND closed_at < ?", (thirty_days_ago,))
conn.commit()

def save_image_buffer(image_buffer, prefix, user_or_ticket):
    if image_buffer is not None:
        filename = f"{prefix}_{user_or_ticket}_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(image_buffer.get_buffer())
        return filepath
    return ""

# ----------------- SESSION & LOGIN (WITH SELFIE & GPS) -----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_info = None
    st.session_state.login_selfie_path = ""
    st.session_state.login_location = ""

if not st.session_state.logged_in:
    st.title("⚡ DG Fault Management Portal")
    st.subheader("Login, Live Selfie & GPS Verification")

    col1, _ = st.columns([1.8, 2])
    with col1:
        login_user = st.text_input("Username")
        login_pass = st.text_input("Password", type="password")

        st.write("📍 **লাইভ লোকেশন ধৰা হৈছে...**")
        loc = get_geolocation()
        current_map_link = ""

        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            current_map_link = f"https://www.google.com/maps?q={lat},{lon}"
            st.success(f"Location ধৰা পৰিছে: {lat:.4f}, {lon:.4f}")
        else:
            st.warning("ম'বাইলত Location (GPS) On কৰক আৰু ব্ৰাউজাৰক Allow কৰক।")

        st.write("📷 **লগ-ইন কৰিবলৈ চেলফি লওক (বাধ্যতামূলক):**")
        selfie_pic = st.camera_input("Take Live Selfie")

        if st.button("Login", use_container_width=True):
            if login_user in USERS and USERS[login_user]["password"] == login_pass:
                if selfie_pic is None:
                    st.error("চেলফি লোৱাটো বাধ্যতামূলক!")
                elif not current_map_link:
                    st.error("GPS Location ধৰা পৰা নাই! ম'বাইলৰ GPS On কৰি Allow কৰক।")
                else:
                    saved_selfie = save_image_buffer(selfie_pic, "login_selfie", login_user)
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.user_info = USERS[login_user]
                    st.session_state.login_selfie_path = saved_selfie
                    st.session_state.login_location = current_map_link
                    st.rerun()
            else:
                st.error("ভুল Username বা Password!")
else:
    current_username = st.session_state.username
    user = st.session_state.user_info
    role = user["role"]
    user_selfie = st.session_state.login_selfie_path
    user_loc = st.session_state.login_location

    col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
    with col_t1:
        st.title("⚡ DG Fault Portal")
        st.caption(f"Logged in: **{user['name']}** ({current_username}) | Role: **{role}**")
        if user_loc:
            st.markdown(f"[📍 আপোনাৰ Login Location চাওক]({user_loc})")
    with col_t2:
        if user_selfie and os.path.exists(user_selfie):
            st.image(user_selfie, caption="Login Selfie", width=70)
    with col_t3:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_info = None
            st.session_state.login_selfie_path = ""
            st.session_state.login_location = ""
            st.rerun()

    st.divider()

    # ১. Utility Technician Form (Fault Log)
    if role == "Utility Technician":
        st.subheader("নতুন Fault Log কৰক")
        with st.form("new_fault_form"):
            site = st.text_input("Site ID (যেনে: GUW-10)")
            dg = st.text_input("DG Model / Serial")
            desc = st.text_area("Fault Description")
            fault_img = st.file_uploader("Fault ৰ ফটো আপলোড কৰক", type=["jpg", "png", "jpeg"])
            submit = st.form_submit_button("Request পঠিয়াওক")

            if submit and site and dg:
                cursor.execute("SELECT COUNT(*) FROM faults")
                count = cursor.fetchone()[0]
                new_id = f"TKT-{count + 101}"
                photo_path = save_image_buffer(fault_img, "fault", new_id)

                cursor.execute("""
                    INSERT INTO faults (id, site, dg, desc, status, docket, assigned_eng, logged_by, logged_by_selfie, logged_by_loc, rectification, fault_photo, rect_photo, created_at, closed_at)
                    VALUES (?, ?, ?, ?, 'PENDING_SM', '', '', ?, ?, ?, '', ?, '', ?, NULL)
                """, (new_id, site, dg, desc, current_username, user_selfie, user_loc, photo_path, datetime.now()))
                conn.commit()

                st.success(f"Fault {new_id} সফলভাৱে যোগ কৰা হ'ল!")
                st.rerun()

        st.divider()

    st.subheader("Fault Requests & Status")

    cursor.execute("""
        SELECT id, site, dg, desc, status, docket, assigned_eng, logged_by, logged_by_selfie, logged_by_loc, action_by_selfie, action_by_loc, rectification, fault_photo, rect_photo 
        FROM faults ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        st.info("কোনো ৰেকৰ্ড পোৱা নগ'ল।")

    for r in rows:
        t_id, t_site, t_dg, t_desc, t_status, t_docket, t_eng, t_logged_by, t_l_selfie, t_l_loc, t_act_selfie, t_act_loc, t_rect, t_fphoto, t_rphoto = r

        with st.expander(f"{t_id} | {t_site} - {t_dg} | [{t_status}]", expanded=(t_status != 'CLOSED')):
            st.write(f"**সমস্যা:** {t_desc}")
            
            c_info1, c_info2 = st.columns([3, 1])
            with c_info1:
                creator_name = USERS.get(t_logged_by, {}).get('name', t_logged_by)
                st.caption(f"Logged by: **{creator_name}**")
                if t_l_loc:
                    st.markdown(f"📍 [Creator GPS Location মানচিত্ৰত চাওক]({t_l_loc})")
            with c_info2:
                if t_l_selfie and os.path.exists(t_l_selfie):
                    st.image(t_l_selfie, caption="Logged Selfie", width=80)

            if t_fphoto and os.path.exists(t_fphoto):
                st.image(t_fphoto, caption="Fault Photo", width=300)

            if t_docket:
                eng_display = USERS.get(t_eng, {}).get("name", t_eng)
                st.info(f"Docket No: **{t_docket}** | Assigned Engineer: **{eng_display}**")

            if t_rect:
                st.warning(f"Rectification Notes: {t_rect}")

            if t_rphoto and os.path.exists(t_rphoto):
                st.image(t_rphoto, caption="Work Photo", width=300)

            if t_act_selfie and os.path.exists(t_act_selfie):
                st.write("---")
                c_act1, c_act2 = st.columns([3, 1])
                with c_act1:
                    st.caption("Action/Verification সম্পূৰ্ণ কৰোঁতা:")
                    if t_act_loc:
                        st.markdown(f"📍 [Action Taker GPS Location চাওক]({t_act_loc})")
                with c_act2:
                    st.image(t_act_selfie, caption="Action Selfie", width=80)

            # ২. Service Manager স্তৰ
            if role == "Service Manager" and t_status == "PENDING_SM":
                c1, c2 = st.columns(2)
                if c1.button("Approve (Selfie & GPS Certified)", key=f"sm_app_{t_id}"):
                    cursor.execute("""
                        UPDATE faults SET status = 'PENDING_DOCKET', action_by_selfie = ?, action_by_loc = ? 
                        WHERE id = ?
                    """, (user_selfie, user_loc, t_id))
                    conn.commit()
                    st.rerun()
                if c2.button("Reject", key=f"sm_rej_{t_id}"):
                    cursor.execute("""
                        UPDATE faults SET status = 'REJECTED', action_by_selfie = ?, action_by_loc = ? 
                        WHERE id = ?
                    """, (user_selfie, user_loc, t_id))
                    conn.commit()
                    st.rerun()

            # ৩. Docket Team স্তৰ
            elif role == "Docket Team" and t_status == "PENDING_DOCKET":
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    d_no = st.text_input("Enter Docket No", key=f"doc_in_{t_id}")
                with col_d2:
                    selected_eng = st.selectbox(
                        "Assign Service Engineer",
                        options=list(ENGINEERS_LIST.keys()),
                        format_func=lambda x: ENGINEERS_LIST[x],
                        key=f"doc_eng_{t_id}"
                    )
                if st.button("Submit & Assign", key=f"doc_btn_{t_id}"):
                    if d_no:
                        cursor.execute("""
                            UPDATE faults SET docket = ?, assigned_eng = ?, status = 'ASSIGNED_ENG' 
                            WHERE id = ?
                        """, (d_no, selected_eng, t_id))
                        conn.commit()
                        st.rerun()
                    else:
                        st.error("Docket No দিয়ক!")

            # ৪. Service Engineer স্তৰ
            elif role == "Service Engineer" and t_status == "ASSIGNED_ENG":
                if t_eng == current_username:
                    st.success("🔧 এই কামটো আপোনাক অৰ্পণ কৰা হৈছে:")
                    notes = st.text_area("Work Done / Rectification Notes", key=f"eng_in_{t_id}")
                    rect_img = st.file_uploader("কাম কৰাৰ পাছৰ ফটো আপলোড কৰক", type=["jpg", "png", "jpeg"], key=f"eng_img_{t_id}")
                    
                    if st.button("Request Close", key=f"eng_btn_{t_id}"):
                        if notes:
                            rect_photo_path = save_image_buffer(rect_img, "rect", t_id)
                            cursor.execute("""
                                UPDATE faults 
                                SET rectification = ?, rect_photo = ?, status = 'PENDING_UT_VERIFY', action_by_selfie = ?, action_by_loc = ? 
                                WHERE id = ?
                            """, (notes, rect_photo_path, user_selfie, user_loc, t_id))
                            conn.commit()
                            st.rerun()
                        else:
                            st.error("Notes লিখাটো বাধ্যতামূলক!")
                else:
                    assigned_name = USERS.get(t_eng, {}).get("name", t_eng)
                    st.info(f"🔒 এই কামটো **{assigned_name}**-ক অৰ্পণ কৰা হৈছে।")

            # ৫. Utility Tech Final Verification
            elif role == "Utility Technician" and t_status == "PENDING_UT_VERIFY":
                if t_logged_by == current_username:
                    st.write("🔍 *আপুনি এই টিকটটো খুলিছিল। পৰীক্ষা কৰি সিদ্ধান্ত লওক:*")
                    c1, c2 = st.columns(2)
                    if c1.button("Approve & Close", key=f"ut_app_{t_id}"):
                        cursor.execute("""
                            UPDATE faults SET status = 'CLOSED', closed_at = ?, action_by_selfie = ?, action_by_loc = ? 
                            WHERE id = ?
                        """, (datetime.now(), user_selfie, user_loc, t_id))
                        conn.commit()
                        st.rerun()
                    if c2.button("Reject", key=f"ut_rej_{t_id}"):
                        cursor.execute("UPDATE faults SET status = 'ASSIGNED_ENG' WHERE id = ?", (t_id,))
                        conn.commit()
                        st.rerun()
                else:
                    creator_name = USERS.get(t_logged_by, {}).get("name", t_logged_by)
                    st.warning(f"🔒 এই Fault টো **{creator_name}**-এ তুলিছিল। কেৱল তেওঁহে Close কৰিব পাৰিব।")
