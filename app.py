import streamlit as st
import os
import requests
import pytz
import pandas as pd
import io
import re
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="DG Fault Portal", layout="wide")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- GOOGLE APPS SCRIPT WEB APP CONNECTION -----------------
# তলত আপোনাৰ Google Sheet Apps Script Deploy কৰি পোৱা Web App URL টো বহুৱাওক:
SHEET_API_URL = "https://script.google.com/macros/s/AKfycbxYOUR_DEPLOYED_SCRIPT_ID/exec"

SHEET_HEADERS = [
    "id", "site", "dg", "desc", "status", "docket", "assigned_eng",
    "logged_by", "mobile", "logged_by_selfie", "logged_by_loc", "action_by_selfie",
    "action_by_loc", "rectification", "fault_photo", "rect_photo",
    "created_at", "closed_at"
]

def load_all_faults():
    try:
        res = requests.get(SHEET_API_URL, timeout=12)
        records = res.json()
        rows = []
        for r in records:
            rows.append([
                str(r.get("id", "")),
                str(r.get("site", "")),
                str(r.get("dg", "")),
                str(r.get("desc", "")),
                str(r.get("status", "")),
                str(r.get("docket", "")),
                str(r.get("assigned_eng", "")),
                str(r.get("logged_by", "")),
                str(r.get("mobile", "")),
                str(r.get("logged_by_selfie", "")),
                str(r.get("logged_by_loc", "")),
                str(r.get("action_by_selfie", "")),
                str(r.get("action_by_loc", "")),
                str(r.get("rectification", "")),
                str(r.get("fault_photo", "")),
                str(r.get("rect_photo", "")),
                str(r.get("created_at", "")),
                str(r.get("closed_at", ""))
            ])
        return rows
    except Exception as e:
        return []

def add_fault_to_sheet(row_data):
    try:
        res = requests.post(SHEET_API_URL, json={"action": "append", "row": row_data}, timeout=12)
        return True
    except Exception as e:
        st.error(f"Google Sheet-ত ডাটা লিখোঁতে সমস্যা হৈছে: {e}")
        return False

