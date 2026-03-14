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

class NoteAnalysis(BaseModel):
    note_index: int
    severity: str = Field(..., pattern="^(Good|Flagged)$")
    reason: str

class TranscriptAnalysisResponse(BaseModel):
    notes_analysis: List[NoteAnalysis]

def analyze_transcript(data: dict) -> TranscriptAnalysisResponse:
    prompt = f"""
    You are given session notes and corresponding call details and transcripts recorded by the Housing Coordinator.
    Analyze each note and determine if there is a corresponding call session within 60 minutes.
    
    Session Notes: {json.dumps(data.get('notes', []), indent=2)}
    Call Transcripts: {json.dumps(data.get('call_transcripts', []), indent=2)}
    
    Follow the rules:
    - If time difference <= 5 mins, mark 'Good'.
    - If difference > 5 mins, mark 'Flagged'.
    - If Service Type is Direct/In Person or Indirect, mark 'Good' without call verification.
    - If Direct Remote, verify call records.
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06", # Using model that supports Structured Outputs
        messages=[
            {"role": "system", "content": "You are a specialized housing coordinator QA analyzer."},
            {"role": "user", "content": prompt}
        ],
        response_format=TranscriptAnalysisResponse,
    )
    return completion.choices[0].message.parsed

def main():
    input_folder = "data/notes/filtered_notes/"
    output_folder = "AI Revised 1"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
            
        data = safe_load_json(os.path.join(input_folder, filename))
        if not data:
            continue

        print(f"Analyzing transcripts for {filename}...")
        results = analyze_transcript(data)
        
        # Update data
        for analysis in results.notes_analysis:
            if analysis.note_index < len(data["notes"]):
                data["notes"][analysis.note_index]["transcript_severity"] = analysis.severity
                data["notes"][analysis.note_index]["transcript_reason"] = analysis.reason

        safe_save_json(data, os.path.join(output_folder, filename))
        time.sleep(1)

if __name__ == "__main__":
    main()
