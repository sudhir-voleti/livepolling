import streamlit as st
import requests
import pandas as pd
import time

# ==========================================
# 1. HARDCODED KEYS (The "Get It Working" Way)
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"

# ==========================================
# 2. POLL CONTENT (Edit these 3 things only!)
# ==========================================
POLL_ID = "lecture_01_marketing"  # Change this to save data in a new "bucket"
TITLE = "Which Ad Strategy is Most Ethical?"
POLL_OPTIONS = {
    "Option A": "Data-driven targeting (Personalized)",
    "Option B": "Mass-market appeal (Generic)",
    "Option C": "Contextual targeting (Privacy-first)"
}

# ==========================================
# 3. APP LOGIC (Don't touch unless needed)
# ==========================================
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

st.set_page_config(page_title="Live Poll", layout="centered")
st.title(f"🔥 {TITLE}")

# --- VOTING SECTION ---
cols = st.columns(len(POLL_OPTIONS))
options_list = list(POLL_OPTIONS.keys())

for i, opt in enumerate(options_list):
    with cols[i]:
        st.subheader(opt)
        st.info(POLL_OPTIONS[opt])

st.divider()
choice = st.radio("Cast your vote:", options_list, horizontal=True)
user_comment = st.text_input("Why did you choose this? (Optional)")

if st.button("Submit Vote", type="primary"):
    payload = {
        "poll_id": POLL_ID,
        "option": choice,
        "comment": user_comment.strip() if user_comment else None
    }
    # Using 'Prefer': 'return=minimal' to speed up the post
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/votes", 
                         headers={**headers, "Prefer": "return=minimal"}, 
                         json=payload)
    if resp.status_code in [200, 201]:
        st.success("Vote recorded! Results updating below...")
        time.sleep(1)
        st.rerun()
    else:
        st.error(f"Error saving vote: {resp.text}")

# --- RESULTS SECTION (AUTO-REFRESHING) ---
@st.fragment(run_every=5)
def live_results():
    st.divider()
    st.header("📊 Live Results")
    # Fetch only the votes for THIS specific poll_id
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{POLL_ID}&select=option,comment", headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        if data:
            df = pd.DataFrame(data)
            # Count results and ensure all options show up even with 0 votes
            counts = df['option'].value_counts().reindex(options_list, fill_value=0)
            st.bar_chart(counts)
            st.write(f"**Total Votes:** {len(data)}")
            
            # Show the 5 most recent comments
            comments = df.dropna(subset=['comment']).tail(5)
            if not comments.empty:
                st.write("**Recent Feedback:**")
                st.table(comments[['option', 'comment']])
        else:
            st.info("Waiting for the first vote...")

live_results()

# --- INSTRUCTOR SECTION ---
with st.expander("👩‍🏫 Instructor Panel"):
    p = st.text_input("Admin Password", type="password")
    if p == INSTRUCTOR_PASSWORD:
        if st.button("Reset THIS Poll (Delete Votes)"):
            requests.delete(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{POLL_ID}", headers=headers)
            st.rerun()
