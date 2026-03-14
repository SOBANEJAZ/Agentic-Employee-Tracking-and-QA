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

class ServiceAnalysis(BaseModel):
    note_index: int
    service_severity: str = Field(..., pattern="^(Good|Flagged)$")
    service_reason: str

class ServiceAnalysisResponse(BaseModel):
    service_analysis: List[ServiceAnalysis]

def analyze_service(data: dict) -> ServiceAnalysisResponse:
    prompt = f"""
    Review session notes and verify if Service Line and Service Type are correct.
    
    Definitions:
    - Housing Stabilization: Helping client maintain housing.
    - Housing Transition: Helping client find housing.
    - Housing Consultation: Assisting with paperwork/eligibility.
    
    Session Notes: {json.dumps(data.get('notes', []), indent=2)}
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a Housing Service Specialist."},
            {"role": "user", "content": prompt}
        ],
        response_format=ServiceAnalysisResponse,
    )
    return completion.choices[0].message.parsed

def main():
    input_folder = "AI Revised 3"
    output_folder = "AI Revised 4"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
            
        data = safe_load_json(os.path.join(input_folder, filename))
        print(f"Analyzing services for {filename}...")
        results = analyze_service(data)
        
        for analysis in results.service_analysis:
            idx = analysis.note_index
            if idx < len(data["notes"]):
                data["notes"][idx]["service_severity"] = analysis.service_severity
                data["notes"][idx]["service_reason"] = analysis.service_reason

        safe_save_json(data, os.path.join(output_folder, filename))
        time.sleep(1)

if __name__ == "__main__":
    main()
