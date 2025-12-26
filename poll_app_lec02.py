import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

LECTURE_DATA = {
    "Audit: The Revenue Leak": {
        "id": "lec02_audit_rev",
        "options": ["50%", "63%", "70%", "72%"],
        "content": "Based on the Q3 2025 data, what specific percentage of revenue is still claimed by the 'Big Three' labels?"
    },
    "Audit: The 53bps Driver": {
        "id": "lec02_audit_margin",
        "options": ["Ad-supported Free Tier", "Premium Individual", "Student/Duo Bundles", "Non-repeatable Social Charges"],
        "content": "Which specific segment was responsible for the 53bps Gross Margin expansion reported in Q3?"
    },
    "Synthesis: Apple's Advantage": {
        "id": "lec02_synth_apple",
        "options": ["Higher upfront fees", "Local on-device AI processing", "Ignoring EU law", "Hardware exclusivity"],
        "content": "How does Apple's 'Project Sonic' leverage its Neural Engine to bypass the EU 200% Rule?"
    },
    "Lab: Churn Fragility": {
        "id": "lec02_lab_churn",
        "options": ["Leo (Conscious Creator)", "Marcus (Sonic Purist)", "Maya (Vibe-Drifter)"],
        "content": "Which persona proved most vulnerable to Apple’s $10.99 'Sonic' pricing during your simulation?"
    },
    "Lab: The Deal-Breaker": {
        "id": "lec02_lab_word",
        "options": ["Free Text Entry"],
        "content": "What is the #1 reason your persona would REJECT the 'Originals' (Vertical Integration) mandate? (Type one word)"
    },
    "Final Boardroom Recommendation": {
        "id": "lec02_final_vote",
        "options": ["Strategy A: Vanguard Pivot", "Strategy B: Regulatory Shield", "Strategy C: Premium Anchor", "Strategy D: Custom Hybrid"],
        "content": "As the PMM Taskforce, what is your final recommendation to Daniel Ek?"
    }
}

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_submissions(poll_id):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    params = {"poll_id": f"eq.{poll_id}", "select": "*"}
    try:
        # MANDATORY CHANGE: Changed 'submissions' to 'votes'
        r = requests.get(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, params=params)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame()

# ==========================================
# 3. GLOBAL NAVIGATION
# ==========================================
st.set_page_config(page_title="Lec02 Strategic Verdict", layout="wide")

# Persistent State Management
if 'unlocked' not in st.session_state:
    st.session_state.unlocked = False

page = st.sidebar.radio("Navigation", ["Student Voting", "Instructor Dashboard"])
selected_act_name = st.sidebar.selectbox("Current Discussion Question:", list(LECTURE_DATA.keys()))
current_act = LECTURE_DATA[selected_act_name]

# ==========================================
# 4. STUDENT VOTING PAGE
# ==========================================
if page == "Student Voting":
    st.title("Student War Room")
    st.subheader(selected_act_name)
    st.info(current_act["content"])
    
    if f"voted_{current_act['id']}" not in st.session_state:
        with st.form(key=f"form_{current_act['id']}"):
            name = st.text_input("Student Name / ID:")
            
            if current_act['options'] == ["Free Text Entry"]:
                vote = st.text_input("Enter your word/response:")
            else:
                vote = st.radio("Select your answer:", current_act['options'])
            
            comment = st.text_area("Justification (Mandatory - min 5 words):")
            submit = st.form_submit_button("Submit Verdict")
            
            if submit:
                word_count = len(comment.strip().split())
                if name and vote and word_count >= 5:
                    payload = {
                        "poll_id": current_act["id"], 
                        "option": vote, 
                        "comment": comment, 
                        "student_name": name
                    }
                    # MANDATORY FIX: Sending to 'votes'
                    requests.post(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, json=payload)
                    st.session_state[f"voted_{current_act['id']}"] = True
                    st.success("Verdict recorded. Strategy requires precision!")
                    st.rerun()
                else:
                    st.error("🚨 All fields required. Provide Name and a 5-word justification.")
    else:
        st.success("Submission received for this activity.")

# ==========================================
# 5. INSTRUCTOR DASHBOARD
# ==========================================
elif page == "Instructor Dashboard":
    st.title("Executive Dashboard")
    pwd = st.sidebar.text_input("Admin Password", type="password")
    
    if pwd == INSTRUCTOR_PASSWORD:
        st.header(f"Live Boardroom Data: {selected_act_name}")
        
        colA, colB = st.columns(2)
        with colA:
            if st.button("REVEAL RESULTS", use_container_width=True): 
                st.session_state.unlocked = True
        with colB:
            if st.button("HIDE RESULTS", use_container_width=True): 
                st.session_state.unlocked = False

        if st.session_state.unlocked:
            # Call the helper function that uses the 'votes' table
            df = get_submissions(current_act['id'])
            
            if not df.empty:
                col_m, col_c = st.columns([1, 3])
                with col_m:
                    st.metric("Submissions", len(df))
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", data=csv, file_name=f"Lec02_{current_act['id']}.csv")
                
                with col_c:
                    if current_act['options'] == ["Free Text Entry"]:
                        st.write("### The Deal-Breakers:")
                        st.info(", ".join(df['option'].dropna().astype(str).tolist()))
                    else:
                        counts = df['option'].value_counts().reset_index()
                        counts.columns = ['Option', 'Votes']
                        c_type = st.radio("Chart:", ["Bar", "Pie"], horizontal=True)
                        fig = px.bar(counts, x='Votes', y='Option', orientation='h', color='Option') if c_type == "Bar" else px.pie(counts, values='Votes', names='Option', hole=0.4)
                        st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(df[['student_name', 'option', 'comment']], use_container_width=True)
            else:
                st.info("Awaiting taskforce inputs...")
    else:
        st.warning("Enter administrator password in the sidebar.")
