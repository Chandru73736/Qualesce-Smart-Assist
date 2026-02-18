import streamlit as st
import boto3
import time
from auth import create_user_table, add_user, login_user

# ---------------- Page Setup ----------------
st.set_page_config(
    page_title="Internal Knowledge Assistant",
    layout="wide"
)

create_user_table()

# ---------------- Session State ----------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "pending_prompt" not in st.session_state:
    st.session_state["pending_prompt"] = None


# ---------------- ENTERPRISE CSS ----------------
st.markdown("""
<style>

/* Layout */
.block-container {
    max-width: 1400px !important;
    margin: auto;
}

.stApp {
    background-color: #f4f6f9;
}

/* Buttons */
div.stButton > button {
    width: 100% !important;
    height: 50px !important;
    border-radius: 25px;
    font-size: 14px;
    background: linear-gradient(135deg, #4f8edc, #76a9ea);
    color: white;
    border: none;
    white-space: normal !important;
    transition: 0.3s ease;
}

div.stButton > button:hover {
    transform: translateY(-2px);
}

/* Chat Bubbles */
.chat-bubble {
    padding: 14px 18px;
    border-radius: 18px;
    margin-bottom: 12px;
    max-width: 70%;
    font-size: 15px;
}

.user-bubble {
    background: linear-gradient(135deg, #4f8edc, #76a9ea);
    color: white;
    margin-left: auto;
}

.assistant-bubble {
    background-color: white;
    color: #333;
}

/* Fixed Chat Input */
div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 800px;
}

div[data-testid="stChatInput"] textarea {
    border-radius: 25px !important;
    padding: 16px !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- Authentication ----------------
if not st.session_state["authenticated"]:

    col1, col2, col3 = st.columns([4, 4, 4])

    with col2:
        st.markdown("""
            <div style="margin-top:80px;">
                <h2 style="color:#0b3c6d;">🔐 Qualesce Smart Assist</h2>
                <h3 style="color:#0b3c6d;">Login</h3>
            </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True):
                if login_user(username, password):
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

        with tab2:
            new_user = st.text_input("Create Username")
            new_password = st.text_input("Create Password", type="password")

            if st.button("Sign Up", use_container_width=True):
                if add_user(new_user, new_password):
                    st.success("Account Created Successfully")
                else:
                    st.error("Username already exists")

    st.stop()


# ---------------- Sidebar ----------------
st.sidebar.title("📜 Chat History")

if st.session_state["messages"]:
    for i, m in enumerate(st.session_state["messages"]):
        if m["role"] == "user":
            st.sidebar.markdown(f"**Q{i+1}:** {m['content'][:40]}...")

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["messages"] = []
    st.rerun()


# ---------------- Header ----------------
st.markdown("""
<div style="padding-top:25px;">
<h2 style="color:#0b3c6d;">🤖 Qualesce Knowledge Assistant</h2>
<p style="color:#555;">Ask questions based on internal knowledge</p>
</div>
""", unsafe_allow_html=True)


# ---------------- Suggested Questions (HORIZONTAL FIX) ----------------
suggestions = [
    "What ROI benefits does Qualesce deliver?",
    "Want to Know About Qualesce and its process?",
    "Please provide a complete end-to-end overview of SAP",
    "What is the Vendor Confirmation process?",
    "Please describe the IS-AS process followed in Qualesce?",
]

cols = st.columns(len(suggestions))

for i, question in enumerate(suggestions):
    with cols[i]:
        if st.button(question, key=f"suggestion_{i}"):
            st.session_state["pending_prompt"] = question
            st.rerun()


# ---------------- AWS Setup ----------------
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
AWS_DEFAULT_REGION = st.secrets["AWS_DEFAULT_REGION"]


# ---------------- Display Chat ----------------
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="chat-bubble user-bubble">{msg["content"]}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="chat-bubble assistant-bubble">{msg["content"]}</div>',
            unsafe_allow_html=True
        )


# ---------------- Chat Input ----------------
prompt = st.chat_input("Message Qualesce Assistant...")

if st.session_state["pending_prompt"]:
    prompt = st.session_state["pending_prompt"]
    st.session_state["pending_prompt"] = None


# ---------------- Process Prompt ----------------
if prompt:

    st.session_state["messages"].append(
        {"role": "user", "content": prompt}
    )

    st.markdown(
        f'<div class="chat-bubble user-bubble">{prompt}</div>',
        unsafe_allow_html=True
    )

    assistant_container = st.empty()
    assistant_container.markdown(
        '<div class="chat-bubble assistant-bubble">Typing...</div>',
        unsafe_allow_html=True
    )

    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=AWS_DEFAULT_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    response = client.retrieve_and_generate(
        input={"text": prompt},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": "PGXNDGLTDP",
                "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            }
        }
    )

    answer = response["output"]["text"]

    full_response = ""
    for char in answer:
        full_response += char
        assistant_container.markdown(
            f'<div class="chat-bubble assistant-bubble">{full_response}</div>',
            unsafe_allow_html=True
        )
        time.sleep(0.01)

    st.session_state["messages"].append(
        {"role": "assistant", "content": answer}
    )
