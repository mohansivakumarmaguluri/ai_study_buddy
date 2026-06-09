import streamlit as st
from utils.ui_helper import render_sidebar
from utils.gemini_helper import GeminiHelper
from utils.database import save_study_session
from utils.export_helper import export_to_txt, export_to_pdf

# Initialize common layout and styling
render_sidebar("flashcards")

# Inject Custom CSS for Flashcard Styling
st.markdown("""
<style>
    .flashcard-box {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        min-height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 40px;
        margin: 20px 0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease;
    }
    .flashcard-title {
        font-size: 0.85rem;
        color: #10b981;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .flashcard-text {
        font-size: 1.6rem;
        font-weight: 600;
        color: #f8fafc;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎴 Flashcard Generator")
st.markdown("Generate interactive question-and-answer study decks on any topic. Flip them to reveal answers, and test your recall.")

# 1. State Initializers
if "flashcards_topic" not in st.session_state:
    st.session_state.flashcards_topic = ""
if "flashcards_output" not in st.session_state:
    st.session_state.flashcards_output = None
if "flashcards_index" not in st.session_state:
    st.session_state.flashcards_index = 0
if "flashcards_flipped" not in st.session_state:
    st.session_state.flashcards_flipped = False

# Input Controls
topic_input = st.text_input(
    "Enter a topic or paste notes to generate flashcards from:",
    value=st.session_state.flashcards_topic,
    placeholder="e.g. Mitochondria structure, Python decorators, French vocabulary..."
)

card_count = st.slider("Number of cards to generate:", min_value=5, max_value=15, value=8)

col_btn, _ = st.columns([1.5, 3])
with col_btn:
    generate_clicked = st.button("🎴 Create Flashcard Deck", use_container_width=True)

# 2. Logic Execution
if generate_clicked and topic_input.strip():
    # Reset index and flip status
    st.session_state.flashcards_topic = topic_input.strip()
    st.session_state.flashcards_output = None
    st.session_state.flashcards_index = 0
    st.session_state.flashcards_flipped = False
    
    with st.spinner("🃏 Crafting study flashcards..."):
        try:
            cards = GeminiHelper.generate_flashcards(
                st.session_state.flashcards_topic,
                count=card_count,
                api_key=st.session_state.api_key
            )
            st.session_state.flashcards_output = cards
            
            # Save the session to study history
            save_study_session("flashcards", f"{st.session_state.flashcards_topic} ({len(cards)} cards)", cards)
            st.success(f"Successfully generated {len(cards)} study flashcards!")
        except Exception as e:
            st.error(f"Failed to generate flashcards: {str(e)}")

# 3. Render Deck if present
if st.session_state.flashcards_output:
    cards = st.session_state.flashcards_output
    topic = st.session_state.flashcards_topic
    idx = st.session_state.flashcards_index
    
    st.markdown("---")
    st.subheader(f"🎴 Study Deck: {topic}")
    
    # Progress indicator
    st.write(f"Card **{idx + 1}** of **{len(cards)}**")
    st.progress((idx + 1) / len(cards))
    
    current_card = cards[idx]
    is_flipped = st.session_state.flashcards_flipped
    
    # Display Front or Back
    card_side_title = "BACK (Answer / Definition)" if is_flipped else "FRONT (Question / Concept)"
    card_display_text = current_card.get("back") if is_flipped else current_card.get("front")
    
    # Render Card Box
    st.markdown(f"""
    <div class="flashcard-box">
        <div class="flashcard-title">{card_side_title}</div>
        <div class="flashcard-text">{card_display_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Card controls row
    col_prev, col_flip, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅️ Previous", use_container_width=True, disabled=(idx == 0)):
            st.session_state.flashcards_index -= 1
            st.session_state.flashcards_flipped = False
            st.rerun()
            
    with col_flip:
        if st.button("🔄 Flip Card", type="primary", use_container_width=True):
            st.session_state.flashcards_flipped = not st.session_state.flashcards_flipped
            st.rerun()
            
    with col_next:
        if st.button("Next ➡️", use_container_width=True, disabled=(idx == len(cards) - 1)):
            st.session_state.flashcards_index += 1
            st.session_state.flashcards_flipped = False
            st.rerun()
            
    # Export Options Section
    st.markdown("---")
    st.subheader("📥 Export Flashcards Deck")
    
    col_txt, col_pdf, _ = st.columns([1, 1, 2])
    
    txt_data = export_to_txt("flashcards", topic, cards)
    with col_txt:
        st.download_button(
            label="📄 Export as TXT",
            data=txt_data,
            file_name=f"study_buddy_flashcards_{topic.lower().replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    pdf_bytes = export_to_pdf("flashcards", topic, cards)
    with col_pdf:
        st.download_button(
            label="📕 Export as PDF",
            data=pdf_bytes,
            file_name=f"study_buddy_flashcards_{topic.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
elif not topic_input:
    st.info("Input a topic above and select card limits. Flashcards will be generated with clear front prompts and back answers.")
