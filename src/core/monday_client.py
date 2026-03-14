import os
import time
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple
from requests.exceptions import RequestException

load_dotenv()

class MondayClient:
    """
    A robust client for interacting with the Monday.com GraphQL API.
    Supports item fetching, column updates, and retry logic for complexity limits.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MONDAY_API_KEY")
        if not self.api_key:
            raise ValueError("MONDAY_API_KEY not found in environment")
        self.url = "https://api.monday.com/v2"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
            "API-Version": "2024-04"  # Use a recent API version
        }

    def post_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Executes a raw GraphQL POST request.
        
        Args:
            query: The GraphQL query string.
            variables: Optional variables for the query.
        
        Returns:
            The JSON response dictionary.
        """
        response = requests.post(
            self.url, 
            json={"query": query, "variables": variables}, 
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def make_request_with_retry(
        self,
        query: str,
        variables: Optional[Dict] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Tuple[Dict, bool]:
        """Make a request with retry logic and exponential backoff."""
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                response_data = self.post_query(query, variables)
                if "errors" in response_data:
                    error_messages = [e.get("message", "").lower() for e in response_data.get("errors", [])]
                    if any("complexity" in msg or "limit" in msg for msg in error_messages):
                        print(f"Complexity limit reached. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                    return response_data, False
                return response_data, True
            except (RequestException, ValueError) as e:
                print(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
        return {"data": {}, "errors": ["Max retries exceeded"]}, False

    def fetch_items(self, board_id: int, limit: int = 400) -> List[Dict]:
        """Fetch all items from a board."""
        query = """
        query ($boardId: [ID!], $limit: Int) {
            boards(ids: $boardId) {
                groups {
                    title
                    id
                    items_page(limit: $limit) {
                        cursor
                        items {
                            id
                            name
                        }
                    }
                }
            }
        }
        """
        variables = {"boardId": [str(board_id)], "limit": limit}
        data, success = self.make_request_with_retry(query, variables)
        if success:
            items = []
            for board in data.get("data", {}).get("boards", []):
                for group in board.get("groups", []):
                    items.extend(group.get("items_page", {}).get("items", []))
            return items
        return []

    def update_column_value(self, board_id: int, item_id: int, column_id: str, value: str) -> bool:
        """Update a simple column value."""
        mutation = """
        mutation ($boardId: ID!, $itemId: ID!, $columnId: String!, $value: String!) {
            change_simple_column_value (
                board_id: $boardId, 
                item_id: $itemId, 
                column_id: $columnId, 
                value: $value
            ) {
                id
            }
        }
        """
        variables = {
            "boardId": str(board_id),
            "itemId": str(item_id),
            "columnId": column_id,
            "value": value
        }
        data, success = self.make_request_with_retry(mutation, variables)
        return success

    def create_item(self, board_id: int, group_id: str, item_name: str) -> Optional[int]:
        """Create a new item on a board."""
        mutation = """
        mutation ($boardId: ID!, $groupId: String!, $itemName: String!) {
            create_item(
                board_id: $boardId,
                group_id: $groupId,
                item_name: $itemName
            ) {
                id
            }
        }
        """
        variables = {
            "boardId": str(board_id),
            "groupId": group_id,
            "itemName": item_name
        }
        data, success = self.make_request_with_retry(mutation, variables)
        if success:
            return data.get("data", {}).get("create_item", {}).get("id")
        return None
