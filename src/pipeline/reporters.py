import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.core.monday_client import MondayClient

logger = logging.getLogger(__name__)

# Constants and Mappings (Consolidated from 13.py)
SERVICE_TYPE_MAP = {"Transitioning": "1", "Sustaining": "0", "Consultation": "2"}
PROVIDED_AS_MAP = {"Direct/Remote": "0", "Direct Remote": "0", "indirect": "1", "Direct/In-Person": "3"}
FLAG_MAP = {"Good": "1", "Flagged": "0"}
TRANSCRIPT_FLAG_MAP = {"Good": "2", "Flagged": "0"}
SEVERITY_MAP = {"Flagged": "0", "Good": "3"} # Simplified

class Reporter:
    def __init__(self, monday_client: MondayClient):
        self.monday = monday_client
        self.report_board_id = 8139951792 # From 13.py

    def upload_qa_report(self, audited_notes: List[Dict[str, Any]]):
        """
        Consolidates logic from 13.py.
        Updates Monday.com with QA results.
        """
        for note in audited_notes:
            group_id = note.get("group_name")
            if not group_id:
                continue

            item_name = note.get("group_title", "Daily QA Report")
            item_id = self.monday.create_item(self.report_board_id, group_id, item_name)
            
            if not item_id:
                logger.error(f"Failed to create report item for {item_name}")
                continue

            # Update various columns based on audit results
            updates = {
                "date": note.get("date"),
                "status80": SERVICE_TYPE_MAP.get(note.get("service_type"), "2"),
                "status4": PROVIDED_AS_MAP.get(note.get("provided_as"), "0"),
                "severity_flags_mkks6sc7": TRANSCRIPT_FLAG_MAP.get(note.get("transcript_severity"), "2"),
                "issue_description_mkm0j7qm": note.get("transcript_reason"),
                "text_mkm1vk1y": note.get("start_reason"),
                "text_mkm1d8wd": note.get("end_reason"),
                "dup__of_severity_flags_mkm19yh": SEVERITY_MAP.get(note.get("start_severity"), "3"),
                "status_mkm1fy0n": SEVERITY_MAP.get(note.get("end_severity"), "3"),
                "text_mkm2sxx6": note.get("bill_reason"),
                "status_mkm2zs2v": "1" if note.get("bill_severity") == "Good" else "2",
                "long_text_mkm545rp": note.get("service_reason"),
                "status_mkm64aec": FLAG_MAP.get(note.get("service_severity"), "1"),
                "status_mkm5aj0m": FLAG_MAP.get(note.get("column_severity"), "1")
            }

            for col_id, value in updates.items():
                if value is not None:
                    self.monday.update_column_value(self.report_board_id, item_id, col_id, str(value))

    def upload_unit_report(self, board_id: int, aggregated_units: List[Dict[str, Any]]):
        """Consolidates logic from 14_units_monday.py."""
        for entry in aggregated_units:
            group_id = entry.get("group_name")
            item_id = self.monday.create_item(board_id, group_id, "Daily Units Report")
            if item_id:
                self.monday.update_column_value(board_id, item_id, "numbers_mkm6axzx", str(entry.get("total_units", 0)))
                self.monday.update_column_value(board_id, item_id, "status_mkm61j", FLAG_MAP.get(entry.get("units_status"), "1"))
