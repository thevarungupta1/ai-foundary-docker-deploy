import streamlit as st
from agent import run_agent, MODEL

st.set_page_config(
    page_title="Foundry AI Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Enterprise AI Agent")
st.caption(f"Powered by Microsoft Foundry | {MODEL}")

with st.sidebar:
    st.header("Agent Settings")
    st.success("Foundry configuration loaded")

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.write("Capabilities")
    st.write("• Technical Q&A")
    st.write("• Calculator tool")
    st.write("• Multi-turn conversations")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask your AI agent...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                response = run_agent(
                    st.session_state.messages
                )
                st.markdown(response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

            except Exception:
                st.error(
                    "Unable to contact the AI model. "
                    "Check the application logs."
                )