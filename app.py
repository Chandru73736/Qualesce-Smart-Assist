import streamlit as st
import boto3
import os
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

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
.stApp {
    background-color: #f4f6f9;
}

section[data-testid="stSidebar"] {
    background-color: #e9eef6;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 6rem;
}

.chat-bubble {
    padding: 14px 18px;
    border-radius: 18px;
    margin-bottom: 12px;
    max-width: 70%;
    font-size: 15px;
    animation: fadeIn 0.25s ease-in-out;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.user-bubble {
    background-color: #0b3c6d;
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 4px;
}

.assistant-bubble {
    background-color: white;
    color: #333;
    margin-right: auto;
    border-bottom-left-radius: 4px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}

div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: 55%;
    transform: translateX(-50%);
    width: 50%;
}

div[data-testid="stChatInput"] textarea {
    border-radius: 20px !important;
    border: 1px solid #ddd !important;
    background-color: white !important;
    padding: 16px !important;
    font-size: 15px !important;
    min-height: 55px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.logout-container {
    position: fixed;
    bottom: 20px;
    left: 20px;
    width: 200px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Authentication ----------------
if not st.session_state["authenticated"]:

    st.markdown("<h2 style='text-align:center;color:#0b3c6d;'>🔐 Qualesce Login</h2>", unsafe_allow_html=True)

    left, center, right = st.columns([3, 4, 3])

    with center:
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

for i, m in enumerate(st.session_state["messages"]):
    if m["role"] == "user":
        st.sidebar.markdown(f"**Q{i+1}:** {m['content'][:40]}...")

st.sidebar.markdown('<div class="logout-container">', unsafe_allow_html=True)
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["messages"] = []
    st.rerun()
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# ---------------- Header ----------------
logo_path = r"C:\Users\ChandruS\OneDrive - Qualesce\Documents\QI\Qualesce Logo.png"

col1, col2 = st.columns([7, 3])

with col1:
    st.markdown("""
    <div style="padding-top:25px;">
        <div style="font-size:32px;font-weight:700;color:#0b3c6d;">
            🤖 Qualesce Knowledge Assistant
        </div>
        <div style="font-size:15px;color:#555;margin-top:4px;">
            Ask questions based on internal knowledge
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if os.path.exists(logo_path):
        st.markdown('<div style="text-align:right;padding-top:35px;">', unsafe_allow_html=True)
        st.image(logo_path, width=220)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- AWS Setup ----------------
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
AWS_DEFAULT_REGION = st.secrets["AWS_DEFAULT_REGION"]

# ---------------- Chat Display ----------------
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-bubble user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble assistant-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

# ---------------- Suggested Questions (Horizontal Row) ----------------
if len(st.session_state["messages"]) == 0:

    st.markdown("### 💡 Try asking:")

    suggestions = [
        "Explain PO Parking process",
        "How does Job Scheduling work?",
        "Describe Birthday Mail workflow",
        "What is Vendor Confirmation?",
        "Explain HUB sales automation"
    ]

    cols = st.columns(len(suggestions))

    for i, question in enumerate(suggestions):
        if cols[i].button(question, use_container_width=True):
            st.session_state["suggested_prompt"] = question
            st.rerun()

# ---------------- Chat Input ----------------
if "suggested_prompt" in st.session_state:
    prompt = st.session_state.pop("suggested_prompt")
else:
    prompt = st.chat_input("Message Qualesce Assistant...")

if prompt:

    st.session_state["messages"].append({"role": "user", "content": prompt})

    st.markdown(f'<div class="chat-bubble user-bubble">{prompt}</div>', unsafe_allow_html=True)

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
