import streamlit as st
import sqlite3
import os
import requests
import pytz
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="DG Fault Portal", layout="wide")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- IST TIME HELPER -----------------
def get_ist_now():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

# ----------------- TELEGRAM BOT CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8984648592:AAG0JKeI_z5gSrkF5A31AfYTYogmjzvg-FA"
TELEGRAM_CHAT_ID = "-1003996057592"

def send_telegram_alert(message_text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

# ----------------- USER ACCOUNTS -----------------
USERS = {
    # 27 Utility Technicians
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
    
    # 3 Service Managers (JC-Mapped)
    "manager1": {"password": "2026", "role": "Service Manager", "name": "Ajay Sharma (SM)", "jc": "Shillong"},
    "manager2": {"password": "2026", "role": "Service Manager", "name": "Rakesh Ahmed (SM)", "jc": "Tura"},
    "manager3": {"password": "2026", "role": "Service Manager", "name": "Saharul (SM)", "jc": "Jowai"},
    
    # Docket Desk
    "docket": {"password": "2027", "role": "Docket Team", "name": "Docket Desk"},
    
    # 15 Service Engineers
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
    "eng15": {"password": "124", "role": "Service Engineer", "name": "Khairul Islam (Engineer)"}
}

ENGINEERS_LIST = {u: USERS[u]["name"] for u in USERS if USERS[u]["role"] == "Service Engineer"}
MANAGERS_LIST = {u: USERS[u]["name"] for u in USERS if USERS[u]["role"] == "Service Manager"}
JC_LIST = ["Tura", "Shillong", "Jowai"]

# ----------------- DATABASE SETUP -----------------
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

thirty_days_ago = (get_ist_now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
cursor.execute("DELETE FROM faults WHERE status = 'CLOSED' AND closed_at < ?", (thirty_days_ago,))
conn.commit()

def save_image_buffer(image_buffer, prefix, user_or_ticket):
    """Saves a single uploaded image or camera buffer and returns the file path."""
    if image_buffer is not None:
        filename = f"{prefix}_{user_or_ticket}_{int(get_ist_now().timestamp())}_{os.urandom(3).hex()}.jpg"
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

def save_multiple_images(file_list, prefix, ticket_id):
    """Saves multiple uploaded files and returns comma-separated file paths."""
    if not file_list:
        return ""
    saved_paths = []
    for idx, f in enumerate(file_list):
        path = save_image_buffer(f, f"{prefix}_{idx+1}", ticket_id)
        if path:
            saved_paths.append(path)
    return ",".join(saved_paths)

def display_images_gallery(paths_str, caption_title):
    """Renders single or multiple comma-separated image paths cleanly."""
    if not paths_str:
        return
    paths = [p.strip() for p in paths_str.split(",") if p.strip()]
    valid_paths = [p for p in paths if os.path.exists(p)]
    if not valid_paths:
        return
    st.write(f"📸 **{caption_title} ({len(valid_paths)} photo{'s' if len(valid_paths) > 1 else ''}):**")
    cols = st.columns(min(len(valid_paths), 4))
    for i, p in enumerate(valid_paths):
        with cols[i % len(cols)]:
            st.image(p, caption=f"Photo {i+1}", use_container_width=True)

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

        st.write("📍 **Capturing live location...**")
        loc = get_geolocation()
        current_map_link = ""

        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            current_map_link = f"https://www.google.com/maps?q={lat},{lon}"
            st.success(f"Location captured: {lat:.4f}, {lon:.4f}")
        else:
            st.warning("Please turn on Device GPS / Location and allow browser permissions.")

        st.write("📷 **Take live selfie to login (Mandatory):**")
        selfie_pic = st.camera_input("Take Live Selfie")

        if st.button("Login", use_container_width=True):
            if login_user in USERS and USERS[login_user]["password"] == login_pass:
                if selfie_pic is None:
                    st.error("Taking a selfie is mandatory!")
                elif not current_map_link:
                    st.error("GPS location not detected! Please turn on device GPS and allow browser location access.")
                else:
                    saved_selfie = save_image_buffer(selfie_pic, "login_selfie", login_user)
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.user_info = USERS[login_user]
                    st.session_state.login_selfie_path = saved_selfie
                    st.session_state.login_location = current_map_link
                    st.rerun()
            else:
                st.error("Invalid Username or Password!")
else:
    current_username = st.session_state.username
    user = st.session_state.user_info
    role = user["role"]
    user_selfie = st.session_state.login_selfie_path
    user_loc = st.session_state.login_location

    col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
    with col_t1:
        st.title("⚡ DG Fault Portal")
        jc_badge = f" | Assigned JC: **{user.get('jc')}**" if user.get('jc') else ""
        st.caption(f"Logged in: **{user['name']}** ({current_username}) | Role: **{role}**{jc_badge}")
        if user_loc:
            st.markdown(f"[📍 View Login Location on Google Maps]({user_loc})")
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

    # 1. Utility Technician Form (Fault Log with Multiple Photo Upload)
    if role == "Utility Technician":
        st.subheader("Log New Fault Request")
        with st.form("new_fault_form"):
            c_site, c_jc = st.columns([2, 1])
            with c_site:
                site = st.text_input("Site ID (e.g. GUW-10)")
            with c_jc:
                selected_jc = st.selectbox("Job Centre (JC)", JC_LIST)
            
            c_dg1, c_dg2 = st.columns(2)
            with c_dg1:
                dg_make = st.selectbox(
                    "DG Make", 
                    ["Kirloskar", "Mahindra", "Eicher"]
                )
            with c_dg2:
                dg_rating = st.selectbox(
                    "DG Rating (kVA)", 
                    ["10 kVA", "15 kVA", "20 kVA", "25 kVA", "30 kVA", "125 kVA"]
                )

            st.markdown("---")
            st.markdown("📞 **Pre-logging Online Support Details:**")
            
            support_names_list = ["None / No support contacted", "Other (Mention name below)"] + list(ENGINEERS_LIST.values()) + list(MANAGERS_LIST.values())
            selected_support_person = st.selectbox("Who was contacted for Online Support?", support_names_list)
            
            custom_person_name = ""
            if selected_support_person == "Other (Mention name below)":
                custom_person_name = st.text_input("Enter the person's name who provided support:")

            online_sup_remarks = st.text_input("Advice / troubleshooting steps given during online support:")

            st.markdown("---")
            desc = st.text_area("Fault Remarks / Description")
            
            # Multiple photo upload enabled
            fault_imgs = st.file_uploader(
                "Upload Fault Photos (You can select multiple photos)", 
                type=["jpg", "png", "jpeg"], 
                accept_multiple_files=True
            )
            submit = st.form_submit_button("Submit Fault Request")

            if submit and site and desc:
                # Determine final online support name
                if selected_support_person == "Other (Mention name below)":
                    support_final_name = custom_person_name.strip() if custom_person_name.strip() else "Other Person"
                else:
                    support_final_name = selected_support_person

                cursor.execute("SELECT COUNT(*) FROM faults")
                count = cursor.fetchone()[0]
                new_id = f"TKT-{count + 101}"
                
                # Save multiple photos
                photo_paths = save_multiple_images(fault_imgs, "fault", new_id)

                site_with_jc = f"{site} [{selected_jc}]"
                dg_combined = f"{dg_make} ({dg_rating})"
                now_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")

                full_desc = (
                    f"{desc}\n\n"
                    f"📞 Online Support: {support_final_name}\n"
                    f"💡 Support Guidance: {online_sup_remarks if online_sup_remarks else 'N/A'}"
                )

                cursor.execute("""
                    INSERT INTO faults (
                        id, site, dg, desc, status, docket, assigned_eng, 
                        logged_by, logged_by_selfie, logged_by_loc, 
                        action_by_selfie, action_by_loc, rectification, 
                        fault_photo, rect_photo, created_at, closed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_id, site_with_jc, dg_combined, full_desc, 'PENDING_SM', '', '', 
                    current_username, user_selfie, user_loc, 
                    '', '', '', photo_paths, '', now_time, None
                ))
                conn.commit()

                photo_count = len(fault_imgs) if fault_imgs else 0
                tg_msg = (
                    f"🚨 *New DG Fault Logged!*\n\n"
                    f"📌 *Ticket ID:* `{new_id}`\n"
                    f"🏢 *Site ID:* {site}\n"
                    f"📍 *JC:* {selected_jc}\n"
                    f"🏭 *DG:* {dg_make} ({dg_rating})\n"
                    f"📞 *Online Support:* {support_final_name}\n"
                    f"💡 *Support Guidance:* {online_sup_remarks if online_sup_remarks else 'N/A'}\n"
                    f"📝 *Fault Remarks:* {desc}\n"
                    f"📷 *Photos Uploaded:* {photo_count}\n"
                    f"👤 *Logged by:* {user['name']}\n"
                    f"🕒 *Date & Time:* {format_dt(now_time)}"
                )
                send_telegram_alert(tg_msg)

                st.success(f"Fault ticket {new_id} created successfully with {photo_count} photo(s)! Telegram notification sent.")
                st.rerun()
            elif submit:
                st.error("Site ID and Fault Remarks are required!")

        st.divider()

    st.subheader("Fault Requests & Status Tracker")

    cursor.execute("""
        SELECT id, site, dg, desc, status, docket, assigned_eng, logged_by, logged_by_selfie, logged_by_loc, action_by_selfie, action_by_loc, rectification, fault_photo, rect_photo, created_at, closed_at 
        FROM faults ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        st.info("No fault records found.")

    for r in rows:
        (t_id, t_site, t_dg, t_desc, t_status, t_docket, t_eng, t_logged_by, 
         t_l_selfie, t_l_loc, t_act_selfie, t_act_loc, t_rect, t_fphoto, t_rphoto, 
         t_created_at, t_closed_at) = r

        created_str = format_dt(t_created_at)
        closed_str = format_dt(t_closed_at)

        ticket_jc = "Unknown"
        for jc_opt in JC_LIST:
            if f"[{jc_opt}]" in t_site:
                ticket_jc = jc_opt
                break

        with st.expander(f"{t_id} | {t_site} - {t_dg} | [{t_status}] 📅 {created_str}", expanded=(t_status != 'CLOSED')):
            c_meta1, c_meta2 = st.columns(2)
            with c_meta1:
                st.write(f"🕒 **Logged Date (IST):** {created_str}")
            with c_meta2:
                if t_status == "CLOSED" and closed_str:
                    st.write(f"✅ **Closed Date (IST):** {closed_str}")

            st.write(f"**Fault Details & Online Support:**")
            st.info(t_desc)
            
            c_info1, c_info2 = st.columns([3, 1])
            with c_info1:
                creator_name = USERS.get(t_logged_by, {}).get('name', t_logged_by)
                st.caption(f"Logged by: **{creator_name}** | JC: **{ticket_jc}**")
                if t_l_loc:
                    st.markdown(f"📍 [View Creator GPS Location]({t_l_loc})")
            with c_info2:
                if t_l_selfie and os.path.exists(t_l_selfie):
                    st.image(t_l_selfie, caption="Logged Selfie", width=80)

            # Display multiple fault photos
            display_images_gallery(t_fphoto, "Fault Photos")

            if t_docket:
                eng_display = USERS.get(t_eng, {}).get("name", t_eng)
                st.info(f"Docket No: **{t_docket}** | Assigned Engineer: **{eng_display}**")

            if t_rect:
                st.warning(f"Rectification Notes: {t_rect}")

            # Display multiple rectification photos
            display_images_gallery(t_rphoto, "Rectification Photos")

            if t_act_selfie and os.path.exists(t_act_selfie):
                st.write("---")
                c_act1, c_act2 = st.columns([3, 1])
                with c_act1:
                    st.caption("Action / Verification Taken By:")
                    if t_act_loc:
                        st.markdown(f"📍 [View Action Taker GPS Location]({t_act_loc})")
                with c_act2:
                    st.image(t_act_selfie, caption="Action Selfie", width=80)

            # 2. Service Manager Stage (JC-Enforced)
            if role == "Service Manager" and t_status == "PENDING_SM":
                manager_jc = user.get("jc", "")
                if ticket_jc == manager_jc:
                    st.success(f"✔️ This ticket belongs to your jurisdiction ({manager_jc} JC).")
                    c1, c2 = st.columns(2)
                    if c1.button("Approve", key=f"sm_app_{t_id}"):
                        cursor.execute("""
                            UPDATE faults SET status = 'PENDING_DOCKET', action_by_selfie = ?, action_by_loc = ? 
                            WHERE id = ?
                        """, (user_selfie, user_loc, t_id))
                        conn.commit()
                        send_telegram_alert(f"✅ Fault Approved by SM\nTicket: {t_id}\nJC: {ticket_jc}\nManager: {user['name']}\nStatus: PENDING DOCKET")
                        st.rerun()
                    if c2.button("Reject", key=f"sm_rej_{t_id}"):
                        cursor.execute("""
                            UPDATE faults SET status = 'REJECTED', action_by_selfie = ?, action_by_loc = ? 
                            WHERE id = ?
                        """, (user_selfie, user_loc, t_id))
                        conn.commit()
                        send_telegram_alert(f"❌ Fault REJECTED by SM\nTicket: {t_id}\nJC: {ticket_jc}\nManager: {user['name']}")
                        st.rerun()
                else:
                    assigned_sm_name = "Assigned SM"
                    for u in USERS.values():
                        if u.get("role") == "Service Manager" and u.get("jc") == ticket_jc:
                            assigned_sm_name = u.get("name")
                            break
                    st.warning(f"🔒 This ticket belongs to **{ticket_jc}** JC. Only **{assigned_sm_name}** is authorized to approve/reject.")

            # 3. Docket Team Stage
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
                        send_telegram_alert(f"📋 Docket Assigned\nTicket: {t_id}\nJC: {ticket_jc}\nDocket No: {d_no}\nAssigned Engineer: {eng_name}")
                        st.rerun()
                    else:
                        st.error("Please enter a Docket Number.")

            # 4. Service Engineer Stage (With multiple rectification photos upload)
            elif role == "Service Engineer" and t_status == "ASSIGNED_ENG":
                if t_eng == current_username:
                    st.success("🔧 This ticket is assigned to you:")
                    notes = st.text_area("Work Done / Rectification Notes", key=f"eng_in_{t_id}")
                    
                    # Multiple work photos upload enabled
                    rect_imgs = st.file_uploader(
                        "Upload Post-Work Photos (Multiple photos allowed)", 
                        type=["jpg", "png", "jpeg"], 
                        accept_multiple_files=True,
                        key=f"eng_img_{t_id}"
                    )
                    
                    if st.button("Request Close", key=f"eng_btn_{t_id}"):
                        if notes:
                            rect_photo_paths = save_multiple_images(rect_imgs, "rect", t_id)
                            cursor.execute("""
                                UPDATE faults 
                                SET rectification = ?, rect_photo = ?, status = 'PENDING_UT_VERIFY', action_by_selfie = ?, action_by_loc = ? 
                                WHERE id = ?
                            """, (notes, rect_photo_paths, user_selfie, user_loc, t_id))
                            conn.commit()
                            rect_count = len(rect_imgs) if rect_imgs else 0
                            send_telegram_alert(f"🔧 Work Completed by Engineer\nTicket: {t_id}\nJC: {ticket_jc}\nEngineer: {user['name']}\nWork Photos: {rect_count}\nStatus: PENDING UT VERIFICATION")
                            st.rerun()
                        else:
                            st.error("Rectification notes are mandatory!")
                else:
                    assigned_name = USERS.get(t_eng, {}).get("name", t_eng)
                    st.info(f"🔒 This ticket is assigned to **{assigned_name}**.")

            # 5. Utility Tech Final Verification
            elif role == "Utility Technician" and t_status == "PENDING_UT_VERIFY":
                if t_logged_by == current_username:
                    st.write("🔍 *You logged this ticket. Please verify work done and decide:*")
                    c1, c2 = st.columns(2)
                    if c1.button("Approve & Close", key=f"ut_app_{t_id}"):
                        now_close = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("""
                            UPDATE faults SET status = 'CLOSED', closed_at = ?, action_by_selfie = ?, action_by_loc = ? 
                            WHERE id = ?
                        """, (now_close, user_selfie, user_loc, t_id))
                        conn.commit()
                        send_telegram_alert(f"🎉 Ticket CLOSED Successfully\nTicket: {t_id}\nJC: {ticket_jc}\nVerified & Closed by: {user['name']}")
                        st.rerun()
                    if c2.button("Reject (Re-assign to Engineer)", key=f"ut_rej_{t_id}"):
                        cursor.execute("UPDATE faults SET status = 'ASSIGNED_ENG' WHERE id = ?", (t_id,))
                        conn.commit()
                        send_telegram_alert(f"⚠️ Ticket Verification Rejected by UT\nTicket: {t_id}\nJC: {ticket_jc}\nRe-opened for Engineer.")
                        st.rerun()
                else:
                    creator_name = USERS.get(t_logged_by, {}).get("name", t_logged_by)
                    st.warning(f"🔒 This fault was logged by **{creator_name}**. Only the creator can close it.")
