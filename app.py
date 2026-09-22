import streamlit as st
import sqlite3
import os
import requests
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="DG Fault Portal", layout="wide")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- TELEGRAM BOT CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8984648592:AAG0JKeI_z5gSrkF5A31AfYTYogmjzvg-FA"
TELEGRAM_CHAT_ID = "-1003596057592"

def send_telegram_alert(message_text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

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
    "eng1": {"password": "124", "role": "Service Engineer", "name": "Biren (Engineer)"},
    "eng2": {"password": "124", "role": "Service Engineer", "name": "Anup (Engineer)"}
}

ENGINEERS_LIST = {u: USERS[u]["name"] for u in USERS if USERS[u]["role"] == "Service Engineer"}

# ----------------- DATABASE SETUP -----------------
# পুৰণি টেবুলৰ অমিল এৰাবলৈ v2 ডাটাবেচ ব্যৱহাৰ কৰা হৈছে
conn = sqlite3.connect("dg_faults_v2.db", check_same_thread=False)
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
    created_at TEXT,
    closed_at TEXT
)
""")
conn.commit()

thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
cursor.execute("DELETE FROM faults WHERE status = 'CLOSED' AND closed_at < ?", (thirty_days_ago,))
conn.commit()

def save_image_buffer(image_buffer, prefix, user_or_ticket):
    if image_buffer is not None:
        filename = f"{prefix}{user_or_ticket}{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            if hasattr(image_buffer, "getvalue"):
                f.write(image_buffer.getvalue())
            elif hasattr(image_buffer, "get_buffer"):
                f.write(image_buffer.get_buffer())
            else:
                f.write(image_buffer.read())
        return filepath
    return ""

def format_dt(dt_val):
    if not dt_val:
        return ""
    try:
        if isinstance(dt_val, str):
            clean_str = dt_val.split(".")[0]
            dt_obj = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt_obj = dt_val
        return dt_obj.strftime("%d-%b-%Y, %I:%M %p")
    except Exception:
        return str(dt_val)[:16]

# ----------------- SESSION & LOGIN (SELFIE & GPS) -----------------
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

        st.write("📍 *লাইভ লোকেশন ধৰা হৈছে...*")
        loc = get_geolocation()
        current_map_link = ""

        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            current_map_link = f"https://www.google.com/maps?q={lat},{lon}"
            st.success(f"Location ধৰা পৰিছে: {lat:.4f}, {lon:.4f}")
        else:
            st.warning("ম'বাইলত Location (GPS) On কৰক আৰু ব্ৰাউজাৰক Allow কৰক।")

        st.write("📷 *লগ-ইন কৰিবলৈ চেলফি লওক (বাধ্যতামূলক):*")
        selfie_pic = st.camera_input("Take Live Selfie")

        if st.button("Login", use_container_width=True):
            if login_user in USERS and USERS[login_user]["password"] == login_pass:
                if selfie_pic is None:
                    st.error("চেলফি লোৱাটো বাধ্যতামূলক!")
                elif not current_map_link:
                    st.error("GPS Location ধৰা পৰা নাই! ম'বাইলৰ GPS On কৰি ব্ৰাউজাৰত Allow কৰক।")
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
        st.caption(f"Logged in: *{user['name']}* ({current_username}) | Role: *{role}*")
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

                now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO faults (
                        id, site, dg, desc, status, docket, assigned_eng, 
                        logged_by, logged_by_selfie, logged_by_loc, 
                        action_by_selfie, action_by_loc, rectification, 
                        fault_photo, rect_photo, created_at, closed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_id, site, dg, desc, 'PENDING_SM', '', '', 
                    current_username, user_selfie, user_loc, 
                    '', '', '', photo_path, '', now_time, None
                ))
                conn.commit()

                # Telegram Alert
                tg_msg = (
                    f"🚨 নতুন DG Fault Logged!\n\n"
                    f"📌 Ticket ID: {new_id}\n"
                    f"🏢 Site: {site}\n"
                    f"⚙️ DG: {dg}\n"
                    f"📝 সমস্যা: {desc}\n"
                    f"👤 Logged by: {user['name']}\n"
                    f"🕒 Date: {format_dt(now_time)}"
                )
                send_telegram_alert(tg_msg)

                st.success(f"Fault {new_id} সফলভাৱে যোগ কৰা হ'ল! Telegram-ত Alert পঠিওৱা হৈছে।")
                st.rerun()

        st.divider()

    st.subheader("Fault Requests & Status")

    cursor.execute("""
        SELECT id, site, dg, desc, status, docket, assigned_eng, logged_by, logged_by_selfie, logged_by_loc, action_by_selfie, action_by_loc, rectification, fault_photo, rect_photo, created_at, closed_at 
        FROM faults ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        st.info("কোনো ৰেকৰ্ড পোৱা নগ'ল।")

    for r in rows:
        (t_id, t_site, t_dg, t_desc, t_status, t_docket, t_eng, t_logged_by, 
         t_l_selfie, t_l_loc, t_act_selfie, t_act_loc, t_rect, t_fphoto, t_rphoto, 
         t_created_at, t_closed_at) = r

        created_str = format_dt(t_created_at)
        closed_str = format_dt(t_closed_at)

        with st.expander(f"{t_id} | {t_site} - {t_dg} | [{t_status}] 📅 {created_str}", expanded=(t_status != 'CLOSED')):
            c_meta1, c_meta2 = st.columns(2)
            with c_meta1:
                st.write(f"🕒 *Fault Logged Date:* {created_str}")
            with c_meta2:
                if t_status == "CLOSED" and closed_str:
                    st.write(f"✅ *Closed Date:* {closed_str}")

            st.write(f"*সমস্যা:* {t_desc}")
            
            c_info1, c_info2 = st.columns([3, 1])
            with c_info1:
                creator_name = USERS.get(t_logged_by, {}).get('name', t_logged_by)
                st.caption(f"Logged by: *{creator_name}*")
                if t_l_loc:
                    st.markdown(f"📍 [Creator GPS Location মানচিত্ৰত চাওক]({t_l_loc})")
            with c_info2:
                if t_l_selfie and os.path.exists(t_l_selfie):
                    st.image(t_l_selfie, caption="Logged Selfie", width=80)

            if t_fphoto and os.path.exists(t_fphoto):
                st.image(t_fphoto, caption="Fault Photo", width=300)

            if t_docket:
                eng_display = USERS.get(t_eng, {}).get("name", t_eng)
                st.info(f"Docket No: *{t_docket}* | Assigned Engineer: *{eng_display}*")

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
                if c1.button("Approve", key=f"sm_app_{t_id}"):
                    cursor.execute("""
                        UPDATE faults SET status = 'PENDING_DOCKET', action_by_selfie = ?, action_by_loc = ? 
                        WHERE id = ?
                    """, (user_selfie, user_loc, t_id))
                    conn.commit()
                    send_telegram_alert(f"✅ Fault Approved by SM\nTicket: {t_id}\nManager: {user['name']}\nStatus: PENDING DOCKET")
                    st.rerun()
                if c2.button("Reject", key=f"sm_rej_{t_id}"):
                    cursor.execute("""
                        UPDATE faults SET status = 'REJECTED', action_by_selfie = ?, action_by_loc = ? 
                        WHERE id = ?
                    """, (user_selfie, user_loc, t_id))
                    conn.commit()
                    send_telegram_alert(f"❌ Fault REJECTED by SM\nTicket: {t_id}\nManager: {user['name']}")
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
                        eng_name = ENGINEERS_LIST[selected_eng]
                        send_telegram_alert(f"📋 Docket Assigned\nTicket: {t_id}\nDocket No: {d_no}\nAssigned Engineer: {eng_name}")
                        st.rerun()
                    else:
                        st.error("Docket No দিয়ক!")

            # ৪. Service Engineer স্তৰ (কেৱল দায়িত্ব পোৱাজনেহে কৰিব পাৰিব)
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
                            send_telegram_alert(f"🔧 Work Completed by Engineer\nTicket: {t_id}\nEngineer: {user['name']}\nStatus: PENDING UT VERIFICATION")
                            st.rerun()
                        else:
                            st.error("Notes লিখাটো বাধ্যতামূলক!")
                else:
                    assigned_name = USERS.get(t_eng, {}).get("name", t_eng)
                    st.info(f"🔒 এই কামটো *{assigned_name}*-ক অৰ্পণ কৰা হৈছে।")

            # ৫. Utility Tech Final Verification (কেৱল Fault বনোৱা টেকনিচিয়ানেহে Close কৰিব পাৰিব)
            elif role == "Utility Technician" and t_status == "PENDING_UT_VERIFY":
                if t_logged_by == current_username:
                    st.write("🔍 আপুনি এই টিকটটো খুলিছিল। পৰীক্ষা কৰি সিদ্ধান্ত লওক:")
                    c1, c2 = st.columns(2)
                    if c1.button("Approve & Close", key=f"ut_app_{t_id}"):
                        now_close = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("""
                            UPDATE faults SET status = 'CLOSED', closed_at = ?, action_by_selfie = ?, action_by_loc = ? 
                            WHERE id = ?
                        """, (now_close, user_selfie, user_loc, t_id))
                        conn.commit()
                        send_telegram_alert(f"🎉 Ticket CLOSED Successfully\nTicket: {t_id}\nVerified & Closed by: {user['name']}")
                        st.rerun()
                    if c2.button("Reject (Re-assign to Engineer)", key=f"ut_rej_{t_id}"):
                        cursor.execute("UPDATE faults SET status = 'ASSIGNED_ENG' WHERE id = ?", (t_id,))
                        conn.commit()
                        send_telegram_alert(f"⚠️ Ticket Verification Rejected by UT\nTicket: {t_id}\nRe-opened for Engineer.")
                        st.rerun()
                else:
                    creator_name = USERS.get(t_logged_by, {}).get("name", t_logged_by)
                    st.warning(f"🔒 এই Fault টো *{creator_name}*-এ তুলিছিল। কেৱল তেওঁহে Close কৰিব পাৰিব।")
