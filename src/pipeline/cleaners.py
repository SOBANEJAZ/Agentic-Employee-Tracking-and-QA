import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pytz import timezone
from src.core.utils import (
    convert_utc_to_cst,
    parse_monday_date_value,
    parse_monday_time_value
)

logger = logging.getLogger(__name__)

class DataCleaner:
    @staticmethod
    def clean_monday_notes(raw_board_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidates logic from 03_notes_cleaner.py.
        Standardizes raw Monday.com item data into a clean dictionary.
        """
        cleaned_notes = []
        for board in raw_board_data:
            # Note: raw_board_data is assumed to be the list of items from a board
            # If it's the full GraphQL response, we'd need to traverse it.
            # Assuming MondayClient.fetch_items already returns a flat list of items.
            for item in board: # Assuming board is a list of items for a board
                column_values = {cv["column"]["title"]: cv for cv in item.get("column_values", [])}
                
                date = parse_monday_date_value(column_values.get("Date", {}).get("value"))
                start_time = parse_monday_time_value(column_values.get("Start Time", {}).get("value"))
                end_time = parse_monday_time_value(column_values.get("End Time", {}).get("value"))

                # Logic to get units from various possible column names
                manual_units = (
                    column_values.get("Manual units", {}).get("value")
                    or column_values.get("Units", {}).get("value")
                    or column_values.get("Manual Units", {}).get("value")
                )

                def get_status_label(status_cv: Optional[Dict[str, Any]]) -> Optional[str]:
                    # Extract label from Monday's StatusValue type
                    if status_cv and "label" in status_cv:
                        return status_cv["label"]
                    return None

                cleaned_note = {
                    "item_name": item.get("name"),
                    "item_id": item.get("id"),
                    "session_creation_time": convert_utc_to_cst(item.get("created_at")),
                    "date": date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "manual_units": manual_units,
                    "service_type": get_status_label(column_values.get("Service Type")),
                    "provided_as": get_status_label(column_values.get("Provided As")),
                    "session_status": get_status_label(column_values.get("Session Status")),
                    "update_text_body": item.get("updates", [{}])[-1].get("text_body") if item.get("updates") else None,
                }
                cleaned_notes.append(cleaned_note)
        return cleaned_notes

    @staticmethod
    def filter_by_date(notes: List[Dict[str, Any]], days_offset: int = 16) -> List[Dict[str, Any]]:
        """Filters notes based on a target date calculated from offset."""
        cst_tz = timezone("US/Central")
        target_date = (datetime.now(cst_tz) - timedelta(days=days_offset)).strftime("%Y-%m-%d")
        return [n for n in notes if n.get("date") == target_date]

    @staticmethod
    def clean_transcripts(calls: List[Dict[str, Any]], staff_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidates 08_call_transcript_cleaner.py.
        Formats transcripts and identifies speakers.
        """
        staff_numbers = {s["number"] for s in staff_info if "number" in s}
        
        for call in calls:
            transcript_data = call.get("call_transcript")
            if transcript_data and "data" in transcript_data and "dialogue" in transcript_data["data"]:
                dialogue = transcript_data["data"]["dialogue"]
                formatted_conversation = []
                for entry in dialogue:
                    speaker = "Staff Member" if entry.get("identifier") in staff_numbers else "Client"
                    formatted_conversation.append({
                        "speaker": speaker,
                        "message": entry.get("content")
                    })
                call["call_transcript"] = {"conversation": formatted_conversation}
        return calls
