import streamlit as st
from utils.ui_helper import render_sidebar
from utils.gemini_helper import GeminiHelper
from utils.database import save_study_session

# Initialize common layout and styling
render_sidebar("chat")

st.title("💬 Study Assistant Chat")
st.markdown("Interact directly with your AI Study Buddy. Ask follow-up questions, request coding debugging, clarify equations, or check study outlines.")

# 1. State Initializers
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "model", "text": "Hello! 🎓 I am your AI Study Buddy. I can help clarify concepts, explain textbook chapters, write coding exercises, or quiz you. What are we studying today?"}
    ]
if "chat_topic" not in st.session_state:
    # Default topic description for saving history
    st.session_state.chat_topic = "General Q&A Session"

# Action buttons row (Clear & Save)
col_save, col_clear, _ = st.columns([1.5, 1.5, 4])

with col_save:
    if st.button("💾 Save Chat Session", use_container_width=True):
        if len(st.session_state.chat_history) > 1:
            # Generate a nice topic summary based on the first user query
            first_user_msg = next((msg["text"] for msg in st.session_state.chat_history if msg["role"] == "user"), None)
            topic_desc = f"Chat: {first_user_msg[:25]}..." if first_user_msg else "Study Buddy Chat Session"
            
            # Save the raw list as session content
            save_study_session("chat", topic_desc, st.session_state.chat_history)
            st.toast("Chat session saved to history!", icon="💾")
        else:
            st.warning("Chat is empty. Type a message first!")
            
with col_clear:
    if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
        st.session_state.chat_history = [
            {"role": "model", "text": "Hello! 🎓 I am your AI Study Buddy. I can help clarify concepts, explain textbook chapters, write coding exercises, or quiz you. What are we studying today?"}
        ]
        st.toast("Chat history cleared.", icon="🗑️")
        st.rerun()

st.markdown("---")

# 2. Render Chat History Messages
for msg in st.session_state.chat_history:
    role = msg["role"]
    avatar = "🎓" if role == "model" else "🧑‍💻"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["text"])

# 3. Handle User Input
user_prompt = st.chat_input("Ask a follow-up question, or copy a topic here...")

if user_prompt:
    # Render user message immediately
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_prompt)
        
    # Append to state history
    st.session_state.chat_history.append({"role": "user", "text": user_prompt})
    
    # Generate response
    with st.chat_message("model", avatar="🎓"):
        message_placeholder = st.empty()
        with st.spinner("✍️ Study Buddy is thinking..."):
            try:
                # Call Gemini Helper
                ai_reply = GeminiHelper.chat_response(
                    user_prompt,
                    st.session_state.chat_history,
                    api_key=st.session_state.api_key
                )
                message_placeholder.markdown(ai_reply)
                
                # Append assistant reply to state history
                st.session_state.chat_history.append({"role": "model", "text": ai_reply})
            except Exception as e:
                error_msg = f"Failed to get reply: {str(e)}"
                message_placeholder.error(error_msg)
