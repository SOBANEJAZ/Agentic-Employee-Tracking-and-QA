import json
import os
from datetime import datetime, timedelta
import pytz
from src.core.utils import safe_load_json, safe_save_json

def get_datetime_format(datetime_str):
    if "T" in datetime_str and datetime_str.endswith("Z"):
        return "%Y-%m-%dT%H:%M:%S.%fZ" if "." in datetime_str else "%Y-%m-%dT%H:%M:%S.Z"
    elif "+0000" in datetime_str:
        return "%a, %d %b %Y %H:%M:%S %z"
    return None

def main(days_offset: int = 16):
    cst = pytz.timezone("America/Chicago")
    target_date = (datetime.now(cst) - timedelta(days=days_offset)).strftime("%Y-%m-%d")
    print(f"Combining call logs for date: {target_date}")

    main_json_path = "data/reference/phone_details.json"
    call_logs_dir = "data/call_logs"
    
    phone_details = safe_load_json(main_json_path)

    # Combine IDs
    for index, entry in enumerate(phone_details):
        log_path = os.path.join(call_logs_dir, f"{index}.json")
        if os.path.exists(log_path):
            log_data = safe_load_json(log_path)
            start_time = entry.get("Start Time")
            for item in log_data.get("data", []):
                if start_time == item.get("createdAt"):
                    entry["callid"] = item.get("id")
                    break

    # Filter by date and length
    filtered = []
    for item in phone_details:
        if len(item) < 10:
            continue
            
        start_time_str = item.get("Start Time")
        if start_time_str:
            try:
                # Basic parsing to get date
                from dateutil.parser import parse
                dt = parse(start_time_str).astimezone(cst)
                if dt.strftime("%Y-%m-%d") == target_date:
                    item["Start Time"] = dt.isoformat() # Standardize format
                    filtered.append(item)
            except Exception:
                continue

    safe_save_json(filtered, main_json_path)
    print(f"Saved {len(filtered)} matched calls to {main_json_path}")

if __name__ == "__main__":
    import sys
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    main(offset)
