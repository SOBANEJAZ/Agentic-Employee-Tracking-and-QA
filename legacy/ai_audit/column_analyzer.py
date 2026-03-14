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

class ColumnAnalysis(BaseModel):
    note_index: int
    column_severity: str = Field(..., pattern="^(Good|Flagged)$")
    column_reason: str

class ColumnAnalysisResponse(BaseModel):
    column_analysis: List[ColumnAnalysis]

def analyze_columns(data: dict) -> ColumnAnalysisResponse:
    prompt = f"""
    Verify if all required columns are correctly filled.
    Required: start_time, end_time, manual_units, service_type, provided_as, service_line, session_status.
    
    Session Notes: {json.dumps(data.get('notes', []), indent=2)}
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a Monday.com Data Compliance Officer."},
            {"role": "user", "content": prompt}
        ],
        response_format=ColumnAnalysisResponse,
    )
    return completion.choices[0].message.parsed

def main():
    input_folder = "AI Revised 5"
    output_folder = "AI Revised 6"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
            
        data = safe_load_json(os.path.join(input_folder, filename))
        print(f"Analyzing columns for {filename}...")
        results = analyze_columns(data)
        
        for analysis in results.column_analysis:
            idx = analysis.note_index
            if idx < len(data["notes"]):
                data["notes"][idx]["column_severity"] = analysis.column_severity
                data["notes"][idx]["column_reason"] = analysis.column_reason

        safe_save_json(data, os.path.join(output_folder, filename))
        time.sleep(1)

if __name__ == "__main__":
    main()
