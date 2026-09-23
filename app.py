# ১. Utility Technician Form (Fault Log)
    if role == "Utility Technician":
        st.subheader("নতুন Fault Log কৰক")
        with st.form("new_fault_form"):
            site = st.text_input("Site ID (যেনে: GUW-10)")
            
            c_dg1, c_dg2 = st.columns(2)
            with c_dg1:
                dg_make = st.selectbox(
                    "DG Make", 
                    ["Kirloskar", "Cummins", "Mahindra Powerol", "Ashok Leyland", "Eicher", "Other"]
                )
            with c_dg2:
                dg_rating = st.selectbox(
                    "DG Rating (kVA)", 
                    ["10 kVA", "15 kVA", "20 kVA", "25 kVA", "30 kVA", "40 kVA", "62.5 kVA", "82.5 kVA", "125 kVA", "Other"]
                )
                
            desc = st.text_area("Fault Remarks / Description (সমস্যাৰ বিৱৰণ)")
            fault_img = st.file_uploader("Fault ৰ ফটো আপলোড কৰক", type=["jpg", "png", "jpeg"])
            submit = st.form_submit_button("Request পঠিয়াওক")

            if submit and site and desc:
                cursor.execute("SELECT COUNT(*) FROM faults")
                count = cursor.fetchone()[0]
                new_id = f"TKT-{count + 101}"
                photo_path = save_image_buffer(fault_img, "fault", new_id)

                # DG Make আৰু Rating একেলগে DG ফিল্ডত সংৰক্ষণ কৰা হৈছে
                dg_combined = f"{dg_make} ({dg_rating})"

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
                    new_id, site, dg_combined, desc, 'PENDING_SM', '', '', 
                    current_username, user_selfie, user_loc, 
                    '', '', '', photo_path, '', now_time, None
                ))
                conn.commit()

                # Telegram Alert-তো এই সকলোবোৰ তথ্য একেলগে প্ৰেৰণ হ'ব
                tg_msg = (
                    f"🚨 *নতুন DG Fault Logged!*\n\n"
                    f"📌 *Ticket ID:* `{new_id}`\n"
                    f"🏢 *Site ID:* {site}\n"
                    f"🏭 *DG Make:* {dg_make}\n"
                    f"⚡ *DG Rating:* {dg_rating}\n"
                    f"📝 *Fault Remarks:* {desc}\n"
                    f"👤 *Logged by:* {user['name']}\n"
                    f"🕒 *Date & Time:* {format_dt(now_time)}"
                )
                send_telegram_alert(tg_msg)

                st.success(f"Fault {new_id} সফলভাৱে যোগ কৰা হ'ল!")
                st.rerun()
            elif submit:
                st.error("Site ID আৰু Fault Remarks লিখাটো বাধ্যতামূলক!")
