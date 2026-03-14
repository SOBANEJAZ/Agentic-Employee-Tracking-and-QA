import os
import json
from datetime import datetime, timedelta
from pytz import timezone
from src.core.monday_client import MondayClient
from src.core.utils import safe_load_json

def main(days_offset: int = 16):
    cst = timezone("US/Central")
    target_date = (datetime.now(cst) - timedelta(days=days_offset)).strftime("%Y-%m-%d")
    print(f"Uploading units for date: {target_date}")

    client = MondayClient()
    input_dir = "Output_units"
    board_id = 8198737855
    
    # Status mapping for Daily Units Report
    FLAG_MAP = {"Good": "1", "Flagged": "0"}

    for filename in os.listdir(input_dir):
        if not filename.endswith(".json"):
            continue
            
        data = safe_load_json(os.path.join(input_dir, filename))
        notes = data.get("notes", [])
        if not notes:
            continue

        group_id = notes[0].get("group_name")
        if not group_id:
            continue

        for note in notes:
            # Create item
            item_id = client.create_item(board_id, group_id, "Daily Units Report")
            if not item_id:
                continue

            # Update columns
            client.update_column_value(board_id, item_id, "date4", target_date)
            
            total_units = note.get("total_units")
            if total_units is not None:
                client.update_column_value(board_id, item_id, "numbers_mkm6axzx", str(total_units))

            status = note.get("units_status")
            if status:
                client.update_column_value(board_id, item_id, "status_mkm61j", FLAG_MAP.get(status, "1"))

            reason = note.get("units_reason")
            if reason:
                client.update_column_value(board_id, item_id, "long_text_mkm6wg9t", reason)

if __name__ == "__main__":
    import sys
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    main(offset)
