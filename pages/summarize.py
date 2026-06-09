import streamlit as st
from utils.ui_helper import render_sidebar
from utils.gemini_helper import GeminiHelper
from utils.pdf_reader import extract_text_from_pdf
from utils.database import save_study_session
from utils.export_helper import export_to_txt, export_to_pdf

# Initialize common layout and styling
render_sidebar("summarize")

st.title("📝 Notes Summarizer")
st.markdown("Transform long lectures, paragraphs, or PDF textbooks into clean revision notes, exam-focus sheets, and key checkpoints.")

# 1. State Initializers
if "summarize_topic" not in st.session_state:
    st.session_state.summarize_topic = ""
if "summarize_output" not in st.session_state:
    st.session_state.summarize_output = None

# Input methods tabs
input_tab1, input_tab2 = st.tabs(["✍️ Paste Your Notes", "📂 Upload PDF Textbook"])

notes_content = ""
source_name = ""

with input_tab1:
    pasted_notes = st.text_area(
        "Paste your study material or lecture notes here:",
        height=250,
        placeholder="Type or paste notes here (at least 50 words recommended for best results)..."
    )
    if pasted_notes.strip():
        notes_content = pasted_notes.strip()
        # Create a topic/title automatically from the first few words of the text
        words = pasted_notes.split()
        source_name = " ".join(words[:5]) + "..." if len(words) > 5 else pasted_notes

with input_tab2:
    uploaded_file = st.file_uploader(
        "Upload a PDF chapter or slides:",
        type=["pdf"],
        help="Reads text directly from the pages of your PDF document."
    )
    if uploaded_file is not None:
        try:
            with st.spinner("Extracting text from PDF..."):
                notes_content = extract_text_from_pdf(uploaded_file)
            st.success(f"Successfully loaded {uploaded_file.name} ({len(notes_content)} characters extracted)!")
            source_name = uploaded_file.name
        except Exception as e:
            st.error(f"Error parsing PDF: {str(e)}")

# Summarize trigger button
col_btn, _ = st.columns([1, 3])
with col_btn:
    summarize_clicked = st.button("⚡ Summarize Now", use_container_width=True)

# 2. Logic Execution
if summarize_clicked:
    if not notes_content.strip():
        st.warning("Please provide study content by either pasting text or uploading a PDF.")
    else:
        st.session_state.summarize_topic = source_name
        with st.spinner("🔍 AI Study Buddy is synthesizing your notes..."):
            try:
                result = GeminiHelper.summarize_notes(
                    notes_content, 
                    api_key=st.session_state.api_key
                )
                st.session_state.summarize_output = result
                
                # Save to history
                save_study_session("summarize", st.session_state.summarize_topic, result)
                st.success("Summary generated successfully!")
            except Exception as e:
                st.error(f"Failed to summarize notes: {str(e)}")

# 3. Render Outputs if present
if st.session_state.summarize_output:
    data = st.session_state.summarize_output
    topic = st.session_state.summarize_topic
    
    st.markdown("---")
    st.subheader(f"📘 Summary Guide: {topic}")
    
    # Renders structured layout
    tab1, tab2, tab3 = st.tabs([
        "📝 Executive Summary & Revision Sheet", 
        "🔑 Important Concepts", 
        "🎯 Exam-Focused Notes"
    ])
    
    with tab1:
        st.markdown("### Executive Summary")
        st.markdown(data.get("summary", ""))
        
        st.markdown("---")
        st.markdown("### Quick Revision Checklist")
        checkpoints = data.get("revision_sheet", [])
        if checkpoints:
            for item in checkpoints:
                st.checkbox(item, key=f"rev_{item[:30]}_{hash(item)}")
        else:
            st.write("No checkpoint list available.")
            
    with tab2:
        st.markdown("### Key Vocabulary & Core Concepts")
        concepts = data.get("key_concepts", [])
        if concepts:
            for item in concepts:
                st.markdown(f'<div class="stat-badge">🔑</div> {item}', unsafe_allow_html=True)
        else:
            st.write("No concepts list available.")
            
    with tab3:
        st.markdown("### Critical Exam Points & Formulae")
        st.markdown(data.get("exam_focus", ""))
        
    # Export Options Section
    st.markdown("---")
    st.subheader("📥 Export Summary Sheet")
    
    col_txt, col_pdf, _ = st.columns([1, 1, 2])
    
    # Text Export
    txt_data = export_to_txt("summarize", topic, data)
    with col_txt:
        st.download_button(
            label="📄 Export as TXT",
            data=txt_data,
            file_name=f"study_buddy_summary_{topic.lower().replace(' ', '_')[:20]}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    # PDF Export
    pdf_bytes = export_to_pdf("summarize", topic, data)
    with col_pdf:
        st.download_button(
            label="📕 Export as PDF",
            data=pdf_bytes,
            file_name=f"study_buddy_summary_{topic.lower().replace(' ', '_')[:20]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
elif not notes_content:
    st.info("Pasted text notes or uploaded PDFs are summarized securely using Gemini 1.5 Flash.")
