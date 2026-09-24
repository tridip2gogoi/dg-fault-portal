import streamlit as st
import os
import requests
import pytz
import pandas as pd
import io
import sqlite3
from datetime import datetime
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="DG Fault Management Portal", layout="wide")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- SQLITE LOCAL DATABASE SETUP -----------------
DB_FILE = "dg_faults.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS faults (
            id TEXT PRIMARY KEY,
            site TEXT,
            dg TEXT,
            desc TEXT,
            status TEXT,
            docket TEXT,
            assigned_eng TEXT,
            logged_by TEXT,
            mobile TEXT,
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
    ''')
    conn.commit()
    conn.close()

init_db()

def load_all_faults():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM faults ORDER BY created_at ASC")
        rows = c.fetchall()
        conn.close()
        return [[str(item) if item is not None else "" for item in r] for r in rows]
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return []

def add_fault_to_sheet(row_data):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO faults VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', tuple(row_data))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving to database: {e}")
        return False

def update_fault_in_sheet(ticket_id, updates_dict):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for k, v in updates_dict.items():
            query = f"UPDATE faults SET {k} = ? WHERE id = ?"
            c.execute(query, (str(v), str(ticket_id)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating database: {e}")
        return False

# ----------------- IST & TRT TIME HELPERS -----------------
def get_ist_now():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

def calculate_trt(created_at_str, closed_at_str=None):
    if not created_at_str:
        return "N/A", "Unknown", 0.0
    try:
        clean_created = created_at_str.split(".")[0]
        c_dt = datetime.strptime(clean_created, "%Y-%m-%d %H:%M:%S")
        if closed_at_str:
            clean_closed = closed_at_str.split(".")[0]
            end_dt = datetime.strptime(clean_closed, "%Y-%m-%d %H:%M:%S")
        else:
            end_dt = get_ist_now().replace(tzinfo=None)

        delta = end_dt - c_dt
        total_seconds = max(0, int(delta.total_seconds()))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        trt_str = f"{hours}h {minutes}m"
        total_hours = total_seconds / 3600.0

        if total_hours <= 24:
            category = "Normal (< 24h)"
        elif total_hours <= 48:
            category = "Warning (24-48h)"
        else:
            category = "Critical (> 48h)"

        return trt_str, category, total_hours
    except Exception:
        return "N/A", "Unknown", 0.0

# ----------------- TELEGRAM BOT CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "8984648592:AAG0JKeI_z5gSrkF5A31AfYTYogmjzvg-FA"
TELEGRAM_CHAT_ID = "-1003996057592"

def send_telegram_alert(message_text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message_text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

# ----------------- USER ACCOUNTS -----------------
USERS = {
    # Data Analysis & Central Supervisor
    "tridip.gogoi": {"password": "Gogoi@6095", "role": "Data Analysis", "name": "Central Supervisor (All JC)", "jc": "All"},

    # ----------------- UTILITY TECHNICIANS (64 USERS MAPPED TO JC) -----------------
    # Shillong JC
    "tech1": {"password": "123", "role": "Utility Technician", "name": "Ebestar Khongsit (Tech)", "jc": "Shillong"},
    "tech2": {"password": "123", "role": "Utility Technician", "name": "Augustar Buddon (Tech)", "jc": "Shillong"},
    "tech3": {"password": "123", "role": "Utility Technician", "name": "BANKITKUPAR RANI (Tech)", "jc": "Shillong"},
    "tech4": {"password": "123", "role": "Utility Technician", "name": "JITENDRA RAM (Tech)", "jc": "Shillong"},
    "tech5": {"password": "123", "role": "Utility Technician", "name": "Mahesh Barman (Tech)", "jc": "Shillong"},
    "tech6": {"password": "123", "role": "Utility Technician", "name": "ANDLEBERT SHANGPLIANG (Tech)", "jc": "Shillong"},
    "tech7": {"password": "123", "role": "Utility Technician", "name": "Tyngshainlong kharjana (Tech)", "jc": "Shillong"},
    "tech8": {"password": "123", "role": "Utility Technician", "name": "Bankynsia Mukhim (Tech)", "jc": "Shillong"},
    "tech9": {"password": "123", "role": "Utility Technician", "name": "BANTEILANG LYNGDOH (Tech)", "jc": "Shillong"},
    "tech10": {"password": "123", "role": "Utility Technician", "name": "WILLGEORGE SHIJI MARNGAR (Tech)", "jc": "Shillong"},
    "tech11": {"password": "123", "role": "Utility Technician", "name": "Dapkupar Marngar (Tech)", "jc": "Shillong"},
    "tech12": {"password": "123", "role": "Utility Technician", "name": "DONLAD DORPHANG (Tech)", "jc": "Shillong"},
    "tech13": {"password": "123", "role": "Utility Technician", "name": "HABANJOP WANKHAR (Tech)", "jc": "Shillong"},
    "tech14": {"password": "123", "role": "Utility Technician", "name": "JELIUS L MARSHILONG (Tech)", "jc": "Shillong"},
    "tech15": {"password": "123", "role": "Utility Technician", "name": "KRISEN NONGSPUNG (Tech)", "jc": "Shillong"},
    "tech16": {"password": "123", "role": "Utility Technician", "name": "JIAD ALI (Tech)", "jc": "Shillong"},
    "tech17": {"password": "123", "role": "Utility Technician", "name": "Kharawbor Sylliong (Tech)", "jc": "Shillong"},
    "tech18": {"password": "123", "role": "Utility Technician", "name": "TAUFIKAR RAHMAN (Tech)", "jc": "Shillong"},
    "tech19": {"password": "123", "role": "Utility Technician", "name": "KITBOKLANG DORPHANG (Tech)", "jc": "Shillong"},
    "tech20": {"password": "123", "role": "Utility Technician", "name": "LAINEH JUNOM LAKHIT (Tech)", "jc": "Shillong"},
    "tech21": {"password": "123", "role": "Utility Technician", "name": "LOTSTARJUNE NONGSIEJ (Tech)", "jc": "Shillong"},
    "tech22": {"password": "123", "role": "Utility Technician", "name": "Mathaius Iawrod (Tech)", "jc": "Shillong"},
    "tech23": {"password": "123", "role": "Utility Technician", "name": "MELVIN PYNGROPE (Tech)", "jc": "Shillong"},
    "tech24": {"password": "123", "role": "Utility Technician", "name": "PYNSHAI MASHARING (Tech)", "jc": "Shillong"},
    "tech25": {"password": "123", "role": "Utility Technician", "name": "TEIBORLIN THYRNIANG (Tech)", "jc": "Shillong"},
    "tech26": {"password": "123", "role": "Utility Technician", "name": "SARANGA PANI SAIKIA (Tech)", "jc": "Shillong"},
    "tech27": {"password": "123", "role": "Utility Technician", "name": "UTPAL GOHAIN (Tech)", "jc": "Shillong"},
    "tech28": {"password": "123", "role": "Utility Technician", "name": "Wahidur Rahman (Tech)", "jc": "Shillong"},

    # Jowai JC
    "tech29": {"password": "123", "role": "Utility Technician", "name": "RICHARD SUMER (Tech)", "jc": "Jowai"},
    "tech30": {"password": "123", "role": "Utility Technician", "name": "ORLANDO SANGMA (Tech)", "jc": "Jowai"},
    "tech31": {"password": "123", "role": "Utility Technician", "name": "SHANDIP SYLLIANG (Tech)", "jc": "Jowai"},
    "tech32": {"password": "123", "role": "Utility Technician", "name": "SHOHIDUL ISLAM (Tech)", "jc": "Jowai"},
    "tech33": {"password": "123", "role": "Utility Technician", "name": "Chibor Muksor (Tech)", "jc": "Jowai"},
    "tech34": {"password": "123", "role": "Utility Technician", "name": "Karmilus Bamon (Tech)", "jc": "Jowai"},
    "tech35": {"password": "123", "role": "Utility Technician", "name": "Ansar Ahmed Barbhuiya (Tech)", "jc": "Jowai"},
    "tech36": {"password": "123", "role": "Utility Technician", "name": "Bob Taney (Tech)", "jc": "Jowai"},
    "tech37": {"password": "123", "role": "Utility Technician", "name": "MOUCHAM ALI AHMED (Tech)", "jc": "Jowai"},
    "tech38": {"password": "123", "role": "Utility Technician", "name": "WAIDUL HAQUE MAJUMDER (Tech)", "jc": "Jowai"},

    # Tura JC
    "tech39": {"password": "123", "role": "Utility Technician", "name": "Anupam Kumer shing (Tech)", "jc": "Tura"},
    "tech40": {"password": "123", "role": "Utility Technician", "name": "Jul Hussain (Tech)", "jc": "Tura"},
    "tech41": {"password": "123", "role": "Utility Technician", "name": "SHARIFUL ISLAM (Tech)", "jc": "Tura"},
    "tech42": {"password": "123", "role": "Utility Technician", "name": "AMINUL ISLAM (Tech)", "jc": "Tura"},
    "tech43": {"password": "123", "role": "Utility Technician", "name": "Md Rizwan (Tech)", "jc": "Tura"},
    "tech44": {"password": "123", "role": "Utility Technician", "name": "AMRESH KUMAR (Tech)", "jc": "Tura"},
    "tech45": {"password": "123", "role": "Utility Technician", "name": "Hazrat Ali (Tech)", "jc": "Tura"},
    "tech46": {"password": "123", "role": "Utility Technician", "name": "Avinash Kumar (Tech)", "jc": "Tura"},
    "tech47": {"password": "123", "role": "Utility Technician", "name": "ANURAG KUMAR (Tech)", "jc": "Tura"},
    "tech48": {"password": "123", "role": "Utility Technician", "name": "Md Tazirul Islam (Tech)", "jc": "Tura"},
    "tech49": {"password": "123", "role": "Utility Technician", "name": "Manseng Marak (Tech)", "jc": "Tura"},
    "tech50": {"password": "123", "role": "Utility Technician", "name": "Babidul Islam (Tech)", "jc": "Tura"},
    "tech51": {"password": "123", "role": "Utility Technician", "name": "BRINDABON HAJONG (Tech)", "jc": "Tura"},
    "tech52": {"password": "123", "role": "Utility Technician", "name": "GAGANJYOTI DAS (Tech)", "jc": "Tura"},
    "tech53": {"password": "123", "role": "Utility Technician", "name": "Golap Rabbani (Tech)", "jc": "Tura"},
    "tech54": {"password": "123", "role": "Utility Technician", "name": "HAKIBUL ISLAM (Tech)", "jc": "Tura"},
    "tech55": {"password": "123", "role": "Utility Technician", "name": "Sengjal D Sangma (Tech)", "jc": "Tura"},
    "tech56": {"password": "123", "role": "Utility Technician", "name": "NAMSRANG R SANGMA (Tech)", "jc": "Tura"},
    "tech57": {"password": "123", "role": "Utility Technician", "name": "NAZRUL AHMED (Tech)", "jc": "Tura"},
    "tech58": {"password": "123", "role": "Utility Technician", "name": "Ashutosh kumar (Tech)", "jc": "Tura"},
    "tech59": {"password": "123", "role": "Utility Technician", "name": "Santosh Kumar Yadav (Tech)", "jc": "Tura"},
    "tech60": {"password": "123", "role": "Utility Technician", "name": "SENGBA G SANGMA (Tech)", "jc": "Tura"},
    "tech61": {"password": "123", "role": "Utility Technician", "name": "Shanjibul Ahmed (Tech)", "jc": "Tura"},
    "tech62": {"password": "123", "role": "Utility Technician", "name": "VIKASH KUMAR (Tech)", "jc": "Tura"},
    "tech63": {"password": "123", "role": "Utility Technician", "name": "Walseng B Marak (Tech)", "jc": "Tura"},
    "tech64": {"password": "123", "role": "Utility Technician", "name": "Zeaul Hoque (Tech)", "jc": "Tura"},

    # UT Supervisors
    "utsup1": {"password": "2026", "role": "UT Supervisor", "name": "Wellbertstar Jaba (UT Sup)", "jc": "Shillong"},
    "utsup2": {"password": "2026", "role": "UT Supervisor", "name": "Binay Ray (UT Sup)", "jc": "Jowai"},
    "utsup3": {"password": "2026", "role": "UT Supervisor", "name": "Maynal Haque (UT Sup)", "jc": "Tura"},
    "utsup4": {"password": "2026", "role": "UT Supervisor", "name": "Mojib Kumar Saikia (UT Sup)", "jc": "Tura"},

    # Service Managers
    "manager1": {"password": "2026", "role": "Service Manager", "name": "Ajay Sharma (SM)", "jc": "Shillong"},
    "manager2": {"password": "2026", "role": "Service Manager", "name": "Rakesh Ahmed (SM)", "jc": "Tura"},
    "manager3": {"password": "2026", "role": "Service Manager", "name": "Saharul (SM)", "jc": "Jowai"},

    # Docket Desk
    "docket": {"password": "2027", "role": "Docket Team", "name": "Docket Desk"},

    # Service Engineers
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

ENGINEERS_LIST = {u: USERS[u]['name'] for u in USERS if USERS[u]["role"] == "Service Engineer"}
MANAGERS_LIST = {u: USERS[u]['name'] for u in USERS if USERS[u]["role"] == "Service Manager"}
JC_LIST = ["Tura", "Shillong", "Jowai"]

def save_image_buffer(image_buffer, prefix, user_or_ticket):
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
    if not file_list:
        return ""
    saved_paths = []
    for idx, f in enumerate(file_list):
        path = save_image_buffer(f, f"{prefix}_{idx+1}", ticket_id)
        if path:
            saved_paths.append(path)
    return ",".join(saved_paths)

def display_images_gallery(paths_str, caption_title):
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
        clean_str = str(dt_val).split(".")[0]
        dt_obj = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
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

    # ----------------- PUBLIC LIVE TT SUMMARY ON LOGIN PAGE -----------------
    st.divider()
    st.subheader("📊 Live DG Fault Tracker & Project Overview (Public View)")

    public_rows = load_all_faults()
    pub_total = len(public_rows)
    pub_pending_sm = sum(1 for r in public_rows if r[4] == 'PENDING_SM')
    pub_in_prog = sum(1 for r in public_rows if r[4] in ['PENDING_DOCKET', 'ASSIGNED_ENG', 'PENDING_UT_VERIFY', 'PENDING_UT_SUP_VERIFY'])
    pub_closed = sum(1 for r in public_rows if r[4] == 'CLOSED')

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tickets", pub_total)
    k2.metric("Pending SM Approval", pub_pending_sm)
    k3.metric("Under Rectification", pub_in_prog)
    k4.metric("Total Closed", pub_closed)

else:
    current_username = st.session_state.username
    user = st.session_state.user_info
    role = user["role"]
    user_selfie = st.session_state.login_selfie_path
    user_loc = st.session_state.login_location

    col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
    with col_t1:
        st.title("⚡ DG Fault Management Portal")
        jc_badge = f" | Assigned/Supervised JC: **{user.get('jc')}**" if user.get('jc') else ""
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

    # 1. Utility Technician Fault Logging Form (Auto-Selected & Locked JC)
    if role == "Utility Technician":
        st.subheader("Log New DG Fault Request")
        user_assigned_jc = user.get("jc", "Shillong")

        with st.form("new_fault_form"):
            c_site, c_jc = st.columns([2, 1])
            with c_site:
                site = st.text_input("Site ID (e.g. GUW-10)")
            with c_jc:
                jc_index = JC_LIST.index(user_assigned_jc) if user_assigned_jc in JC_LIST else 0
                selected_jc = st.selectbox("Job Centre (JC)", JC_LIST, index=jc_index, disabled=True)
            
            c_mob, c_dg1, c_dg2 = st.columns([1.5, 1, 1])
            with c_mob:
                contact_mobile = st.text_input("Contact Mobile Number (10 digits)", max_chars=10, help="Enter active 10-digit mobile number")
            with c_dg1:
                dg_make = st.selectbox("DG Make", ["Kirloskar", "Mahindra", "Eicher"])
            with c_dg2:
                dg_rating = st.selectbox("DG Rating (kVA)", ["10 kVA", "15 kVA", "20 kVA", "25 kVA", "30 kVA", "125 kVA"])

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
            fault_imgs = st.file_uploader("Upload Fault Photos (Multiple allowed)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
            submit = st.form_submit_button("Submit Fault Request")

            if submit:
                clean_mobile = contact_mobile.strip()
                if not (site and desc and clean_mobile):
                    st.error("Site ID, Mobile Number, and Fault Remarks are strictly required!")
                elif not (clean_mobile.isdigit() and len(clean_mobile) == 10):
                    st.error("Please enter a valid 10-digit mobile number without spaces or country code.")
                else:
                    if selected_support_person == "Other (Mention name below)":
                        support_final_name = custom_person_name.strip() if custom_person_name.strip() else "Other Person"
                    else:
                        support_final_name = selected_support_person

                    all_current_rows = load_all_faults()
                    new_id = f"TKT-{len(all_current_rows) + 101}"
                    photo_paths = save_multiple_images(fault_imgs, "fault", new_id)

                    site_with_jc = f"{site} [{selected_jc}]"
                    dg_combined = f"{dg_make} ({dg_rating})"
                    now_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")

                    full_desc = (
                        f"{desc}\n\n"
                        f"📞 Online Support: {support_final_name}\n"
                        f"💡 Support Guidance: {online_sup_remarks if online_sup_remarks else 'N/A'}"
                    )

                    row_payload = [
                        new_id, site_with_jc, dg_combined, full_desc, 'PENDING_SM', '', '', 
                        current_username, clean_mobile, user_selfie, user_loc, 
                        '', '', '', photo_paths, '', now_time, ''
                    ]
                    success = add_fault_to_sheet(row_payload)

                    if success:
                        photo_count = len(fault_imgs) if fault_imgs else 0
                        tg_msg = (
                            f"🚨 *New DG Fault Logged!*\n\n"
                            f"📌 *Ticket ID:* `{new_id}`\n"
                            f"🏢 *Site ID:* {site}\n"
                            f"📍 *JC:* {selected_jc}\n"
                            f"🏭 *DG:* {dg_make} ({dg_rating})\n"
                            f"📱 *Contact No:* [{clean_mobile}](tel:{clean_mobile})\n"
                            f"📞 *Online Support:* {support_final_name}\n"
                            f"💡 *Support Guidance:* {online_sup_remarks if online_sup_remarks else 'N/A'}\n"
                            f"📝 *Fault Remarks:* {desc}\n"
                            f"📷 *Photos Uploaded:* {photo_count}\n"
                            f"👤 *Logged by:* {user['name']} (📞 {clean_mobile})\n"
                            f"🕒 *Date & Time (IST):* {format_dt(now_time)}"
                        )
                        send_telegram_alert(tg_msg)
                        st.success(f"Fault ticket {new_id} saved to database! Telegram notification sent.")
                        st.rerun()

        st.divider()

    # =========================================================================
    # 1. TOTAL DASHBOARD (Project Overview - Visible to All)
    # =========================================================================
    st.subheader("📊 Live DG Fault Tracker & Project Overview (Total Dashboard)")

    all_rows = load_all_faults()

    total_count = len(all_rows)
    pending_sm_count = sum(1 for r in all_rows if str(r[4]).strip() == 'PENDING_SM')
    in_progress_count = sum(1 for r in all_rows if str(r[4]).strip() in ['PENDING_DOCKET', 'ASSIGNED_ENG', 'PENDING_UT_VERIFY', 'PENDING_UT_SUP_VERIFY'])
    closed_count = sum(1 for r in all_rows if str(r[4]).strip() == 'CLOSED')

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Tickets", total_count)
    kpi2.metric("Pending SM Approval", pending_sm_count)
    kpi3.metric("Under Rectification", in_progress_count)
    kpi4.metric("Total Closed", closed_count)

    # TRT Aging & Date-wise Project Summary Calculation
    analytics_rows = []
    normal_trt_count = 0
    warning_trt_count = 0
    critical_trt_count = 0

    for r in all_rows:
        t_id, t_site, t_status = r[0], r[1], r[4]
        t_created, t_closed = r[16], r[17]

        t_jc = "Unknown"
        for jc_opt in JC_LIST:
            if f"[{jc_opt}]" in t_site:
                t_jc = jc_opt
                break

        trt_str, trt_cat, _ = calculate_trt(t_created, t_closed)
        if trt_cat == "Normal (< 24h)":
            normal_trt_count += 1
        elif trt_cat == "Warning (24-48h)":
            warning_trt_count += 1
        elif trt_cat == "Critical (> 48h)":
            critical_trt_count += 1

        analytics_rows.append({
            "Ticket ID": t_id,
            "JC": t_jc,
            "Log Date": str(t_created).split(" ")[0] if t_created else "N/A",
            "Close Date": str(t_closed).split(" ")[0] if t_closed else "N/A",
            "Status": t_status,
            "TRT Category": trt_cat
        })

    # Aging Overview Bar
    st.write("---")
    st.markdown("##### ⏳ Overall TRT Aging Summary (All Tickets)")
    ag1, ag2, ag3 = st.columns(3)
    ag1.metric("🟢 Normal (< 24h)", normal_trt_count)
    ag2.metric("🟡 Warning (24-48h)", warning_trt_count)
    ag3.metric("🔴 Critical (> 48h)", critical_trt_count)

    # Date-wise & JC-wise Breakdown Table
    if analytics_rows:
        df_all = pd.DataFrame(analytics_rows)
        dates_list = sorted(list(set(df_all["Log Date"].unique()) - {"N/A"}), reverse=True)

        summary_records = []
        for d in dates_list:
            d_df = df_all[df_all["Log Date"] == d]
            for jc in JC_LIST:
                jc_df = d_df[d_df["JC"] == jc]
                t_log = len(jc_df)
                if t_log > 0:
                    summary_records.append({
                        "Date": d,
                        "Job Centre (JC)": jc,
                        "Log Date Total": t_log,
                        "Approved": len(jc_df[~jc_df["Status"].isin(["PENDING_SM", "REJECTED"])]),
                        "Pending SM": len(jc_df[jc_df["Status"] == "PENDING_SM"]),
                        "Rejected": len(jc_df[jc_df["Status"] == "REJECTED"]),
                        "Closed on Date": len(df_all[(df_all["Close Date"] == d) & (df_all["JC"] == jc) & (df_all["Status"] == "CLOSED")])
                    })

        if summary_records:
            with st.expander("📈 View Date-wise & JC-wise Project Breakdown Table", expanded=False):
                st.dataframe(pd.DataFrame(summary_records), use_container_width=True)

    st.divider()

    # =========================================================================
    # 2. USER'S OWN CASES (Actionable Cases & Action Cards)
    # =========================================================================
    st.subheader(f"📌 My Actionable Cases ({user['name']})")

    now_ist_dt = get_ist_now().replace(tzinfo=None)
    retention_limit_days = 30

    my_cases = []
    for r in all_rows:
        t_id = str(r[0]).strip()
        t_site = str(r[1]).strip()
        t_status = str(r[4]).strip()
        t_docket = str(r[5]).strip()
        t_eng = str(r[6]).strip()
        t_logged_by = str(r[7]).strip()
        t_created = str(r[16]).strip()
        t_closed = str(r[17]).strip()

        # Job Centre (JC) Identification
        t_jc = "Unknown"
        for jc_opt in JC_LIST:
            if f"[{jc_opt}]" in t_site:
                t_jc = jc_opt
                break

        # Role-based User Filtering
        is_my_case = False

        if role == "Utility Technician":
            # Technician: Own created tickets (Open + Closed within 30 days)
            if t_logged_by == current_username:
                if t_status != "CLOSED":
                    is_my_case = True
                elif t_closed:
                    try:
                        c_dt = datetime.strptime(t_closed.split(".")[0], "%Y-%m-%d %H:%M:%S")
                        if (now_ist_dt - c_dt).days <= retention_limit_days:
                            is_my_case = True
                    except Exception:
                        pass

        elif role == "Service Engineer":
            # Service Engineer: ONLY OPEN CASES assigned to this engineer
            if t_eng == current_username and t_status != "CLOSED":
                is_my_case = True

        elif role == "UT Supervisor":
            # UT Supervisor: Tickets in supervised JC (Open + Closed within 30 days)
            sup_jc = user.get("jc", "")
            if (sup_jc == "All") or (t_jc == sup_jc):
                if t_status != "CLOSED":
                    is_my_case = True
                elif t_closed:
                    try:
                        c_dt = datetime.strptime(t_closed.split(".")[0], "%Y-%m-%d %H:%M:%S")
                        if (now_ist_dt - c_dt).days <= retention_limit_days:
                            is_my_case = True
                    except Exception:
                        pass

        elif role in ["Service Manager", "Data Analysis"]:
            # Service Manager & Data Analysis: Tickets in supervised JC (All for Central Supervisor)
            mgr_jc = user.get("jc", "")
            if (mgr_jc == "All") or (t_jc == mgr_jc):
                if t_status != "CLOSED":
                    is_my_case = True
                elif t_closed:
                    try:
                        c_dt = datetime.strptime(t_closed.split(".")[0], "%Y-%m-%d %H:%M:%S")
                        if (now_ist_dt - c_dt).days <= retention_limit_days:
                            is_my_case = True
                    except Exception:
                        pass

        elif role == "Docket Team":
            # Docket Desk: Tickets needing assignment or actively in progress
            if t_status in ["PENDING_DOCKET", "ASSIGNED_ENG", "PENDING_UT_VERIFY", "PENDING_UT_SUP_VERIFY"]:
                is_my_case = True

        if is_my_case:
            trt_str, trt_cat, trt_hours = calculate_trt(t_created, t_closed)
            my_cases.append((r, t_jc, trt_str, trt_cat))

    # ----------------- MY TICKETS MASTER TABLE -----------------
    st.markdown("### 📋 My Tickets Master Table")
    st.caption(f"Showing **{len(my_cases)}** active or recently closed tickets assigned to or created by you")

    if my_cases:
        table_data = []
        for item in reversed(my_cases):
            r, t_jc, trt_str, trt_cat = item
            (t_id, t_site, t_dg, t_desc, t_status, t_docket, t_eng, t_logged_by, 
             t_mobile, t_l_selfie, t_l_loc, t_act_selfie, t_act_loc, t_rect, 
             t_fphoto, t_rphoto, t_created_at, t_closed_at) = r

            eng_name = USERS.get(t_eng, {}).get("name", t_eng) if t_eng else "Not Assigned"
            tech_name = USERS.get(t_logged_by, {}).get("name", t_logged_by)

            table_data.append({
                "Ticket ID": t_id,
                "Site ID & JC": t_site,
                "DG Rating": t_dg,
                "Status": t_status,
                "TRT Aging": trt_str,
                "TRT Category": trt_cat,
                "Logged By (Tech)": f"{tech_name} ({t_mobile})",
                "Docket No": t_docket if t_docket else "-",
                "Assigned Engineer": eng_name,
                "Created At (IST)": format_dt(t_created_at),
                "Closed At (IST)": format_dt(t_closed_at) if t_closed_at else "-"
            })

        master_df = pd.DataFrame(table_data)
        st.dataframe(master_df, use_container_width=True, hide_index=True)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            master_df.to_excel(writer, index=False, sheet_name="My_Tickets")
        st.download_button(
            label="📥 Download My Tickets Report (Excel)",
            data=excel_buffer.getvalue(),
            file_name=f"My_Tickets_{get_ist_now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("No active tickets found matching your user account.")

    # ----------------- DETAILED TICKET ACTION CARDS (USER'S CASES ONLY) -----------------
    st.write("---")
    st.subheader("🔍 Ticket Action & Individual Details")

    for item in reversed(my_cases):
        r, ticket_jc, trt_str, trt_cat = item
        (t_id, t_site, t_dg, t_desc, t_status, t_docket, t_eng, t_logged_by, 
         t_mobile, t_l_selfie, t_l_loc, t_act_selfie, t_act_loc, t_rect, t_fphoto, t_rphoto, 
         t_created_at, t_closed_at) = r

        created_str = format_dt(t_created_at)
        closed_str = format_dt(t_closed_at)

        if "Normal" in trt_cat:
            trt_badge = f"🟢 TRT: {trt_str}"
        elif "Warning" in trt_cat:
            trt_badge = f"🟡 TRT: {trt_str}"
        else:
            trt_badge = f"🔴 TRT: {trt_str} (Critical)"

        with st.expander(f"{t_id} | {t_site} - {t_dg} | [{t_status}] | {trt_badge} 📅 {created_str}", expanded=(t_status != 'CLOSED')):
            c_meta1, c_meta2, c_meta3 = st.columns(3)
            with c_meta1:
                st.write(f"🕒 **Logged Date (IST):** {created_str}")
            with c_meta2:
                if t_status == "CLOSED" and closed_str:
                    st.write(f"✅ **Closed Date (IST):** {closed_str}")
                else:
                    st.write(f"⏱️ **Active Elapsed TRT:** **{trt_str}**")
            with c_meta3:
                st.write(f"🏷️ **TRT Category:** {trt_cat}")

            st.write(f"**Fault Details & Online Support:**")
            st.info(t_desc)
            
            c_info1, c_info2 = st.columns([3, 1])
            with c_info1:
                creator_name = USERS.get(t_logged_by, {}).get('name', t_logged_by)
                mob_link = f" | 📱 [**Call {t_mobile}**](tel:{t_mobile})" if t_mobile else ""
                st.markdown(f"Logged by: **{creator_name}** ({t_logged_by}){mob_link} | JC: **{ticket_jc}**")
                if t_l_loc:
                    st.markdown(f"📍 [View Creator GPS Location]({t_l_loc})")
            with c_info2:
                if t_l_selfie and os.path.exists(t_l_selfie):
                    st.image(t_l_selfie, caption="Logged Selfie", width=80)

            display_images_gallery(t_fphoto, "Fault Photos")

            if t_docket:
                eng_info = USERS.get(t_eng, {})
                eng_name = eng_info.get("name", t_eng)
                st.markdown(f"Docket No: **{t_docket}** | Assigned Engineer: **{eng_name}**")

            if t_rect:
                st.warning(f"Rectification Notes: {t_rect}")

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

            # ----------------- SERVICE MANAGER APPROVAL -----------------
            if role == "Service Manager" and t_status == "PENDING_SM":
                manager_jc = user.get("jc", "")
                is_authorized = (manager_jc == "All") or (ticket_jc == manager_jc)

                if is_authorized:
                    st.success(f"✔️ You hold approval authority for **{ticket_jc} JC** | Elapsed TRT: **{trt_str}**")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve", key=f"sm_app_{t_id}"):
                        update_fault_in_sheet(t_id, {
                            "status": "PENDING_DOCKET",
                            "action_by_selfie": user_selfie,
                            "action_by_loc": user_loc
                        })
                        send_telegram_alert(
                            f"✅ Fault APPROVED by SM\nTicket: {t_id}\nJC: {ticket_jc}\nTRT at Approval: {trt_str}\nManager: {user['name']}\nStatus: PENDING DOCKET"
                        )
                        st.rerun()
                    if c2.button("❌ Reject", key=f"sm_rej_{t_id}"):
                        update_fault_in_sheet(t_id, {
                            "status": "REJECTED",
                            "action_by_selfie": user_selfie,
                            "action_by_loc": user_loc
                        })
                        send_telegram_alert(
                            f"❌ Fault REJECTED by SM\nTicket: {t_id}\nJC: {ticket_jc}\nTRT at Rejection: {trt_str}\nManager: {user['name']}"
                        )
                        st.rerun()
                else:
                    assigned_sm_name = "Assigned SM"
                    for u in USERS.values():
                        if u.get("role") == "Service Manager" and u.get("jc") == ticket_jc:
                            assigned_sm_name = u.get("name")
                            break
                    st.warning(f"🔒 Ticket belongs to **{ticket_jc} JC**. Only **{assigned_sm_name}** or the **Central Supervisor** can approve/reject.")

            # ----------------- DOCKET ASSIGNMENT -----------------
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
                        update_fault_in_sheet(t_id, {
                            "docket": d_no,
                            "assigned_eng": selected_eng,
                            "status": "ASSIGNED_ENG"
                        })
                        eng_name = ENGINEERS_LIST[selected_eng]
                        send_telegram_alert(f"📋 Docket Assigned\nTicket: {t_id}\nJC: {ticket_jc}\nTRT: {trt_str}\nDocket No: {d_no}\nAssigned Engineer: {eng_name}")
                        st.rerun()
                    else:
                        st.error("Please enter a Docket Number.")

            # ----------------- ENGINEER WORK RECTIFICATION -----------------
            elif role == "Service Engineer" and t_status == "ASSIGNED_ENG":
                if t_eng == current_username:
                    st.success("🔧 This ticket is assigned to you:")
                    notes = st.text_area("Work Done / Rectification Notes", key=f"eng_in_{t_id}")
                    rect_imgs = st.file_uploader("Upload Post-Work Photos (Multiple allowed)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"eng_img_{t_id}")
                    
                    if st.button("Request Close", key=f"eng_btn_{t_id}"):
                        if notes:
                            rect_photo_paths = save_multiple_images(rect_imgs, "rect", t_id)
                            update_fault_in_sheet(t_id, {
                                "rectification": notes,
                                "rect_photo": rect_photo_paths,
                                "status": "PENDING_UT_VERIFY",
                                "action_by_selfie": user_selfie,
                                "action_by_loc": user_loc
                            })
                            rect_count = len(rect_imgs) if rect_imgs else 0
                            send_telegram_alert(f"🔧 Work Completed by Engineer\nTicket: {t_id}\nJC: {ticket_jc}\nTRT: {trt_str}\nEngineer: {user['name']}\nWork Photos: {rect_count}\nStatus: PENDING UT VERIFICATION")
                            st.rerun()
                        else:
                            st.error("Rectification notes are mandatory!")
                else:
                    assigned_name = USERS.get(t_eng, {}).get("name", t_eng)
                    st.info(f"🔒 This ticket is assigned to **{assigned_name}**.")

            # ----------------- 5. UTILITY TECH VERIFICATION -----------------
            elif role == "Utility Technician" and t_status == "PENDING_UT_VERIFY":
                if t_logged_by == current_username:
                    st.write("🔍 *You logged this ticket. Please verify work done and forward to UT Supervisor:*")
                    c1, c2 = st.columns(2)
                    if c1.button("Approve & Forward to UT Supervisor", key=f"ut_app_{t_id}"):
                        update_fault_in_sheet(t_id, {
                            "status": "PENDING_UT_SUP_VERIFY",
                            "action_by_selfie": user_selfie,
                            "action_by_loc": user_loc
                        })
                        send_telegram_alert(
                            f"✅ *UT Verified & Forwarded*\n"
                            f"Ticket: `{t_id}`\nJC: {ticket_jc}\n"
                            f"TRT: {trt_str}\n"
                            f"Verified By UT: {user['name']}\n"
                            f"Status: PENDING UT SUPERVISOR FINAL APPROVAL"
                        )
                        st.rerun()
                    if c2.button("Reject (Re-assign to Engineer)", key=f"ut_rej_{t_id}"):
                        update_fault_in_sheet(t_id, {"status": "ASSIGNED_ENG"})
                        send_telegram_alert(f"⚠️ Ticket Rejected by UT\nTicket: {t_id}\nJC: {ticket_jc}\nRe-opened for Engineer.")
                        st.rerun()
                else:
                    creator_name = USERS.get(t_logged_by, {}).get("name", t_logged_by)
                    st.warning(f"🔒 This fault was logged by **{creator_name}**. Only the creator can verify.")

            # ----------------- 6. UT SUPERVISOR FINAL APPROVAL & CLOSURE -----------------
            elif role == "UT Supervisor" and t_status == "PENDING_UT_SUP_VERIFY":
                sup_jc = user.get("jc", "")
                is_authorized = (sup_jc == "All") or (ticket_jc == sup_jc)

                if is_authorized:
                    st.success(f"🛡️ **Final UT Supervisor Approval Authority for {ticket_jc} JC**")
                    c_sup1, c_sup2 = st.columns(2)
                    if c_sup1.button("🏆 Final Approve & Close Ticket", key=f"sup_app_{t_id}"):
                        now_close = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
                        update_fault_in_sheet(t_id, {
                            "status": "CLOSED",
                            "closed_at": now_close,
                            "action_by_selfie": user_selfie,
                            "action_by_loc": user_loc
                        })
                        send_telegram_alert(
                            f"🎉 *Ticket CLOSED (Final Approval by UT Supervisor)*\n\n"
                            f"📌 *Ticket ID:* `{t_id}`\n"
                            f"📍 *JC:* {ticket_jc}\n"
                            f"⏱️ *Total Resolution TRT:* {trt_str}\n"
                            f"👤 *Final Closed by UT Sup:* {user['name']}\n"
                            f"🕒 *Closed At:* {format_dt(now_close)}"
                        )
                        st.rerun()
                    if c_sup2.button("❌ Reject back to Engineer", key=f"sup_rej_{t_id}"):
                        update_fault_in_sheet(t_id, {"status": "ASSIGNED_ENG"})
                        send_telegram_alert(
                            f"⚠️ Final Approval Rejected by UT Sup\n"
                            f"Ticket: {t_id}\nJC: {ticket_jc}\n"
                            f"Rejected by: {user['name']}\n"
                            f"Status: Re-assigned to Engineer"
                        )
                        st.rerun()
                else:
                    st.warning(f"🔒 This ticket belongs to **{ticket_jc} JC**. Only **{ticket_jc} UT Supervisor** can grant final closure.")
