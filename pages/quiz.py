import streamlit as st
from utils.ui_helper import render_sidebar
from utils.gemini_helper import GeminiHelper
from utils.database import save_study_session, log_quiz_result
from utils.export_helper import export_to_txt, export_to_pdf

# Initialize common layout and styling
render_sidebar("quiz")

st.title("🎯 Study Quiz Generator")
st.markdown("Test your knowledge! Input any topic, choose a level, and tackle a 10-question interactive MCQ quiz with explanatory grading.")

# 1. State Initializers
if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = ""
if "quiz_difficulty" not in st.session_state:
    st.session_state.quiz_difficulty = "Intermediate"
if "quiz_output" not in st.session_state:
    # This will store the list of 10 question dicts
    st.session_state.quiz_output = None
if "quiz_user_answers" not in st.session_state:
    st.session_state.quiz_user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0.0

# Input Controls
topic_input = st.text_input(
    "Enter the topic for your quiz:",
    value=st.session_state.quiz_topic,
    placeholder="e.g. World War II, Object Oriented Python, Data Structures..."
)

difficulty = st.selectbox(
    "Select Difficulty Level:",
    options=["Beginner", "Intermediate", "Advanced"],
    index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.quiz_difficulty)
)

col_btn, _ = st.columns([1.5, 3])
with col_btn:
    generate_clicked = st.button("🎲 Generate 10-Q Quiz", use_container_width=True)

# 2. Reset and Logic Execution
if generate_clicked and topic_input.strip():
    # Clear previous quiz states
    st.session_state.quiz_topic = topic_input.strip()
    st.session_state.quiz_difficulty = difficulty
    st.session_state.quiz_output = None
    st.session_state.quiz_user_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_score = 0.0
    
    with st.spinner("⏳ Compiling 10 quiz questions. Thinking..."):
        try:
            questions = GeminiHelper.generate_quiz(
                st.session_state.quiz_topic,
                st.session_state.quiz_difficulty,
                api_key=st.session_state.api_key
            )
            st.session_state.quiz_output = questions
            
            # Save the quiz structure to history
            save_study_session("quiz", f"{st.session_state.quiz_topic} ({st.session_state.quiz_difficulty})", questions)
            st.success("Quiz compiled! Test your answers below.")
        except Exception as e:
            st.error(f"Failed to generate quiz: {str(e)}")

# 3. Render Quiz if generated
if st.session_state.quiz_output:
    questions = st.session_state.quiz_output
    topic = st.session_state.quiz_topic
    
    st.markdown("---")
    st.subheader(f"📝 Quiz: {topic} (Level: {st.session_state.quiz_difficulty})")
    
    # Render Questions Form
    with st.form(key="quiz_form"):
        for i, q in enumerate(questions):
            st.markdown(f"**Question {i+1}:** {q.get('question')}")
            
            options = q.get("options", [])
            # Convert user answers or default to None
            default_val = st.session_state.quiz_user_answers.get(i, None)
            
            # Display choices
            # In Streamlit, a radio can be used to select.
            # If the quiz has been graded, we show simple text lists instead of radios, or disabled radios
            choice = st.radio(
                f"Select option for Q{i+1}:",
                options=options,
                index=options.index(default_val) if default_val in options else None,
                key=f"q_radio_{i}",
                label_visibility="collapsed"
            )
            
            if choice:
                st.session_state.quiz_user_answers[i] = choice
                
            st.markdown("<br/>", unsafe_allow_html=True)
            
        # Submit Form Button
        submit_form = st.form_submit_button(
            label="💯 Grade My Quiz" if not st.session_state.quiz_submitted else "🔄 Recalculate Grade", 
            use_container_width=True
        )
        
        if submit_form:
            # Check if all answered
            answered_count = len(st.session_state.quiz_user_answers)
            if answered_count < len(questions):
                st.warning(f"You answered {answered_count} out of {len(questions)} questions. Grading anyway...")
            
            # Compute score
            correct_count = 0
            for idx, q in enumerate(questions):
                user_choice = st.session_state.quiz_user_answers.get(idx, None)
                correct_idx = q.get("correct_option_index", 0)
                correct_choice = q.get("options", [])[correct_idx]
                
                if user_choice == correct_choice:
                    correct_count += 1
            
            final_score = (correct_count / len(questions)) * 100
            st.session_state.quiz_score = final_score
            st.session_state.quiz_submitted = True
            
            # Log results to SQLite
            log_quiz_result(topic, final_score)
            
    # 4. Grading Feedback View
    if st.session_state.quiz_submitted:
        score = st.session_state.quiz_score
        st.markdown("---")
        st.markdown(f"### 📊 Result: **{score:.1f}%** ({int(score // 10)} / 10 Correct)")
        
        if score >= 80:
            st.balloons()
            st.success("🏆 Excellent job! You have a solid grasp of this topic!")
        elif score >= 50:
            st.info("👍 Good effort! Review the explanations below to improve.")
        else:
            st.warning("📚 Keep practicing! Revision of the concept explainer might help.")
            
        st.markdown("### 🔍 Detailed Corrections")
        for i, q in enumerate(questions):
            user_choice = st.session_state.quiz_user_answers.get(i, "No answer")
            correct_idx = q.get("correct_option_index", 0)
            correct_choice = q.get("options", [])[correct_idx]
            
            is_correct = user_choice == correct_choice
            color = "#10b981" if is_correct else "#ef4444"
            status = "✅ Correct" if is_correct else "❌ Incorrect"
            
            # Display colored card for corrections
            with st.container():
                st.markdown(f"""
                <div style="background-color: rgba(30, 41, 59, 0.3); border-left: 5px solid {color}; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                    <strong>Q{i+1}: {q.get('question')}</strong><br/>
                    <span style="color: {color};"><b>Your Answer:</b> {user_choice} ({status})</span><br/>
                    <span style="color: #10b981;"><b>Correct Answer:</b> {correct_choice}</span><br/>
                    <p style="margin-top: 8px; font-size: 0.92rem; color: #94a3b8;"><b>Explanation:</b> {q.get('explanation')}</p>
                </div>
                """, unsafe_allow_html=True)
                
        # Exports
        st.markdown("### 📥 Download Graded Quiz")
        col_txt, col_pdf, _ = st.columns([1, 1, 2])
        
        txt_data = export_to_txt("quiz", topic, questions)
        with col_txt:
            st.download_button(
                label="📄 Export Quiz (TXT)",
                data=txt_data,
                file_name=f"study_buddy_quiz_{topic.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
        pdf_bytes = export_to_pdf("quiz", topic, questions)
        with col_pdf:
            st.download_button(
                label="📕 Export Quiz (PDF)",
                data=pdf_bytes,
                file_name=f"study_buddy_quiz_{topic.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
elif not topic_input:
    st.info("Input a topic above and select a difficulty. We will generate a structured quiz using Gemini 1.5 Flash.")
