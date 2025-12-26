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
# 3. UI LOGIC
# ==========================================
st.set_page_config(page_title="Lec02 Strategic Verdict", layout="wide")
st.title("Lec02: Grounded Audits & Persona Labs")

# Sidebar
page = st.sidebar.radio("View", ["Student Voting", "Instructor Dashboard"])
selected_q_name = st.sidebar.selectbox("Active Poll:", list(LECTURE_DATA.keys()))
current_act = LECTURE_DATA[selected_q_name]

if page == "Student Voting":
    st.subheader(selected_q_name)
    st.info(current_act['content'])

    # Guardrail: Check session state
    if f"voted_{current_act['id']}" not in st.session_state:
        with st.form(key=f"form_{current_act['id']}"):
            name = st.text_input("Student Name / ID:")
            
            if current_act['options'] == ["Free Text Entry"]:
                vote = st.text_input("Enter your word/response:")
            else:
                vote = st.radio("Select your answer:", current_act['options'])
            
            comment = st.text_area("Justification / Evidence (Optional):")
            submit = st.form_submit_button("Submit Verdict")
            
            if submit:
                if name and vote:
                    post_submission(name, current_act['id'], vote, comment)
                    st.session_state[f"voted_{current_act['id']}"] = True
                    st.success("Verdict recorded. Refined thinking leads to better strategy!")
                    st.rerun()
                else:
                    st.warning("Please provide both Name and a Selection.")
    else:
        st.success("You have already submitted your response for this poll.")

else:
    # INSTRUCTOR DASHBOARD
    pw = st.sidebar.text_input("Instructor Password:", type="password")
    if pw == INSTRUCTOR_PASSWORD:
        st.header(f"Live Insights: {selected_q_name}")
        df = get_submissions(current_act['id'])
        
        if not df.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Submissions", len(df))
                # Restore CSV Download Feature
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Data (CSV)", data=csv, file_name=f"{current_act['id']}_results.csv")
            
            with col2:
                if current_act['options'] != ["Free Text Entry"]:
                    counts = df['option'].value_counts().reset_index()
                    counts.columns = ['Option', 'Votes']
                    chart_type = st.radio("Chart:", ["Bar", "Pie"], horizontal=True)
                    if chart_type == "Bar":
                        fig = px.bar(counts, x='Votes', y='Option', orientation='h', color='Option')
                    else:
                        fig = px.pie(counts, values='Votes', names='Option', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("Word Submissions:")
                    st.info(", ".join(df['option'].tolist()))
            
            with st.expander("Participant Commentary"):
                st.dataframe(df[['student_name', 'option', 'comment']].dropna(subset=['comment']))
        else:
            st.info("Awaiting taskforce inputs...")
    else:
        st.warning("Enter instructor password to access boardroom data.")

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