def update_fault_in_sheet(ticket_id, updates_dict):
    try:
        res = requests.post(SHEET_API_URL, json={"action": "update", "id": ticket_id, "updates": updates_dict}, timeout=12)
        return True
    except Exception as e:
        st.error(f"Sheet আপডেট কৰোঁতে সমস্যা হৈছে: {e}")
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
    "admin": {"password": "admin", "role": "Service Manager", "name": "Central Supervisor (All JC)", "jc": "All", "phone": "9876543210"},
    "tech1": {"password": "123", "role": "Utility Technician", "name": "Anupam Kumer Shing (Tech)", "phone": "9864011111"},
    "tech2": {"password": "123", "role": "Utility Technician", "name": "Jul Hussain (Tech)", "phone": "9864022222"},
    "tech3": {"password": "123", "role": "Utility Technician", "name": "Shariful Islam (Tech)", "phone": "9864033333"},
    "tech4": {"password": "123", "role": "Utility Technician", "name": "Aminul Islam (Tech)", "phone": "9864044444"},
    "tech5": {"password": "123", "role": "Utility Technician", "name": "Md Rizwan (Tech)", "phone": "9864055555"},
    "tech6": {"password": "123", "role": "Utility Technician", "name": "Amresh Kumar (Tech)", "phone": "9864066666"},
    "tech7": {"password": "123", "role": "Utility Technician", "name": "Hazrat Ali (Tech)", "phone": "9864077777"},
    "tech8": {"password": "123", "role": "Utility Technician", "name": "Avinash Kumar (Tech)", "phone": "9864088888"},
    "tech9": {"password": "123", "role": "Utility Technician", "name": "Anurag Kumar (Tech)", "phone": "9864099999"},
    "tech10": {"password": "123", "role": "Utility Technician", "name": "Md Tazirul Islam (Tech)", "phone": "9864100000"},
    "tech11": {"password": "123", "role": "Utility Technician", "name": "Manseng Marak (Tech)", "phone": "9864111111"},
    "tech12": {"password": "123", "role": "Utility Technician", "name": "Babidul Islam (Tech)", "phone": "9864122222"},
    "tech13": {"password": "123", "role": "Utility Technician", "name": "Brindabon Hajong (Tech)", "phone": "9864133333"},
    "tech14": {"password": "123", "role": "Utility Technician", "name": "Gaganjyoti Das (Tech)", "phone": "9864144444"},
    "tech15": {"password": "123", "role": "Utility Technician", "name": "Golap Rabbani (Tech)", "phone": "9864155555"},
    "tech16": {"password": "123", "role": "Utility Technician", "name": "Hakibul Islam (Tech)", "phone": "9864166666"},
    "tech17": {"password": "123", "role": "Utility Technician", "name": "Sengjal D Sangma (Tech)", "phone": "9864177777"},
    "tech18": {"password": "123", "role": "Utility Technician", "name": "Namsrang R Sangma (Tech)", "phone": "9864188888"},
    "tech19": {"password": "123", "role": "Utility Technician", "name": "Nazrul Ahmed (Tech)", "phone": "9864199999"},
    "tech20": {"password": "123", "role": "Utility Technician", "name": "Ashutosh Kumar (Tech)", "phone": "9864200000"},
    "tech21": {"password": "123", "role": "Utility Technician", "name": "Santosh Kumar Yadav (Tech)", "phone": "9864211111"},
    "tech22": {"password": "123", "role": "Utility Technician", "name": "Sengba G Sangma (Tech)", "phone": "9864222222"},
    "tech23": {"password": "123", "role": "Utility Technician", "name": "Shanjibul Ahmed (Tech)", "phone": "9864233333"},
    "tech24": {"password": "123", "role": "Utility Technician", "name": "Vikash Kumar (Tech)", "phone": "9864244444"},
    "tech25": {"password": "123", "role": "Utility Technician", "name": "Walseng B Marak (Tech)", "phone": "9864255555"},
    "tech26": {"password": "123", "role": "Utility Technician", "name": "Zeaul Hoque (Tech)", "phone": "9864266666"},
    "tech27": {"password": "123", "role": "Utility Technician", "name": "Dharamveer (Tech)", "phone": "9864277777"},
    "manager1": {"password": "2026", "role": "Service Manager", "name": "Ajay Sharma (SM)", "jc": "Shillong", "phone": "9435011111"},
    "manager2": {"password": "2026", "role": "Service Manager", "name": "Rakesh Ahmed (SM)", "jc": "Tura", "phone": "9435022222"},
    "manager3": {"password": "2026", "role": "Service Manager", "name": "Saharul (SM)", "jc": "Jowai", "phone": "9435033333"},
    "docket": {"password": "2027", "role": "Docket Team", "name": "Docket Desk", "phone": "9435044444"},
    "eng1": {"password": "124", "role": "Service Engineer", "name": "Harnual Roshid (Engineer)", "phone": "9706011111"},
    "eng2": {"password": "124", "role": "Service Engineer", "name": "Krishna Kanta Hazarika (Engineer)", "phone": "9706022222"},
    "eng3": {"password": "124", "role": "Service Engineer", "name": "Shaha Alom (Engineer)", "phone": "9706033333"},
    "eng4": {"password": "124", "role": "Service Engineer", "name": "Suman Kumar (Engineer)", "phone": "9706044444"},
    "eng5": {"password": "124", "role": "Service Engineer", "name": "Belikson Momin (Engineer)", "phone": "9706055555"},
    "eng6": {"password": "124", "role": "Service Engineer", "name": "Sengvear Momin (Engineer)", "phone": "9706066666"},
    "eng7": {"password": "124", "role": "Service Engineer", "name": "Ramij Ali (Engineer)", "phone": "9706077777"},
    "eng8": {"password": "124", "role": "Service Engineer", "name": "George Momin (Engineer)", "phone": "9706088888"},
    "eng9": {"password": "124", "role": "Service Engineer", "name": "Mofidul Islam (Engineer)", "phone": "9706099999"},
    "eng10": {"password": "124", "role": "Service Engineer", "name": "Binod Sangma (Engineer)", "phone": "9706100000"},
    "eng11": {"password": "124", "role": "Service Engineer", "name": "Rakibul Islam (Engineer)", "phone": "9706111111"},
    "eng12": {"password": "124", "role": "Service Engineer", "name": "Alexbirth Sangma (Engineer)", "phone": "9706122222"},
    "eng13": {"password": "124", "role": "Service Engineer", "name": "Habizul Rahman (Engineer)", "phone": "9706133333"},
    "eng14": {"password": "124", "role": "Service Engineer", "name": "Stebirth Sangma (Engineer)", "phone": "9706144444"},
    "eng15": {"password": "124", "role": "Service Engineer", "name": "Khairul Islam (Engineer)", "phone": "9706155555"}
}

