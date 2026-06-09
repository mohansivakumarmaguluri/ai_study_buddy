import streamlit as st
import time
import os
from datetime import datetime
from utils.database import init_db, update_streak, log_study_time, get_analytics, get_study_sessions, get_session_by_id

def inject_custom_css():
    """Injects premium styling and themes into the active Streamlit app view."""
    st.markdown("""
    <style>
        /* Card layouts */
        .glass-card {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        .highlight-box {
            background: rgba(16, 185, 129, 0.1);
            border-left: 4px solid #10b981;
            padding: 16px;
            border-radius: 6px;
            margin: 15px 0;
        }
        .analogy-box {
            background: rgba(245, 158, 11, 0.08);
            border-left: 4px solid #f59e0b;
            padding: 16px;
            border-radius: 6px;
            margin: 15px 0;
        }
        .stat-badge {
            background-color: #1e293b;
            padding: 6px 12px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.1);
            display: inline-block;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        /* Button custom styling */
        .stButton>button {
            border-radius: 8px !important;
            transition: all 0.2s ease;
        }
        /* Tab formatting */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(30, 41, 59, 0.5) !important;
            border-radius: 6px 6px 0 0px !important;
            padding: 10px 16px !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
            color: #94a3b8 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1e3a8a !important;
            color: #ffffff !important;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

def track_study_time():
    """Calculates elapsed seconds between runs and updates database timer."""
    init_db()
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = time.time()
    else:
        current_time = time.time()
        elapsed = current_time - st.session_state.session_start_time
        st.session_state.session_start_time = current_time
        if 1 < elapsed < 600:
            log_study_time(int(elapsed))

def render_sidebar(current_page: str):
    """Renders the common sidebar widgets, API key handles, and lists history specific to the page."""
    track_study_time()
    inject_custom_css()
    
    st.sidebar.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=90)
    st.sidebar.title("AI Study Buddy 🎓")
    st.sidebar.caption("Your personalized Gemini learning assistant.")
    st.sidebar.markdown("---")
    
    # 1. API Key management
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
        
    api_key_env = st.sidebar.text_input(
        "Gemini API Key:",
        type="password",
        value=st.session_state.api_key or "",
        help="Paste your Google Gemini API key here. It overrides the .env file key."
    )
    if api_key_env:
        st.session_state.api_key = api_key_env
        
    # 2. Streak Display
    streak_info = update_streak()
    st.sidebar.markdown(f"🔥 Streak: **{streak_info.get('streak_count', 0)} Days**")
    st.sidebar.markdown("---")
    
    # 3. Session History for current page type
    st.sidebar.markdown(f"📂 **{current_page.capitalize()} History**")
    sessions = get_study_sessions(page=current_page)
    
    if not sessions:
        st.sidebar.caption("No history for this feature yet.")
    else:
        for sess in sessions[:8]: # Show top 8 history sessions
            label = f"💡 {sess['topic']}" if current_page == "explain" else \
                    f"📝 {sess['topic']}" if current_page == "summarize" else \
                    f"🎯 {sess['topic']}" if current_page == "quiz" else \
                    f"🎴 {sess['topic']}" if current_page == "flashcards" else \
                    f"💬 {sess['topic']}"
            
            if len(label) > 28:
                label = label[:25] + "..."
                
            # Create interactive link to reload that session
            if st.sidebar.button(label, key=f"hist_{current_page}_{sess['id']}", use_container_width=True):
                # Fetch full session details
                data = get_session_by_id(sess['id'])
                if data:
                    st.session_state[f"{current_page}_topic"] = data["topic"]
                    st.session_state[f"{current_page}_output"] = data["content"]
                    st.toast(f"Loaded session: '{data['topic']}'", icon="📂")
                    st.rerun()
                    
    st.sidebar.markdown("---")
    # Quick navigation hint
    st.sidebar.page_link("app.py", label="🏠 Home Dashboard", icon="🏠")
