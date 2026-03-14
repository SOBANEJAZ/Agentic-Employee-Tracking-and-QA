import json
import os
import time
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from src.core.utils import safe_load_json, safe_save_json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPEN_AI_API"))

class BillAnalysis(BaseModel):
    note_index: int
    bill_severity: str = Field(..., pattern="^(Good|Flagged)$")
    bill_reason: str

class BillAnalysisResponse(BaseModel):
    bill_analysis: List[BillAnalysis]

def analyze_bills(data: dict) -> BillAnalysisResponse:
    prompt = f"""
    Review session notes for billing accuracy.
    Compare manual_units with the detail provided in the update_text_body.
    One unit = 15 mins.
    If units match duration of activity described, 'Good'.
    If overbilling or mismatch, 'Flagged'.
    
    Session Notes: {json.dumps(data.get('notes', []), indent=2)}
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a Housing Billing Auditor."},
            {"role": "user", "content": prompt}
        ],
        response_format=BillAnalysisResponse,
    )
    return completion.choices[0].message.parsed

def main():
    input_folder = "AI Revised 4"
    output_folder = "AI Revised 5"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
            
        data = safe_load_json(os.path.join(input_folder, filename))
        print(f"Analyzing bills for {filename}...")
        results = analyze_bills(data)
        
        for analysis in results.bill_analysis:
            idx = analysis.note_index
            if idx < len(data["notes"]):
                data["notes"][idx]["bill_severity"] = analysis.bill_severity
                data["notes"][idx]["bill_reason"] = analysis.bill_reason

        safe_save_json(data, os.path.join(output_folder, filename))
        time.sleep(1)

if __name__ == "__main__":
    main()