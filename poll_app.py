import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

# ==========================================
# 0. CORE CONFIGURATION
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy" # Replace with your secret key if this is public
INSTRUCTOR_PASSWORD = "Aitp@2026"

# GLOBAL SETTINGS - Update these per session
CURRENT_LECTURE_ID = "LEC02"  # Change this to 'EXEC_01' etc. for different courses

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ==========================================
# 1. LECTURE CONTENT (The JSON Engine)
# ==========================================
LECTURE_CONTENT = {
    "Concept Check: Product-Service": {
        "id": "q1_spectrum",
        "type": "SINGLE",
        "content": "Where does a SaaS subscription (like Oracle) fall on the Product-Service spectrum?",
        "options": ["Pure Good", "Pure Service", "More Good than Service", "More Service than Good"],
        "correct": "More Service than Good"
    },
    "Strategic Pillars: Select All": {
        "id": "q2_pillars",
        "type": "MULTI",
        "content": "Select ALL features that justify a $19.99 Super-Premium price point:",
        "options": ["Lossless Audio", "AI Remixing", "Concert Presale", "Hardware Discounts"],
        "correct": ["Lossless Audio", "Concert Presale"]
    },
    "Open Reflection": {
        "id": "q3_text",
        "type": "TEXT",
        "content": "In your own words, how does digital scarcity impact marginal cost?",
        "options": [],
        "correct": None
    }
}

# ==========================================
# 2. ANALYSIS DISPATCHER FUNCTIONS
# ==========================================

def analyze_single(df, config):
    counts = df['option'].value_counts().reindex(config['options'], fill_value=0).reset_index()
    counts.columns = ['Choice', 'Votes']
    fig = px.bar(counts, x='Votes', y='Choice', orientation='h', color='Choice', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)
    if config['correct']:
        st.info(f"🎯 **Reference Answer:** {config['correct']}")

def analyze_multi(df, config):
    st.write("### Exact Strategic Combinations")
    combos = df['option'].value_counts().reset_index()
    combos.columns = ['Combination', 'Count']
    st.table(combos)
    if config['correct']:
        target = ", ".join(sorted(config['correct']))
        matches = len(df[df['option'] == target])
        st.success(f"✅ **Target Strategy:** {target} ({matches} students matched exactly)")

def analyze_text(df, config):
    df['Word Count'] = df['comment'].apply(lambda x: len(str(x).split()))
    df = df.sort_values('Word Count', ascending=False)
    st.write("### Class Participation (By Effort)")
    st.dataframe(df[['pgid', 'comment', 'Word Count']], use_container_width=True)

# ==========================================
# 3. APP UI & VOTING LOGIC
# ==========================================
st.set_page_config(page_title=f"Lecture Engine: {CURRENT_LECTURE_ID}", layout="wide")
st.title(f"🎓 {CURRENT_LECTURE_ID}: Interactive Session")

selected_label = st.selectbox("Current Activity:", list(LECTURE_CONTENT.keys()))
q_cfg = LECTURE_CONTENT[selected_label]
poll_id = q_cfg['id']

# Lock Logic
lock_key = f"voted_{CURRENT_LECTURE_ID}_{poll_id}"
if lock_key not in st.session_state: st.session_state[lock_key] = False
if 'unlocked' not in st.session_state: st.session_state.unlocked = False

# Voting Form
with st.container(border=True):
    st.subheader(q_cfg['content'])
    pgid = st.text_input("Enter PGID (Mandatory)", key=f"pgid_{poll_id}")
    
    if q_cfg['type'] == "SINGLE":
        user_val = st.radio("Select Choice:", q_cfg['options'], key=f"rad_{poll_id}")
    elif q_cfg['type'] == "MULTI":
        user_val_list = st.multiselect("Select all that apply:", q_cfg['options'], key=f"mul_{poll_id}")
        user_val = ", ".join(sorted(user_val_list))
    else:
        user_val = "OPEN_TEXT"

    user_comment = st.text_area("Justification (Min 20 chars)", key=f"cmt_{poll_id}")

    # Validation
    is_ready = len(pgid.strip()) > 0 and len(user_comment.strip()) >= 20 and (user_val != "" and user_val != "[]")

    if st.session_state[lock_key]:
        st.warning(f"✅ Response recorded for {CURRENT_LECTURE_ID}.")
    else:
        if st.button("Submit Response", type="primary", disabled=not is_ready):
            payload = {
                "lecture_id": CURRENT_LECTURE_ID,
                "poll_id": poll_id,
                "pgid": pgid,
                "option": user_val,
                "comment": user_comment
            }
            resp = requests.post(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                st.session_state[lock_key] = True
                st.success("Successfully submitted!")
                time.sleep(1); st.rerun()

# ==========================================
# 4. INSTRUCTOR PANEL & DATA DISPATCH
# ==========================================
st.divider()
with st.expander("👩‍🏫 Instructor Controls"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == INSTRUCTOR_PASSWORD:
        c1, c2 = st.columns(2)
        if c1.button("REVEAL RESULTS", use_container_width=True): st.session_state.unlocked = True
        if c2.button("HIDE RESULTS", use_container_width=True): st.session_state.unlocked = False
        
        if st.button("Clear Data for CURRENT Activity"):
            requests.delete(f"{SUPABASE_URL}/rest/v1/votes?lecture_id=eq.{CURRENT_LECTURE_ID}&poll_id=eq.{poll_id}", headers=headers)
            st.rerun()

if st.session_state.unlocked:
    st.header(f"📊 Live Analysis: {selected_label}")
    # Fetch only data for the current lecture and current question
    url = f"{SUPABASE_URL}/rest/v1/votes?lecture_id=eq.{CURRENT_LECTURE_ID}&poll_id=eq.{poll_id}&select=*"
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200 and resp.json():
        df = pd.DataFrame(resp.json())
        
        # Download Link
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Activity Data (CSV)", data=csv, file_name=f"{CURRENT_LECTURE_ID}_{poll_id}.csv")
        
        # DISPATCH TO SPECIFIC ANALYSIS FUNCTION
        if q_cfg['type'] == "SINGLE": analyze_single(df, q_cfg)
        elif q_cfg['type'] == "MULTI": analyze_multi(df, q_cfg)
        elif q_cfg['type'] == "TEXT": analyze_text(df, q_cfg)
    else:
        st.info("No submissions found for this lecture/activity combo.")
