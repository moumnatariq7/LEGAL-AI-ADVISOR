import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from groq import Groq

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Legal AI Advisor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. Custom CSS (Absolute Positioning inside Input Bar + Hero Styling)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Dark Theme Setup */
    .stApp {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }
    
    /* Center Screen Hero Title */
    .hero-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 40vh;
        text-align: center;
    }
    
    .hero-title {
        font-size: 2.6rem;
        font-weight: 700;
        color: #38bdf8;
        letter-spacing: -0.5px;
        animation: fadeIn 0.8s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stChatMessage"] {
        background-color: #1e293b;
        border-radius: 12px;
        border: 1px solid #334155;
        padding: 0.85rem 1.2rem;
        margin-bottom: 0.75rem;
        color: #f8fafc;
    }

    /* Target Bottom Chat Container */
    div[data-testid="stBottom"] {
        background-color: transparent !important;
    }

    div[data-testid="stBottom"] > div {
        position: relative !important;
    }

    /* Make Input Box have padding on the left for the icon */
    .stChatInputContainer {
        border-radius: 28px !important;
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        padding-left: 3rem !important;
    }

    .stChatInputContainer textarea {
        color: #f8fafc !important;
    }

    /* Sidebar Title Styling - Shows at top */
    [data-testid="stSidebarContent"] h1 {
        font-size: 0.95rem !important;
        color: #38bdf8 !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 250px !important;
        background-color: #1e293b !important;
        padding: 1rem !important;
        z-index: 1000 !important;
        border-bottom: 1px solid #334155 !important;
    }

    /* Hide sidebar caption */
    [data-testid="stSidebarContent"] .stCaption {
        display: none !important;
    }

    /* Adjust sidebar content padding for fixed title */
    [data-testid="stSidebarContent"] {
        padding-top: 70px !important;
    }

    /* Force the Popover + Button INSIDE the Input Bar on the Left */
    div[data-testid="stPopover"] {
        position: absolute !important;
        left: 12px !important;
        bottom: 12px !important;
        z-index: 99999 !important;
    }

    div[data-testid="stPopover"] > button {
        background-color: transparent !important;
        color: #94a3b8 !important;
        border: none !important;
        border-radius: 6px !important;
        width: 32px !important;
        height: 32px !important;
        font-size: 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        line-height: 1 !important;
        cursor: pointer !important;
    }

    div[data-testid="stPopover"] > button:hover {
        color: #38bdf8 !important;
        background-color: #334155 !important;
    }

    /* Sidebar buttons */
    .stSidebar .stButton>button {
        background-color: transparent;
        color: #cbd5e1;
        border: 1px solid #334155;
        text-align: left;
        justify-content: flex-start;
        padding: 0.5rem 0.8rem;
        border-radius: 8px;
    }
    
    .stSidebar .stButton>button:hover {
        background-color: #334155;
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. Setup & State Management
# -----------------------------------------------------------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY environment variable missing!")
    st.stop()

@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embeddings = load_embeddings()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = "session_1"
    st.session_state.chat_history["session_1"] = {
        "title": "New Chat",
        "messages": [],
        "retriever": None
    }

current_id = st.session_state.current_session_id
current_chat = st.session_state.chat_history[current_id]

# -----------------------------------------------------------------------------
# 4. Sidebar History
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚖️ Legal AI Advisor")
    st.caption("v2.0 • Assistant")
    st.markdown("---")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"session_{len(st.session_state.chat_history) + 1}"
        st.session_state.chat_history[new_id] = {
            "title": "New Chat",
            "messages": [],
            "retriever": None
        }
        st.session_state.current_session_id = new_id
        st.rerun()

    st.markdown("---")
    st.subheader("📜 Recent Chats")
    
    for session_id, session_data in list(st.session_state.chat_history.items())[::-1]:
        title = session_data["title"]
        display_label = f"💬 **{title}**" if session_id == current_id else f"💬 {title}"
            
        if st.button(display_label, key=session_id, use_container_width=True):
            st.session_state.current_session_id = session_id
            st.rerun()

# -----------------------------------------------------------------------------
# 5. Centered Hero Header
# -----------------------------------------------------------------------------
if len(current_chat["messages"]) == 0:
    st.markdown("""
        <div class="hero-wrapper">
            <div class="hero-title">How can I assist you today?</div>
        </div>
    """, unsafe_allow_html=True)

for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------------------------------------------------------
# 6. Embedded Plus Popover inside Chat Bar
# -----------------------------------------------------------------------------
with st.popover("＋", help="Upload File"):
    st.write("### Attach Document")
    uploaded_file = st.file_uploader(
        "Select contract or legal file (.pdf, .docx, .txt)",
        type=["txt", "pdf", "docx"],
        key=f"uploader_{current_id}"
    )
    
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        with st.spinner("Processing file..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            try:
                if file_extension == ".pdf":
                    loader = PyPDFLoader(tmp_path)
                elif file_extension == ".docx":
                    loader = Docx2txtLoader(tmp_path)
                else:
                    loader = TextLoader(tmp_path, encoding="utf-8")
                    
                documents = loader.load()
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = text_splitter.split_documents(documents)

            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=f"./chroma_db_{current_id}"
            )
            
            current_chat["retriever"] = vectorstore.as_retriever(search_kwargs={"k": 3})
            st.success(f"✅ Attached: {uploaded_file.name}")

if prompt := st.chat_input("Ask a question..."):
    if len(current_chat["messages"]) == 0:
        current_chat["title"] = prompt[:24] + "..." if len(prompt) > 24 else prompt

    current_chat["messages"].append({"role": "user", "content": prompt})
    
    client = Groq(api_key=groq_api_key)
    conversation_history = []
    for msg in current_chat["messages"][-6:]:
        conversation_history.append({"role": msg["role"], "content": msg["content"]})
    
    if current_chat["retriever"] is not None:
        try:
            relevant_docs = current_chat["retriever"].invoke(prompt)
            context = "\n".join([doc.page_content for doc in relevant_docs])

            system_prompt = f"""
You are an intelligent Legal AI Advisor. Answer questions naturally.
If relevant to the attached document, strictly base your answers on the provided context below.

Context:
{context}
"""
            messages_for_api = [{"role": "system", "content": system_prompt}] + conversation_history
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages_for_api,
                temperature=0.3
            )
            answer = response.choices[0].message.content

        except Exception as e:
            answer = f"An error occurred: {str(e)}"
    else:
        try:
            system_prompt = """
You are a helpful, professional Legal AI Assistant. Engage in natural, intelligent conversation with the user.
"""
            messages_for_api = [{"role": "system", "content": system_prompt}] + conversation_history
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages_for_api,
                temperature=0.4
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"An error occurred: {str(e)}"

    current_chat["messages"].append({"role": "assistant", "content": answer})
    st.rerun()