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

class EndTimeNoteAnalysis(BaseModel):
    note_index: int
    end_severity: str = Field(..., pattern="^(Good|Flagged)$")
    end_reason: str

class EndTimeAnalysisResponse(BaseModel):
    time_analysis: List[EndTimeNoteAnalysis]

def analyze_end_time(data: dict) -> EndTimeAnalysisResponse:
    prompt = f"""
    Evaluate accuracy of employee added end times.
    Check Sequence: Update Creation Time vs End Time.
    Rule: End Time should be within 20 mins before Update Creation Time.
    If yes, mark 'Good'. Otherwise 'Flagged' with reason.
    Use 12H format in reasons.
    
    Session Notes: {json.dumps(data.get('notes', []), indent=2)}
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an Employee End Time Checker."},
            {"role": "user", "content": prompt}
        ],
        response_format=EndTimeAnalysisResponse,
    )
    return completion.choices[0].message.parsed

def main():
    input_folder = "AI Revised 2"
    output_folder = "AI Revised 3"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
            
        data = safe_load_json(os.path.join(input_folder, filename))
        print(f"Analyzing end times for {filename}...")
        results = analyze_end_time(data)
        
        for analysis in results.time_analysis:
            idx = analysis.note_index
            if idx < len(data["notes"]):
                data["notes"][idx]["end_severity"] = analysis.end_severity
                data["notes"][idx]["end_reason"] = analysis.end_reason

        safe_save_json(data, os.path.join(output_folder, filename))
        time.sleep(1)

if __name__ == "__main__":
    main()
