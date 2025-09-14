import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434").rstrip("/")
CHAT_URL = f"{OLLAMA_BASE}/api/chat"

# Replace with your Obsidian MCP server base URL
MCP_BASE = os.getenv("OBSIDIAN_API_https_URL", "https://127.0.0.1:27124").rstrip("/")

YOUR_ACCESS_TOKEN = os.getenv("OBSIDIAN_API_KEY")


# Define tool schemas
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Get a list of all files from the Obsidian vault",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_file",
            "description": "Summarize the content of a specific markdown file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the markdown file (e.g. 'xyz.md')",
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_summary_note",
            "description": "Create a summary note that summarizes all files and links to each file",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# -------------------------------
# Obsidian MCP API Wrappers
# -------------------------------
print("API Key:", YOUR_ACCESS_TOKEN)

AUTH_HEADER = {
    "Accept": "application/json",
    "Authorization": f"Bearer {YOUR_ACCESS_TOKEN}",  # your actual token or credentials here
}

print("Headers:", AUTH_HEADER)


def list_files():
    resp = requests.get(f"{MCP_BASE}/vault/", headers={**AUTH_HEADER}, verify=False)
    resp.raise_for_status()
    return resp.json()


def summarize_file(filename: str):
    resp = requests.post(
        f"{MCP_BASE}/summarize",
        json={"filename": filename},
        headers={**AUTH_HEADER},
        verify=False,
    )
    resp.raise_for_status()
    return resp.json()


def create_summary_note():
    resp = requests.post(
        f"{MCP_BASE}/summary-note", headers={**AUTH_HEADER}, verify=False
    )
    resp.raise_for_status()
    return resp.json()


FUNCTION_MAP = {
    "list_files": list_files,
    "summarize_file": summarize_file,
    "create_summary_note": create_summary_note,
}

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Obsidian Chatbot", page_icon="📓")
st.title("📓 Obsidian Vault Assistant")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system",
            "content": (
                "You are an assistant for Obsidian that can call APIs via tools. "
                "If the user asks about files, summaries, or notes, you MUST call the appropriate tool. "
                "Never answer from your own knowledge when a tool exists."
            ),
        }
    ]

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me about your Obsidian vault..."):
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send to Ollama with tools
    payload = {
        "model": "llama3.1:latest",  # 🔑 swap to qwen2.5:latest or mistral:latest if needed
        "messages": st.session_state["messages"],
        "tools": TOOLS,
        "stream": False,
    }
    response = requests.post(CHAT_URL, json=payload)
    response.raise_for_status()
    data = response.json()

    # 🔍 DEBUG: Show raw Ollama response
    with st.expander("🔎 Raw Ollama response"):
        st.json(data)

    # Parse tool call more defensively
    tool_call = None
    message = data.get("message", {})
    if "tool_calls" in message:
        tool_calls = message["tool_calls"]

        if tool_calls:
            tool_call = tool_calls[0]
    elif "tool" in message:
        tool_call = message["tool"]

    # If tool call requested
    if tool_call:
        fn_name = tool_call["function"]["name"]
        args = tool_call["function"].get("arguments", "{}")
        # Check if args is a string; if so, parse it
        if isinstance(args, str):
            fn_args = json.loads(args)
        else:
            fn_args = args

        st.chat_message("assistant").markdown(
            f"➡️ Calling tool: `{fn_name}` with args `{fn_args}`"
        )

        if fn_name in FUNCTION_MAP:
            try:
                result = FUNCTION_MAP[fn_name](**fn_args)
                result_str = json.dumps(result, indent=2)

                # Add tool response back into conversation
                st.session_state["messages"].append(
                    {"role": "tool", "name": fn_name, "content": result_str}
                )
                with st.chat_message("tool"):
                    st.markdown(f"**{fn_name} result:**\n```\n{result_str}\n```")

                # Ask LLM to produce a nice answer using the tool result
                followup_payload = {
                    "model": "llama3.1:latest",
                    "messages": st.session_state["messages"],
                    "stream": False,
                }
                followup = requests.post(CHAT_URL, json=followup_payload)
                followup.raise_for_status()
                final_msg = followup.json()["message"]["content"]

                st.session_state["messages"].append(
                    {"role": "assistant", "content": final_msg}
                )
                with st.chat_message("assistant"):
                    st.markdown(final_msg)

            except Exception as e:
                st.error(f"Tool call `{fn_name}` failed: {e}")
        else:
            st.error(f"Unknown tool requested: {fn_name}")

    else:
        # No tool call, just assistant reply
        final_msg = data["message"]["content"]
        st.session_state["messages"].append({"role": "assistant", "content": final_msg})
        with st.chat_message("assistant"):
            st.markdown(final_msg)
