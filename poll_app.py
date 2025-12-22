import streamlit as st
import requests
import pandas as pd
import time

# ==========================================
# 1. HARDCODED KEYS (Keep these here for now)
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"

# ==========================================
# 2. LECTURE CONTENT (Edit this block each class)
# ==========================================
POLL_CONFIG = {
    "poll_id": "lecture_02_ethics",        # CHANGE THIS for every new poll
    "title": "AI Ethics: Self-Driving Cars",
    "options": {
        "Option A": "Prioritize Passenger",
        "Option B": "Prioritize Pedestrian",
        "Option C": "Random/Neutral"
    },
    "descriptions": {
        "Option A": "The car protects the owner at all costs.",
        "Option B": "The car minimizes total loss of life.",
        "Option C": "The car follows a pre-set legal lottery."
    }
}

# ==========================================
# 3. APP LOGIC
# ==========================================
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

st.set_page_config(page_title="Live Poll", layout="centered")
st.title(f"🔥 {POLL_CONFIG['title']}")

# --- VOTING SECTION ---
cols = st.columns(len(POLL_CONFIG['options']))
options_list = list(POLL_CONFIG['options'].keys())

for i, opt in enumerate(options_list):
    with cols[i]:
        st.subheader(opt)
        st.info(POLL_CONFIG['descriptions'].get(opt, ""))

st.divider()

# NEW: Moniker and Vote Layout
c1, c2 = st.columns([1, 2])
with c1:
    moniker = st.text_input("Your Moniker/Name", placeholder="e.g. Anonymous Tiger")
with c2:
    choice = st.radio("Cast your vote:", options_list, horizontal=True)

user_comment = st.text_input("Optional: Why did you choose this?")

if st.button("Submit Vote", type="primary"):
    if not moniker:
        st.error("Please enter a moniker (name) to vote!")
    else:
        payload = {
            "poll_id": POLL_CONFIG['poll_id'],
            "option": choice,
            "comment": user_comment.strip() if user_comment else None,
            "student_name": moniker.strip() # Matches your DB column
        }
        resp = requests.post(f"{SUPABASE_URL}/rest/v1/votes", 
                             headers={**headers, "Prefer": "return=minimal"}, 
                             json=payload)
        if resp.status_code in [200, 201]:
            st.success(f"Vote recorded, {moniker}! 🎉")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"Error: {resp.text}")

# --- RESULTS SECTION ---
@st.fragment(run_every=5)
def live_results():
    st.divider()
    st.header("📊 Live Results")
    # Fetch only for this specific poll
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{POLL_CONFIG['poll_id']}&select=option,comment,student_name", headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        if data:
            df = pd.DataFrame(data)
            counts = df['option'].value_counts().reindex(options_list, fill_value=0)
            st.bar_chart(counts)
            
            # Show comments with the new monikers
            comments = df.dropna(subset=['comment']).tail(5)
            if not comments.empty:
                st.write("**Recent Feedback:**")
                # Showing Name, Option, and Comment
                st.table(comments[['student_name', 'option', 'comment']])
        else:
            st.info("Waiting for the first vote...")

live_results()

# --- INSTRUCTOR SECTION ---
with st.expander("👩‍🏫 Instructor Panel"):
    p = st.text_input("Admin Password", type="password")
    if p == INSTRUCTOR_PASSWORD:
        if st.button("Reset THIS Poll"):
            requests.delete(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{POLL_CONFIG['poll_id']}", headers=headers)
            st.rerun()
