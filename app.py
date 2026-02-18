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
 
if "pending_prompt" not in st.session_state:
    st.session_state["pending_prompt"] = None
 
 
# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
 
.stApp { background-color: #f4f6f9; }
 
section[data-testid="stSidebar"] { background-color: #e9eef6; }
 
.block-container { padding-top: 1rem; padding-bottom: 6rem; }
 
/* Center Login Screen */
.login-center {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    margin-top: 80px;
    padding-left: 200px;        
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
 
/* Suggestion Bubble Style */
.suggestion-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
    margin-bottom: 15px;
}
 
div.stButton > button {
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 13px;
    background: linear-gradient(135deg, #0b3c6d, #1f5ea8);
    color: white;
    border: none;
    transition: all 0.25s ease;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
 
div.stButton > button:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    background: linear-gradient(135deg, #1f5ea8, #0b3c6d);
}
 
/* Chat input fixed */
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
}
 
</style>
""", unsafe_allow_html=True)
 
 
# ---------------- Authentication ----------------
if not st.session_state["authenticated"]:
 
    st.markdown('<div class="login-center">', unsafe_allow_html=True)
 
    col1, col2, col3 = st.columns([5, 4, 6])
 
    with col2:
 
        st.markdown("""
            <div style="margin-top:40px;">
                <h2 style="color:#0b3c6d;">🔐 Qualesce Smart Assist</h2>
            </div>
            <div style="margin-top:40px;">
                <h2 style="color:#0b3c6d;"> Login</h2>
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
 
    st.markdown('</div>', unsafe_allow_html=True)
 
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
 
 
# ---------------- Suggested Questions ----------------
st.markdown("### 💡 Suggested Questions")
 
suggestions = [
    "Explain the PO Parking automation process",
    "How does Job Scheduling Cancelled Notification work?",
    "Describe the Greeting Birthday Mail workflow",
    "What is the Vendor Confirmation process?",
    "Explain Ex-factor and HUB sales automation",
    "What are the exception handling strategies?",
    "What ROI benefits does Qualesce deliver?",
    "Which SAP T-codes are used in our automations?"
]
 
st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
 
for question in suggestions:
    if st.button(question, key=f"suggestion_{question}"):
        st.session_state["pending_prompt"] = question
        st.rerun()
 
st.markdown('</div>', unsafe_allow_html=True)
 
 
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
 