ENGINEERS_LIST = {u: f"{USERS[u]['name']} (📞 {USERS[u]['phone']})" for u in USERS if USERS[u]["role"] == "Service Engineer"}
MANAGERS_LIST = {u: f"{USERS[u]['name']} (📞 {USERS[u]['phone']})" for u in USERS if USERS[u]["role"] == "Service Manager"}
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
    st.subheader("📊 Live DG Fault Tracker & TT Summary (Overview)")

    public_rows = load_all_faults()
    pub_total = len(public_rows)
    pub_pending_sm = sum(1 for r in public_rows if r[4] == 'PENDING_SM')
    pub_in_prog = sum(1 for r in public_rows if r[4] in ['PENDING_DOCKET', 'ASSIGNED_ENG', 'PENDING_UT_VERIFY'])
    pub_closed = sum(1 for r in public_rows if r[4] == 'CLOSED')

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tickets", pub_total)
    k2.metric("Pending SM Approval", pub_pending_sm)
    k3.metric("Under Rectification", pub_in_prog)
    k4.metric("Total Closed", pub_closed)

    # Date-wise & JC-wise Public Analytics Table
    analytics_rows = []
    for r in public_rows:
        t_id, t_site, t_status = r[0], r[1], r[4]
        t_created, t_closed = r[16], r[17]

        t_jc = "Unknown"
        for jc_opt in JC_LIST:
            if f"[{jc_opt}]" in t_site:
                t_jc = jc_opt
                break

        analytics_rows.append({
            "Ticket ID": t_id,
            "JC": t_jc,
            "Log Date": t_created.split(" ")[0] if t_created else "N/A",
            "Close Date": t_closed.split(" ")[0] if t_closed else "N/A",
            "Status": t_status
        })

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
            st.markdown("##### 📈 Date-wise & JC-wise Breakdown")
            st.dataframe(pd.DataFrame(summary_records), use_container_width=True)

