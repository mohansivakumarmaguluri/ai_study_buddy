import streamlit as st
import time
import pandas as pd
from datetime import datetime
from utils.database import init_db, update_streak, log_study_time, get_analytics, get_session_by_id, delete_session
from utils.gemini_helper import GeminiHelper

# 1. Page Configuration
st.set_page_config(
    page_title="AI Study Buddy - Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Database Initialization
init_db()
streak_info = update_streak()

# 3. Time Spent Tracking (Incremental logging on page refreshes)
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()
else:
    current_time = time.time()
    elapsed = current_time - st.session_state.session_start_time
    st.session_state.session_start_time = current_time
    # Avoid logging idle times (limit to 10 minutes between actions)
    if 1 < elapsed < 600:
        log_study_time(int(elapsed))

# 4. Premium Aesthetic Injector (CSS styling)
st.markdown("""
<style>
    /* Styling for dashboard elements */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 5px 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .rec-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.8));
        border-left: 5px solid #10b981;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 5. Shared Sidebar Setup
def render_sidebar():
    st.sidebar.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
    st.sidebar.title("AI Study Buddy 🎓")
    st.sidebar.caption("Your personalized Gemini learning assistant.")
    st.sidebar.markdown("---")
    
    # API Key Input
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
        
    # Active Streak Display
    st.sidebar.markdown(f"### 🔥 Current Streak: **{streak_info.get('streak_count', 0)} Days**")
    
    # Study History Navigation / Reader
    st.sidebar.markdown("### 📜 Study History")
    analytics = get_analytics()
    recent_sessions = analytics.get("recent_progress", [])
    
    if not recent_sessions:
        st.sidebar.info("No study history yet. Start exploring!")
    else:
        for sess in recent_sessions[:8]: # Show top 8 recent
            icon = "❓"
            page_name = sess['activity_type']
            if page_name == "explain":
                icon = "💡"
            elif page_name == "summarize":
                icon = "📝"
            elif page_name == "quiz":
                icon = "🎯"
            elif page_name == "flashcards":
                icon = "🎴"
            elif page_name == "chat":
                icon = "💬"
                
            label = f"{icon} {sess['topic'][:22]}"
            if len(sess['topic']) > 22:
                label += "..."
            
            # Use columns to align a viewing button and delete button
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                # Store the session selected in session state to open in a dialog
                if st.button(label, key=f"hist_{sess['timestamp']}_{sess['topic']}", use_container_width=True):
                    # Find session in database
                    # Because we don't have id in recent_progress, let's fetch session by details or query db directly
                    pass
            with col2:
                # We can add a simple trash icon or leave as is to keep it clean.
                pass
                
    st.sidebar.markdown("---")
    st.sidebar.info("Tip: Use the sidebar pages to navigate between modules.")

render_sidebar()

# Fetch latest analytics
analytics = get_analytics()

# Format time spent
total_seconds = analytics.get("total_time_spent", 0)
hours = total_seconds // 3600
minutes = (total_seconds % 3600) // 60
seconds = total_seconds % 60
time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m {seconds}s"

# 6. Main Dashboard Content
st.title("📚 Study Buddy Dashboard")
st.markdown("Welcome back! Here is your personalized learning analytics and study plan.")
st.markdown("---")

# Dashboard Stat Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Study Streak</div>
        <div class="metric-val">{analytics.get("streak_count", 0)} 🔥</div>
        <div class="metric-label">Consecutive Days</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Time Spent Learning</div>
        <div class="metric-val">{time_str}</div>
        <div class="metric-label">Total Duration</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sessions Completed</div>
        <div class="metric-val">{analytics.get("total_sessions", 0)}</div>
        <div class="metric-label">AI Interactions</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    quiz_avg = analytics.get("average_quiz_score", 0.0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Avg Quiz Score</div>
        <div class="metric-val">{quiz_avg:.1f}%</div>
        <div class="metric-label">Out of {analytics.get("total_quizzes_taken", 0)} Quizzes</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# 7. Layout Splits for Charts and Recommendations
chart_col, rec_col = st.columns([3, 2])

with chart_col:
    st.subheader("📈 Learning Activity Tracker")
    daily_act = analytics.get("daily_activity", [])
    if daily_act:
        df = pd.DataFrame(daily_act)
        df.columns = ["Date", "Activities Done"]
        df = df.sort_values(by="Date")
        st.bar_chart(df.set_index("Date"), height=240, color="#3b82f6")
    else:
        st.info("Study buddy logs activities as you learn. Take a quiz or summarize a PDF to populate charts!")

with rec_col:
    st.subheader("💡 Recommended Next Steps")
    
    # Extract last studied topic to customize recommendations
    recent_topics = [sess['topic'] for sess in analytics.get('recent_progress', []) if sess['activity_type'] == 'explain']
    
    if recent_topics:
        last_topic = recent_topics[0]
        st.caption(f"Based on your recent interest in: *{last_topic}*")
        
        # Call Gemini helper async/cacheable to get difficulty & recommendations
        try:
            rec_data = GeminiHelper.detect_difficulty_and_recommendations(last_topic, st.session_state.api_key)
            diff = rec_data.get("difficulty", "Intermediate")
            explan = rec_data.get("explanation", "")
            recs = rec_data.get("recommendations", [])
            
            st.markdown(f"Detected Level: **{diff}** ({explan})")
            for topic in recs:
                st.markdown(f"""
                <div class="rec-card">
                    <b>🎯 {topic}</b><br/>
                    <span style="font-size:0.85rem; color:#94a3b8;">Copy this topic and explain it in the Concept Explainer.</span>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
            <div class="rec-card"><b>🎯 Advanced Applications</b><br/>Deep dive into implementation patterns.</div>
            <div class="rec-card"><b>🎯 Best Practices & Clean Code</b><br/>Optimize performance and security.</div>
            """, unsafe_allow_html=True)
    else:
        st.caption("Complete a concept explanation to get personalized topic recommendations!")
        st.markdown("""
        <div class="rec-card">
            <b>🔥 Concept Explainer</b><br/>
            Try search for: <i>"RESTful APIs"</i> or <i>"How neural networks learn"</i>.
        </div>
        <div class="rec-card">
            <b>📝 Notes Summarizer</b><br/>
            Upload lecture notes PDFs to get instant summary cheatsheets.
        </div>
        <div class="rec-card">
            <b>🎯 MCQ Quizzes</b><br/>
            Generate a quiz to test your readiness for exam questions.
        </div>
        """, unsafe_allow_html=True)

# 8. Learning History Timeline / Table
st.markdown("---")
st.subheader("🗓️ Activity History Details")

# Retrieve full history from database
full_history = analytics.get("recent_progress", [])
if full_history:
    # Build a nice pandas dataframe
    history_df = pd.DataFrame(full_history)
    history_df.columns = ["Activity Type", "Topic/Prompt", "Score (%)", "Timestamp"]
    
    # Capitalize Activity Type
    history_df["Activity Type"] = history_df["Activity Type"].str.upper()
    history_df["Score (%)"] = history_df["Score (%)"].fillna("-")
    
    st.dataframe(history_df, use_container_width=True)
else:
    st.write("No study logs registered yet. Jump into any study page in the sidebar to begin!")
