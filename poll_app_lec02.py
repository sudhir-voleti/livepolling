import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"

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
        r = requests.get(f"{SUPABASE_URL}/rest/v1/submissions", headers=headers, params=params)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame()

def post_submission(student_name, poll_id, option, comment):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    data = {"student_name": student_name, "poll_id": poll_id, "option": option, "comment": comment}
    return requests.post(f"{SUPABASE_URL}/rest/v1/submissions", headers=headers, json=data)

# ==========================================
# 3. NAVIGATION (Place this before the UI)
# ==========================================
page = st.sidebar.radio("Navigation", ["Student Voting", "Instructor Dashboard"])

# ==========================================
# 4. STUDENT VOTING PAGE
# ==========================================
if page == "Student Voting":
    st.subheader(selected_act_name)
    st.info(current_act["content"])
    
    with st.form(key=f"form_{current_act['id']}"):
        choice = st.radio("Select your strategic choice:", current_act["options"])
        moniker = st.text_input("Name / Group Number")
        comment = st.text_area("Justification (Mandatory - min 5 words):")
        submit = st.form_submit_button("Submit Vote")
        
        if submit:
            word_count = len(comment.strip().split())
            if moniker and word_count >= 5:
                payload = {"poll_id": current_act["id"], "option": choice, "comment": comment, "student_name": moniker}
                requests.post(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, json=payload)
                st.success("Vote recorded.")
                st.rerun()
            else:
                st.error("Identification and a 5-word justification are required.")

# ==========================================
# 5. INSTRUCTOR DASHBOARD PAGE (Explicit IF)
# ==========================================
elif page == "Instructor Dashboard":
    pwd = st.sidebar.text_input("Admin Password", type="password")
    
    if pwd == INSTRUCTOR_PASSWORD:
        st.header(f"Boardroom Results: {selected_act_name}")
        
        colA, colB = st.columns(2)
        with colA:
            if st.button("REVEAL RESULTS"): st.session_state.unlocked = True
        with colB:
            if st.button("HIDE RESULTS"): st.session_state.unlocked = False

        if st.session_state.get('unlocked'):
            # Fetch and Render Results
            resp = requests.get(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{current_act['id']}&select=*", headers=headers)
            if resp.status_code == 200 and resp.json():
                df = pd.DataFrame(resp.json())
                
                # Show Chart and Data
                fig = px.bar(df['option'].value_counts().reset_index(), x='count', y='option', orientation='h')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df[['student_name', 'option', 'comment']])
            else:
                st.info("Awaiting taskforce inputs...")
    else:
        st.warning("Please enter the administrator password in the sidebar.")
        
  # ==========================================
# 6. RENDER RESULTS & CSV DOWNLOAD
# ==========================================
def show_results():
    st.header(f"Live Insights: {selected_q_name}")
    df = get_submissions(current_act['id'])
    
    if not df.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Total Submissions", len(df))
            
            # Feature Preserved: CSV Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Raw Data (CSV)",
                data=csv,
                file_name=f"Lec02_Verdict_{current_act['id']}.csv",
                mime="text/csv",
            )
        
        with col2:
            # New for Lec02: Handle the Free Text "Word Cloud" question
            if current_act['options'] == ["Free Text Entry"]:
                st.write("### The Deal-Breakers (Raw Inputs):")
                # Grabs the 'option' column where students typed their one-word answers
                words = ", ".join(df['option'].dropna().astype(str).tolist())
                st.info(words)
            else:
                # Feature Preserved: Chart Toggle
                counts = df['option'].value_counts().reset_index()
                counts.columns = ['Option', 'Votes']
                chart_choice = st.radio("Chart Type:", ["Bar", "Pie"], horizontal=True)
                
                if chart_choice == "Bar":
                    fig = px.bar(counts, x='Votes', y='Option', orientation='h', color='Option', text_auto=True)
                else:
                    fig = px.pie(counts, values='Votes', names='Option', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
        
        # Feature Preserved: Participant Commentary for CP Tracking
        with st.expander("Detailed Participant Commentary"):
            st.dataframe(df[['student_name', 'option', 'comment']].dropna(subset=['comment']), use_container_width=True)
    else:
        st.info("Awaiting taskforce inputs...")

# Execute the render
show_results()
