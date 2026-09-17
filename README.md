# Smart AI Legal Advisor & Contract Analyzer (Pakistan Focus)

An AI-powered legal document processing web application designed to simplify complex employment contracts, NDAs, and Pakistani Labor Laws for employees, freelancers, and small businesses.

## Project Overview

Legal contracts and employment agreements in Pakistan are often lengthy, filled with complex jargon, and difficult for non-legal individuals to understand. This application allows users to upload contracts in various formats or ask general legal questions. The system analyzes the text against Pakistani statutes, detects potentially risky clauses, and suggests safer alternatives in clear Roman Urdu or English.

## Key Features

- **Multi-Format Processing**: Supports PDF, DOCX, TXT, and  contract images via OCR.
- **Localized Pakistani Legal Context**: Integrated reference statutes such as Payment of Wages Act 1936, Factories Act 1934, Maternity Benefit Ordinance 1958, Contract Act 1872, and Companies Act 2017.
- **Visual Clause Risk Detection**: Identifies risky clauses and presents side-by-side visual comparisons (**❌ Maujooda Clause** vs **✅ Naya Safe Alternative**).
- **Strict Language & Script Matching**: Guarantees 100% Roman Urdu or English output based on user query without mixing Urdu script (اردو).
- **Persistent Session Storage**: Stores chat and analysis history locally in `sessions.json` across browser reloads and server restarts.

## Technology Stack

- **Backend Framework**: FastAPI (Python)
- **LLM Engine**: Groq API (`openai/gpt-oss-120b`)
- **Parsers & OCR**: PyPDF, python-docx, EasyOCR
- **Frontend**: HTML5, CSS3, JavaScript
- **Storage**: JSON-based session handling (`sessions.json`)

## Project Structure


LEGAL-AI-ADVISOR/
│
├── data/                  # Local legal reference statutes (PDFs/TXT)
├── templates/
│   └── index.html         # Frontend interface
├── main.py                # Core FastAPI application & routes
├── requirements.txt       # Python dependencies
├── sessions.json          # Persistent chat storage
├── README.md              # Project documentation
└── .env                   # Environment variables (API Key)


Installation & Setup:
1. Clone the Repository
Bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd LEGAL-AI-ADVISOR

2. Create and Activate Virtual Environment
Bash:
python -m venv .venv
# On Windows:
.venv\Scripts\activate

3. Install Dependencies:
Bash
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root directory:

Code snippet
GROQ_API_KEY=your_groq_api_key_here


How to Run
Start the FastAPI application using uvicorn:

Bash
uvicorn main:app --reload
Open your browser and navigate to http://127.0.0.1:8000.

How to Use
Open the application in your browser.

Upload a supported contract document (PDF, DOCX, or Image).

Type a legal query or ask for a contract risk analysis in Roman Urdu or English.

Review the detected risks, explanations, and suggested safe alternatives.

Project Outcome:
The outcome is a fully functional AI Legal Advisor that simplifies contract review, detects risky terms using Pakistani legal context, and provides persistent, multi-format document analysis.