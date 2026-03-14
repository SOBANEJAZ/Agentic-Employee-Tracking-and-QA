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

class StartTimeNoteAnalysis(BaseModel):
    note_index: int
    start_severity: str = Field(..., pattern="^(Good|Flagged)$")
    start_reason: str

class StartTimeAnalysisResponse(BaseModel):
    time_analysis: List[StartTimeNoteAnalysis]

def analyze_start_time(data: dict) -> StartTimeAnalysisResponse:
    prompt = f"""
    Evaluate accuracy of employee added times.
    Check Sequence: Session Creation Time vs Start Time.
    If Session Creation Time is before Start Time within 20 mins, mark 'Good'.
    Otherwise 'Flagged'. 
    Use 12H format in reasons.
    
    Session Notes: {json.dumps(data.get('notes', []), indent=2)}
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an Employee Time Checker."},
            {"role": "user", "content": prompt}
        ],
        response_format=StartTimeAnalysisResponse,
    )
    return completion.choices[0].message.parsed

def main():
    input_folder = "AI Revised 1"
    output_folder = "AI Revised 2"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
            
        data = safe_load_json(os.path.join(input_folder, filename))
        print(f"Analyzing start times for {filename}...")
        results = analyze_start_time(data)
        
        for analysis in results.time_analysis:
            idx = analysis.note_index
            if idx < len(data["notes"]):
                data["notes"][idx]["start_severity"] = analysis.start_severity
                data["notes"][idx]["start_reason"] = analysis.start_reason

        safe_save_json(data, os.path.join(output_folder, filename))
        time.sleep(1)

if __name__ == "__main__":
    main()
