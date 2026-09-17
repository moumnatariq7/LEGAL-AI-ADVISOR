import os
import re
import pandas as pd
from pypdf import PdfReader  # PDF read karne ka tool

# 1. Cleaning Function
def clean_legal_text(raw_text):
    text = re.sub(r'\s+', ' ', raw_text) # Extra spaces aur enters khatam
    text = re.sub(r'[^\w\s\d.,;:\-\'\"\(\)]', '', text) # Fuzool symbols hataye
    return text.strip()

# 2. Main Pipeline for PDF
def run_pdf_pipeline(pdf_name):
    # Output folder check karna
    os.makedirs("output", exist_ok=True)
    
    input_path = os.path.join("data", pdf_name)
    
    # Check karna agar file maujood hai
    if not os.path.exists(input_path):
        print(f"❌ Error: In'data' folder  '{pdf_name}'   file not found")
        return

    print(f"🚀 extracting text from '{pdf_name}'...")
    
    # PDF se text read karna (Original file ko kuch nahi hoga)
    reader = PdfReader(input_path)
    raw_content = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            raw_content += text + "\n"
            
    print("🧹 Data Science Layer: cleaning text...")
    cleaned_content = clean_legal_text(raw_content)
    
    # Saaf kiya hua text alag file mein save karna
    output_txt_path = os.path.join("output", f"cleaned_{pdf_name.replace('.pdf', '.txt')}")
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(cleaned_content)
    
    # Log report banana (Sirf length save hogi)
    df = pd.DataFrame([{
        "File_Name": pdf_name,
        "Original_Length": len(raw_content),
        "Cleaned_Length": len(cleaned_content)
    }])
    df.to_csv("output/data_processing_log.csv", index=False)
    
    print("✅ WEEK 1 TOTAL SUCCESS!")
    print(f"📁 clear and new text saver here: {output_txt_path}")
    print(f"📄 your original pdf '{pdf_name}' data remains unchanged and completely safe ")

if __name__ == "__main__":
    # Agar aapne file ka naam badal kar kuch aur rakha hai toh yahan wo likhein
    run_pdf_pipeline("my_contract.pdf")
