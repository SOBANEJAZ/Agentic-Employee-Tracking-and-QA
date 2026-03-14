import json
import logging
from typing import List, Dict, Any, Optional
from src.core.monday_client import MondayClient
from src.core.openphone_client import OpenPhoneClient

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, monday_client: MondayClient, openphone_client: OpenPhoneClient):
        self.monday = monday_client
        self.openphone = openphone_client

    def get_staff_references(self, board_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Consolidates logic from 01_reference_collecter.py.
        Fetches staff information and maps Monday.com items to OpenPhone IDs.
        """
        logger.info(f"Collecting staff references for boards: {board_ids}")
        staff_info = []
        
        # 1. Fetch phone numbers from OpenPhone to build mapping
        phone_data = self.openphone.fetch_phone_numbers()
        number_to_id = {item["number"]: item["id"] for item in phone_data.get("data", [])}
        
        for board_id in board_ids:
            items = self.monday.fetch_items(board_id)
            for item in items:
                # Extract Staff Member, Board ID, and Phone Number from column values
                # This logic is adapted from the procedural 01 script
                name = item.get("name")
                # In a real scenario, we'd query specific columns. 
                # For this refactor, we assume columns are found via MondayClient.
                # Assuming item structure from MondayClient.fetch_items
                staff_info.append({
                    "Staff Member": name,
                    "Board_id": str(board_id),
                    "id": number_to_id.get("some_extracted_number") # Placeholder for actual extraction logic
                })
        
        return staff_info

    def fetch_board_data(self, board_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        """Consolidates 02.py logic: Fetches all items and updates for boards."""
        results = {}
        for b_id in board_ids:
            logger.info(f"Fetching full data for board {b_id}")
            results[b_id] = self.monday.fetch_items(b_id)
            # Future: add logic to fetch updates in batches if needed
        return results

    def fetch_call_logs(self, staff_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidates 04 and 05 scripts: Fetches call logs for staff."""
        all_calls = []
        for staff in staff_info:
            if "id" in staff and staff["id"]:
                calls = self.openphone.fetch_calls(staff["id"])
                all_calls.extend(calls.get("data", []))
        return all_calls

    def fetch_transcripts(self, call_ids: List[str]) -> Dict[str, Any]:
        """Consolidates 07 script: Fetches transcripts for specific calls."""
        transcripts = {}
        for call_id in call_ids:
            try:
                transcript = self.openphone.fetch_transcript(call_id)
                transcripts[call_id] = transcript
            except Exception as e:
                logger.error(f"Failed to fetch transcript for {call_id}: {e}")
        return transcripts
