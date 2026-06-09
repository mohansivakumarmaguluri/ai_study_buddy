import streamlit as st
from utils.ui_helper import render_sidebar
from utils.gemini_helper import GeminiHelper
from utils.database import save_study_session
from utils.export_helper import export_to_txt, export_to_pdf

# Initialize common layout and styling
render_sidebar("explain")

st.title("💡 Concept Explainer")
st.markdown("Break down complex academic topics into easy-to-understand explanations with real-world analogies, takeaways, and exam questions.")

# 1. State Initializers
if "explain_topic" not in st.session_state:
    st.session_state.explain_topic = ""
if "explain_output" not in st.session_state:
    st.session_state.explain_output = None

# Topic input fields
topic_input = st.text_input(
    "Enter a topic or question you want explained:",
    value=st.session_state.explain_topic,
    placeholder="e.g., Quantum Computing, Photosynthesis, Recursion in programming..."
)

col_btn, _ = st.columns([1, 3])
with col_btn:
    generate_clicked = st.button("🚀 Explain Topic", use_container_width=True)

# 2. Logic Execution
if generate_clicked and topic_input.strip():
    st.session_state.explain_topic = topic_input.strip()
    
    with st.spinner("🧠 AI Study Buddy is analyzing the topic... Please wait."):
        try:
            # Query Gemini helper
            result = GeminiHelper.explain_concept(
                st.session_state.explain_topic, 
                api_key=st.session_state.api_key
            )
            st.session_state.explain_output = result
            
            # Save the session to SQLite history
            save_study_session("explain", st.session_state.explain_topic, result)
            st.success("Explanation generated and saved to history!")
            
        except Exception as e:
            st.error(f"Failed to generate explanation: {str(e)}")

# 3. Render Outputs if present
if st.session_state.explain_output:
    data = st.session_state.explain_output
    topic = st.session_state.explain_topic
    
    st.markdown("---")
    st.subheader(f"📖 Study Guide: {topic}")
    
    # Render segmented Tabs for premium visual organization
    tab1, tab2, tab3, tab4 = st.tabs([
        "👶 Simple Explanation", 
        "⚙️ Technical Details", 
        "📌 Key Takeaways", 
        "📝 Exam & Interview Prep"
    ])
    
    with tab1:
        st.markdown('<div class="analogy-box"><b>💡 Real-world Analogy Inside:</b> Look out for the everyday analogy used to describe this topic.</div>', unsafe_allow_html=True)
        st.markdown(data.get("simple_explanation", ""))
        
    with tab2:
        st.markdown(data.get("technical_details", ""))
        
    with tab3:
        takeaways = data.get("key_takeaways", [])
        if takeaways:
            for item in takeaways:
                st.markdown(f'<div class="stat-badge">✔</div> {item}', unsafe_allow_html=True)
        else:
            st.write("No specific takeaways found.")
            
    with tab4:
        st.markdown("Practice these questions to test your understanding:")
        prep_questions = data.get("exam_prep", [])
        if prep_questions:
            for idx, q in enumerate(prep_questions, 1):
                with st.expander(f"Question {idx}: {q.get('question', '')}"):
                    st.markdown(f"**Model Answer:**  \n{q.get('answer', '')}")
        else:
            st.write("No preparation questions available.")
            
    # Export Options Section
    st.markdown("---")
    st.subheader("📥 Save this Study Session")
    
    col_txt, col_pdf, _ = st.columns([1, 1, 2])
    
    # Text Export
    txt_data = export_to_txt("explain", topic, data)
    with col_txt:
        st.download_button(
            label="📄 Export as TXT",
            data=txt_data,
            file_name=f"study_buddy_explain_{topic.lower().replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    # PDF Export
    pdf_bytes = export_to_pdf("explain", topic, data)
    with col_pdf:
        st.download_button(
            label="📕 Export as PDF",
            data=pdf_bytes,
            file_name=f"study_buddy_explain_{topic.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # Recommendations & next topics
    st.markdown("<br/>", unsafe_allow_html=True)
    try:
        rec_data = GeminiHelper.detect_difficulty_and_recommendations(topic, st.session_state.api_key)
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.markdown(f"**Personalized Next Recommendations (Level: {rec_data.get('difficulty', 'Intermediate')}):**")
        for rec in rec_data.get("recommendations", []):
            st.markdown(f"- **{rec}**")
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception:
        pass
elif not topic_input:
    # Warm prompt for the student
    st.info("Enter any topic above (e.g. 'Binary Search Tree', 'Photosynthesis Light Reactions') to generate a comprehensive study sheet.")
