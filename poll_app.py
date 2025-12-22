import streamlit as st
import requests
import pandas as pd
import time

# ==========================================
# 1. SETUP & CONFIG (Hardcoded for now)
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"

# Define all activities for today's lecture here
LECTURE_DATA = {
    "Activity 1: Ethics": {
        "id": "lec1_act1",
        "options": ["Option A", "Option B"],
        "content": "Is AI tracking ethical?"
    },
    "Activity 2: Pricing": {
        "id": "lec1_act2",
        "options": ["High", "Low", "Freemium"],
        "content": "What is the best pricing strategy?"
    }
}

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

st.set_page_config(page_title="Classroom Poll", layout="wide")

# ==========================================
# 2. ACTIVITY SELECTOR (Top Bar)
# ==========================================
st.title("🎓 Live Lecture Interactive")
selected_act_name = st.selectbox("Select Current Activity:", list(LECTURE_DATA.keys()))
current_act = LECTURE_DATA[selected_act_name]

# ==========================================
# 3. VOTING UI
# ==========================================
with st.container(border=True):
    st.header(selected_act_name)
    st.write(current_act["content"])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        moniker = st.text_input("Name/Moniker", key=f"name_{current_act['id']}")
    with col2:
        choice = st.radio("Your Choice:", current_act["options"], horizontal=True, key=f"radio_{current_act['id']}")
    
    comment = st.text_input("Comment (Optional)", key=f"comm_{current_act['id']}")

    if st.button("Submit Vote", type="primary", key=f"btn_{current_act['id']}"):
        if not moniker:
            st.error("Please enter a moniker!")
        else:
            payload = {
                "poll_id": current_act["id"],
                "option": choice,
                "comment": comment,
                "student_name": moniker
            }
            resp = requests.post(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                st.success("Vote cast! Wait for the instructor to reveal results.")

# ==========================================
# 4. INSTRUCTOR CONTROL & RESULTS
# ==========================================
st.divider()

# We use session_state to keep the results "Unlocked" once the password is correct
if 'results_unlocked' not in st.session_state:
    st.session_state.results_unlocked = False

with st.expander("👩‍🏫 Instructor: Reveal Results"):
    pwd = st.text_input("Instructor Password", type="password")
    if pwd == INSTRUCTOR_PASSWORD:
        if st.button("🔓 SHOW RESULTS TO CLASS"):
            st.session_state.results_unlocked = True
        if st.button("🔒 HIDE RESULTS"):
            st.session_state.results_unlocked = False
        
        if st.button("🗑️ Reset Current Activity"):
            requests.delete(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{current_act['id']}", headers=headers)
            st.rerun()

# --- THE CONDITIONAL RESULTS SECTION ---
if st.session_state.results_unlocked:
    @st.fragment(run_every=5)
    def show_live_data():
        st.subheader(f"📊 Live Results: {selected_act_name}")
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{current_act['id']}&select=*", headers=headers)
        if resp.status_code == 200 and resp.json():
            df = pd.DataFrame(resp.json())
            st.bar_chart(df['option'].value_counts())
            st.dataframe(df[['student_name', 'option', 'comment']], use_container_width=True)
        else:
            st.write("No data yet.")
    
    show_live_data()
else:
    st.info("Results are currently hidden by the instructor. Cast your vote and wait!")
