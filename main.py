import os
import json
import tempfile
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

import pypdf
import docx
import easyocr
from groq import Groq

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

app = FastAPI()

# Initialize OCR reader locally (for image processing)
ocr_reader = easyocr.Reader(['en'], gpu=False)

# File path for persistent chat storage
SESSIONS_FILE = "sessions.json"

def load_sessions():
    """Load sessions from JSON file if exists, else initialize default"""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sessions file: {e}")
    return {
        "session_1": {
            "title": "New Chat",
            "messages": [],
            "context": ""
        }
    }

def save_sessions():
    """Save sessions to JSON file permanently"""
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving sessions file: {e}")

sessions = load_sessions()

# Global variable to store Pakistani Laws text
PAKISTAN_LAWS_CONTEXT = ""

def load_pakistan_laws():
    """App start hote hi data/ folder ki tamam PDFs aur TXT files ka text load karega"""
    global PAKISTAN_LAWS_CONTEXT
    data_dir = "data"
    extracted_laws = []

    if os.path.exists(data_dir):
        for file_name in os.listdir(data_dir):
            file_path = os.path.join(data_dir, file_name)
            
            # Read PDFs
            if file_name.endswith(".pdf"):
                try:
                    reader = pypdf.PdfReader(file_path)
                    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                    if text.strip():
                        extracted_laws.append(f"=== OFFICIAL PAKISTANI LAW: {file_name} ===\n{text}")
                except Exception as e:
                    print(f"Error reading PDF {file_name}: {e}")
            
            # Read TXT files
            elif file_name.endswith(".txt"):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        if text.strip():
                            extracted_laws.append(f"=== OFFICIAL PAKISTANI LAW: {file_name} ===\n{text}")
                except Exception as e:
                    print(f"Error reading TXT {file_name}: {e}")

    PAKISTAN_LAWS_CONTEXT = "\n\n".join(extracted_laws)
    print(f"Loaded {len(extracted_laws)} legal reference files from data/ directory.")

# On startup event
@app.on_event("startup")
async def startup_event():
    load_pakistan_laws()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/new_chat")
async def new_chat():
    session_id = f"session_{len(sessions) + 1}"
    sessions[session_id] = {
        "title": "New Chat",
        "messages": [],
        "context": ""
    }
    save_sessions()
    return JSONResponse({"session_id": session_id})

@app.get("/sessions")
async def get_sessions():
    session_list = [
        {"id": k, "title": v["title"]} 
        for k, v in sessions.items() 
        if len(v["messages"]) > 0
    ]
    return JSONResponse({"sessions": session_list})

@app.get("/get_chat")
async def get_chat(session_id: str):
    session = sessions.get(session_id, {"messages": []})
    return JSONResponse({"messages": session["messages"]})

@app.post("/chat")
async def chat(
    message: str = Form(...), 
    session_id: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    session = sessions.get(session_id)
    if not session:
        return JSONResponse({"reply": "Session error."})

    filename = None
    extracted_text = ""

    if file is not None:
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # 1. Image OCR
            if file_extension in [".png", ".jpg", ".jpeg"]:
                results = ocr_reader.readtext(tmp_path, detail=0)
                extracted_text = "\n".join(results)

            # 2. PDF Parsing
            elif file_extension == ".pdf":
                reader = pypdf.PdfReader(tmp_path)
                extracted_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

            # 3. DOCX Parsing
            elif file_extension == ".docx":
                doc = docx.Document(tmp_path)
                extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text])

            # 4. Text Files
            else:
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as txt_f:
                    extracted_text = txt_f.read()

        except Exception as e:
            print(f"File Extraction Error: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        if extracted_text.strip():
            session["context"] += f"\n\n--- Uploaded Document ({filename}) ---\n" + extracted_text

    if len(session["messages"]) == 0:
        session["title"] = message[:20] + "..." if len(message) > 20 else message

    session["messages"].append({"role": "user", "content": message, "filename": filename})
    client = Groq(api_key=groq_api_key)

    clean_msg = message.strip().lower()
    is_greeting = clean_msg in [
        "hello", "hi", "hey", "salam", "oa", "hello!", "hi!", "salam!", 
        "how r u", "how are you", "kaise ho", "kya haal hai"
    ]

    if is_greeting:
        system_persona = (
            "You are a friendly and polite AI Advisor. "
            "Respond ONLY with a direct, warm greeting matching the user's language without assuming small talk or unasked details. "
            "DO NOT mention robotic phrases like 'Pakistani legal questions' or force formal disclaimers. "
            "Examples: 'Hello! How can I assist you today?' or 'Walaikum Assalam! Main aap ki kya madad kar sakta hoon?'"
        )
        full_prompt = message
    else:
        system_persona = (
            "You are an intelligent AI Advisor specializing in Pakistani Laws.\n"
            "STRICT LANGUAGE & SCRIPT RULES:\n"
            "1. SCRIPT MATCHING: If the user query is in Roman Urdu (e.g., 'bonus r time par salary dene ka qaweene'), write 100% in Roman Urdu (English Alphabets). NEVER use Urdu script (اردو رسم الخط) anywhere in the response.\n"
            "2. ENGLISH QUERIES: If asked in English, respond strictly in English.\n\n"
            "BEHAVIOR & FORMATTING RULES:\n"
            "1. ADAPTIVE RESPONSES: For general or non-legal questions, answer naturally like a helpful assistant. Do NOT force legal disclaimers or talk about Pakistani law unless the topic requires it.\n"
            "2. CLEAN TOP TITLE: NEVER put Act names or statute citations in the main response title. Use short, direct titles like '📋 Agreement Review & Legal Risks' or '📋 Proposed Safe Clauses'.\n"
            "3. CLEAR VISUAL COMPARISON & SPACING: When presenting original vs revised clauses, create distinct visual separation:\n"
            "   - Use **❌ Maujooda Clause (Risky):** for the current text.\n"
            "   - Use **✅ Naya Safe Alternative:** for the proposed text.\n"
            "   - Add a blank line or horizontal divider between clauses so it is effortless to read.\n"
            "4. RETAIN ALL PREVIOUS STRENGTHS:\n"
            "   - Keep auto-detecting hidden risks, harsh terms, and alternatives accurately.\n"
            "   - Keep emojis and clear subheadings.\n"
            "   - No intro/outro fluff sentences."
        )

        full_prompt = f"User Query: {message}"

        if session["context"].strip():
            full_prompt += f"\n\nUSER UPLOADED CONTRACT / DOCUMENT:\n{session['context']}"

        if PAKISTAN_LAWS_CONTEXT.strip():
            full_prompt += f"\n\nREFERENCE PAKISTANI LEGAL ACTS (STATUTES):\n{PAKISTAN_LAWS_CONTEXT[:15000]}"

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_persona},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2
        )
        answer = response.choices[0].message.content
    except Exception as api_err:
        answer = f"Error generating legal advice: {str(api_err)}"

    session["messages"].append({"role": "assistant", "content": answer, "filename": None})

    # Save updated chat to file
    save_sessions()

    return JSONResponse({"reply": answer})

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    webbrowser.open("http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)