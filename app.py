import streamlit as st
from agent import ask_agent

st.set_page_config(page_title="SQL Copilot", page_icon="🤖")
st.title("🤖 SQLite Agentic Copilot")

# Initializing the chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Presenting prev messages.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Getting input from the user
if prompt := st.chat_input("Ask a question about the database..."):
    # Storing the user message in the session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent response
    with st.chat_message("assistant"):
        # Presenting step by step status to the user while the agent is thinking
        with st.status("Thinking...", expanded=True) as status:
            
            def handle_step(func_name: str, args: dict):
                if func_name == "get_schema":
                    st.write("🔍 Inspecting database schema...")
                elif func_name == "run_query":
                    query = args.get("sql_query", "")
                    st.write("⚡ Executing SQL Query:")
                    st.code(query, language="sql")
                else:
                    st.write(f"⚙️ Calling tool: `{func_name}`")

            # Calling the agent with the user prompt and the step handler
            answer = ask_agent(prompt, on_step=handle_step)
            status.update(label="Completed!", state="complete", expanded=False)

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})