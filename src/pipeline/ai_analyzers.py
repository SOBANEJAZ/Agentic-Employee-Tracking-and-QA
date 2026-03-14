import os
import logging
from typing import List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SingleNoteAudit(BaseModel):
    note_index: int
    
    # 1. Transcript Analysis
    transcript_severity: str = Field(..., pattern="^(Good|Flagged)$")
    transcript_reason: str
    
    # 2. Start Time Analysis
    start_severity: str = Field(..., pattern="^(Good|Flagged)$")
    start_reason: str
    
    # 3. End Time Analysis
    end_severity: str = Field(..., pattern="^(Good|Flagged)$")
    end_reason: str
    
    # 4. Service Type Analysis
    service_severity: str = Field(..., pattern="^(Good|Flagged)$")
    service_reason: str
    
    # 5. Billing Analysis
    bill_severity: str = Field(..., pattern="^(Good|Flagged)$")
    bill_reason: str
    
    # 6. Column Compliance Analysis
    column_severity: str = Field(..., pattern="^(Good|Flagged)$")
    column_reason: str

class BatchAuditResponse(BaseModel):
    audits: List[SingleNoteAudit]

class AIAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPEN_AI_API"))
        self.model = "gpt-4o-2024-08-06"

    def audit_notes(self, notes: List[dict], call_transcripts: List[dict]) -> List[dict]:
        """
        Performs a comprehensive audit on a batch of session notes.
        Consolidates logic from all 10_ai_* scripts into a single structured call.
        """
        if not notes:
            return []

        prompt = f"""
        Perform a comprehensive QA audit on the following Housing Coordinator session notes.
        Verify against the provided call transcripts and logical rules.

        Auditing Rules:
        1. TRANSCRIPT: Verify if session notes reflect actual conversation. (Good if match, else Flagged).
        2. START TIME: Session creation must be within 20 mins after start time.
        3. END TIME: End time must be within 20 mins before update creation time.
        4. SERVICE: Verify if Service Line (Stabilization/Transition/Consultation) matches content.
        5. BILLING: 1 unit = 15 mins. Verify if units match duration described in context.
        6. COMPLIANCE: Ensure all required fields (times, service types, units) are filled.

        Session Notes: {notes}
        Call Transcripts: {call_transcripts}
        """

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional Housing Service QA and Billing Auditor."},
                    {"role": "user", "content": prompt}
                ],
                response_format=BatchAuditResponse,
            )
            
            audit_results = completion.choices[0].message.parsed.audits
            
            # Merge results back into the notes objects
            for audit in audit_results:
                if audit.note_index < len(notes):
                    notes[audit.note_index].update(audit.model_dump())
            
            return notes

        except Exception as e:
            logger.error(f"AI Audit failed: {e}")
            return notes