else:
    current_username = st.session_state.username
    user = st.session_state.user_info
    role = user["role"]
    user_selfie = st.session_state.login_selfie_path
    user_loc = st.session_state.login_location

    col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
    with col_t1:
        st.title("⚡ DG Fault Portal")
        jc_badge = f" | Supervised JC: **{user.get('jc')}**" if user.get('jc') else ""
        mob_badge = f" | 📱 **{user.get('phone', '')}**"
        st.caption(f"Logged in: **{user['name']}** ({current_username}){mob_badge} | Role: **{role}**{jc_badge}")
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

    # 1. Utility Technician Form
    if role == "Utility Technician":
        st.subheader("Log New Fault Request")
        default_user_phone = user.get("phone", "")
        with st.form("new_fault_form"):
            c_site, c_jc = st.columns([2, 1])
            with c_site:
                site = st.text_input("Site ID (e.g. GUW-10)")
            with c_jc:
                selected_jc = st.selectbox("Job Centre (JC)", JC_LIST)
            
            c_mob, c_dg1, c_dg2 = st.columns([1.5, 1, 1])
            with c_mob:
                contact_mobile = st.text_input("Contact Mobile Number (10 digits)", value=default_user_phone, max_chars=10, help="Enter active 10-digit mobile number")
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
                        st.success(f"Fault ticket {new_id} saved to Google Sheets! Telegram notification sent.")
                        st.rerun()

        st.divider()

    # ----------------- CENTRAL OWNER & SUPERVISOR DASHBOARD -----------------
    st.subheader("📊 Fault Tracker & Performance Summary")

    all_rows = load_all_faults()

    total_count = len(all_rows)
    pending_sm_count = sum(1 for r in all_rows if r[4] == 'PENDING_SM')
    in_progress_count = sum(1 for r in all_rows if r[4] in ['PENDING_DOCKET', 'ASSIGNED_ENG', 'PENDING_UT_VERIFY'])
    closed_count = sum(1 for r in all_rows if r[4] == 'CLOSED')

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Tickets", total_count)
    kpi2.metric("Pending SM Approval", pending_sm_count)
    kpi3.metric("Under Rectification", in_progress_count)
    kpi4.metric("Total Closed", closed_count)

    # ----------------- FILTERS -----------------
    st.write("---")
    f_c1, f_c2, f_c3 = st.columns(3)
    with f_c1:
        trt_filter = st.selectbox(
            "⏳ Filter by TRT Aging:",
            ["All TRT", "🟢 Normal (< 24h)", "🟡 Warning (24-48h)", "🔴 Critical (> 48h)"]
        )
    with f_c2:
        jc_filter = st.selectbox("📍 Filter by Job Centre (JC):", ["All JCs"] + JC_LIST)
    with f_c3:
        sm_filter_list = ["All Managers", "Central Supervisor (All JC)", "Ajay Sharma (SM - Shillong)", "Rakesh Ahmed (SM - Tura)", "Saharul (SM - Jowai)"]
        sm_filter = st.selectbox("👤 Filter by Responsible SM:", sm_filter_list)

    # ----------------- 30 DAYS RETENTION & USER-SPECIFIC TICKET FILTER -----------------
    now_ist_dt = get_ist_now().replace(tzinfo=None)
    retention_limit_days = 30

    filtered_rows = []
    for r in all_rows:
        t_id = r[0]
        t_site = r[1]
        t_status = r[4]
        t_eng = r[6]
        t_logged_by = r[7]
        t_created = r[16]
        t_closed = r[17]

        # 1. Closed ticket 30 days retention logic
        if t_status == "CLOSED" and t_closed:
            try:
                clean_closed = str(t_closed).split(".")[0]
                closed_dt = datetime.strptime(clean_closed, "%Y-%m-%d %H:%M:%S")
                days_since_closed = (now_ist_dt - closed_dt).days
                if days_since_closed > retention_limit_days:
                    continue
            except Exception:
                pass

        # 2. Identify Job Centre
        t_jc = "Unknown"
        for jc_opt in JC_LIST:
            if f"[{jc_opt}]" in t_site:
                t_jc = jc_opt
                break

        # 3. User-Specific Access Control (Login-ৰ পিছত কেৱল নিজৰ অপেন টিকট ফিল্টাৰ)
        user_match = False
        if role == "Utility Technician":
            user_match = (t_logged_by == current_username) and (t_status != "CLOSED")
        elif role == "Service Engineer":
            user_match = (t_eng == current_username) and (t_status != "CLOSED")
        elif role == "Service Manager":
            mgr_jc = user.get("jc", "")
            user_match = (mgr_jc == "All") or (t_jc == mgr_jc)
        elif role == "Docket Team":
            user_match = (t_status in ["PENDING_DOCKET", "ASSIGNED_ENG"])
        else:
            user_match = True

        if not user_match:
            continue

        # 4. Standard UI filters (TRT, JC, SM dropdown)
        trt_str, trt_cat, trt_hours = calculate_trt(t_created, t_closed)

        trt_match = True
        if trt_filter != "All TRT":
            if "Normal" in trt_filter and trt_cat != "Normal (< 24h)":
                trt_match = False
            elif "Warning" in trt_filter and trt_cat != "Warning (24-48h)":
                trt_match = False
            elif "Critical" in trt_filter and trt_cat != "Critical (> 48h)":
                trt_match = False

        jc_match = (jc_filter == "All JCs") or (t_jc == jc_filter)

        sm_match = True
        if sm_filter == "Ajay Sharma (SM - Shillong)":
            sm_match = (t_jc == "Shillong")
        elif sm_filter == "Rakesh Ahmed (SM - Tura)":
            sm_match = (t_jc == "Tura")
        elif sm_filter == "Saharul (SM - Jowai)":
            sm_match = (t_jc == "Jowai")

        if trt_match and jc_match and sm_match:
            filtered_rows.append((r, t_jc, trt_str, trt_cat))

    # ----------------- MASTER TICKETS TABLE (ALL TKT EKELOGE) -----------------
    st.markdown("### 📋 All Tickets Master Table (একেদমে সকলো টিকট একেলগে)")
    st.caption(f"Showing **{len(filtered_rows)}** matching tickets for your access")

    if filtered_rows:
        table_data = []
        for item in reversed(filtered_rows):
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
            master_df.to_excel(writer, index=False, sheet_name="All_Tickets")
        st.download_button(
            label="📥 Download All Tickets Report (Excel)",
            data=excel_buffer.getvalue(),
            file_name=f"DG_All_Tickets_{get_ist_now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("No tickets found matching your role or the selected filters.")

    # ----------------- DATE-WISE & JC-WISE ANALYTICS TABLE -----------------
    st.write("---")
    st.markdown("### 📈 Date-wise & JC-wise Breakdown")
    st.caption("Owner নিৰীক্ষণৰ বাবে: Log Date-wise Total ➔ Approved Total ➔ Pending Total ➔ Reject Total ➔ Closed Date-wise Total")

    analytics_rows = []
    for r in all_rows:
        t_id, t_site, t_status = r[0], r[1], r[4]
        t_created, t_closed = r[16], r[17]

        t_jc = "Unknown"
        for jc_opt in JC_LIST:
            if f"[{jc_opt}]" in t_site:
                t_jc = jc_opt
                break

        analytics_rows.append({
            "Ticket ID": t_id,
            "JC": t_jc,
            "Log Date": t_created.split(" ")[0] if t_created else "N/A",
            "Close Date": t_closed.split(" ")[0] if t_closed else "N/A",
            "Status": t_status
        })

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
            st.dataframe(pd.DataFrame(summary_records), use_container_width=True)

    # ----------------- DETAILED TICKET ACTION CARDS -----------------
    st.write("---")
    st.subheader("🔍 Ticket Action & Individual Details")

    for item in reversed(filtered_rows):
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
                eng_phone = eng_info.get("phone", "")
                phone_html = f" | 📱 [**Call {eng_phone}**](tel:{eng_phone})" if eng_phone else ""
                st.markdown(f"Docket No: **{t_docket}** | Assigned Engineer: **{eng_name}**{phone_html}")

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

            # ----------------- UTILITY TECH FINAL CLOSURE -----------------
            elif role == "Utility Technician" and t_status == "PENDING_UT_VERIFY":
                if t_logged_by == current_username:
                    st.write("🔍 *You logged this ticket. Please verify work done and decide:*")
                    c1, c2 = st.columns(2)
                    if c1.button("Approve & Close", key=f"ut_app_{t_id}"):
                        now_close = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
                        update_fault_in_sheet(t_id, {
                            "status": "CLOSED",
                            "closed_at": now_close,
                            "action_by_selfie": user_selfie,
                            "action_by_loc": user_loc
                        })
                        send_telegram_alert(f"🎉 Ticket CLOSED Successfully\nTicket: {t_id}\nJC: {ticket_jc}\nTotal Resolution TRT: {trt_str}\nVerified & Closed by: {user['name']}")
                        st.rerun()
                    if c2.button("Reject (Re-assign to Engineer)", key=f"ut_rej_{t_id}"):
                        update_fault_in_sheet(t_id, {"status": "ASSIGNED_ENG"})
                        send_telegram_alert(f"⚠️ Ticket Verification Rejected by UT\nTicket: {t_id}\nJC: {ticket_jc}\nTRT: {trt_str}\nRe-opened for Engineer.")
                        st.rerun()
                else:
                    creator_name = USERS.get(t_logged_by, {}).get("name", t_logged_by)
                    st.warning(f"🔒 This fault was logged by **{creator_name}**. Only the creator can close it.")
