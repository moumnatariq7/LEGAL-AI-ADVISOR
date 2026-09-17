import os
from dotenv import load_dotenv
from groq import Groq

# 1. Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ Error: GROQ_API_KEY not found in .env file!")
    exit()

# 2. Initialize Direct Groq Client
client = Groq(api_key=api_key)

def analyze_legal_text(cleaned_text):
    # Truncate text to a safe length
    max_chars = 3000
    if len(cleaned_text) > max_chars:
        print(f"⚠️ Document is large ({len(cleaned_text)} chars). Analyzing the first {max_chars} characters for test run...\n")
        cleaned_text = cleaned_text[:max_chars]

    prompt = f"""
    You are an expert Senior Corporate Lawyer. Analyze the following legal document extract:

    ---
    {cleaned_text}
    ---

    Perform the following actions:
    1. Summarize the key obligations of all involved parties.
    2. Identify any risky clauses, hidden penalties, unfavorable terms, or legal pitfalls.
    3. Suggest safer alternative wording/remedies for identified risks.

    Provide the output clearly structured in professional Markdown format.
    """
    
    # 3. Direct API Call using active model from your account
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are an expert AI Legal Advisor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    
    return completion.choices[0].message.content

# 4. Execution using Week 1 pipeline output
if __name__ == "__main__":
    sample_file_path = os.path.join("output", "cleaned_my_contract.txt")
    
    if os.path.exists(sample_file_path):
        with open(sample_file_path, "r", encoding="utf-8") as f:
            cleaned_contract = f.read()
            
        print("🤖 AI Legal Specialist is analyzing the contract...\n")
        analysis_result = analyze_legal_text(cleaned_contract)
        
        print("=== LEGAL RISK ANALYSIS REPORT ===")
        print(analysis_result)
    else:
        print(f"⚠️ File '{sample_file_path}' not found. Please run Week 1 code first!")