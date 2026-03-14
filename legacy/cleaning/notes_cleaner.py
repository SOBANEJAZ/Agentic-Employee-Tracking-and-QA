import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from pytz import timezone
import pytz
from src.core.utils import (
    convert_utc_to_cst,
    parse_monday_date_value,
    parse_monday_time_value,
    safe_load_json,
    safe_save_json
)

class DataProcessor:
    def __init__(self, json_data: dict):
        self.data = json_data

    def extract_item_data(self, item: dict) -> dict:
        """Extract relevant data from a Monday.com item."""
        column_values = {cv["column"]["title"]: cv for cv in item.get("column_values", [])}

        date = parse_monday_date_value(column_values.get("Date", {}).get("value"))
        start_time = parse_monday_time_value(column_values.get("Start Time", {}).get("value"))
        end_time = parse_monday_time_value(column_values.get("End Time", {}).get("value"))

        manual_units = (
            column_values.get("Manual units", {}).get("value")
            or column_values.get("Units", {}).get("value")
            or column_values.get("Manual Units", {}).get("value")
        )

        def get_label(status_dict):
            return status_dict.get("label")

        return {
            "item_name": item.get("name"),
            "item_id": item.get("id"),
            "session_creation_time": convert_utc_to_cst(item.get("created_at")),
            "update_creation_time": convert_utc_to_cst(item.get("updates", [{}])[-1].get("created_at")) if item.get("updates") else None,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "manual_units": manual_units,
            "service_type": get_label(column_values.get("Service Type", {})),
            "provided_as": get_label(column_values.get("Provided As", {})),
            "service_line": get_label(column_values.get("Service Line", {})),
            "session_status": get_label(column_values.get("Session Status", {})),
            "signature": get_label(column_values.get("Signature", {})),
            "update_text_body": item.get("updates", [{}])[-1].get("text_body") if item.get("updates") else None,
        }

    def process(self) -> list:
        """Process the entire JSON structure."""
        result = []
        for board in self.data.get("data", {}).get("boards", []):
            for group in board.get("groups", []):
                group_title = group.get("title")
                for item in group.get("items_page", {}).get("items", []):
                    item_data = self.extract_item_data(item)
                    item_data["group_title"] = group_title
                    result.append(item_data)
        return result

def filter_by_date(data: list, target_date: str) -> list:
    """Filter list based on date."""
    return [item for item in data if item.get("date") == target_date]

def main(days_offset: int = 16):
    cst_tz = timezone("US/Central")
    target_date = (datetime.now(cst_tz) - timedelta(days=days_offset)).strftime("%Y-%m-%d")
    print(f"Processing notes for date: {target_date} (Offset: {days_offset} days)")

    raw_dir = Path("data/notes/raw_notes")
    cleaned_dir = Path("data/notes/cleaned_notes")
    filtered_dir = Path("data/notes/filtered_notes")

    for d in [cleaned_dir, filtered_dir]:
        d.mkdir(parents=True, exist_ok=True)

    for file_path in raw_dir.glob("*.json"):
        print(f"Cleaning {file_path.name}...")
        raw_data = safe_load_json(str(file_path))
        processor = DataProcessor(raw_data)
        processed_data = processor.process()
        
        # Save cleaned
        clean_path = cleaned_dir / file_path.name
        safe_save_json(processed_data, str(clean_path))

        # Filter and save
        filtered_data = filter_by_date(processed_data, target_date)
        filter_path = filtered_dir / file_path.name
        safe_save_json(filtered_data, str(filter_path))
        print(f"Saved {len(filtered_data)} filtered records to {filter_path}")

if __name__ == "__main__":
    import sys
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    main(offset)
