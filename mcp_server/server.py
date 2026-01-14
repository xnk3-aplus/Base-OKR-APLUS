import os
import requests
import json
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Base Table API")

BASE_URL = "https://table.base.vn/extapi/v1"
# Update to use the correct token variable from .env
ACCESS_TOKEN = os.getenv("TABLE_ACCESS_TOKEN")

@mcp.tool(
    name="create_record",
    description="Create a new record in a Base Table with specified field values.",
    tags=["table", "record", "create"]
)
def create_record(name: str, username: str = "SonTran", table_id: str = "81", values: dict[str, str] = {}) -> str:
    """
    Create a new record in the Base Table.
    
    Args:
        name: The value for the first column (_name) - checkin_name.
        username: The username of the person creating the record (Default: SonTran).
        table_id: The ID of the table (Default: 81).
        values: A dictionary of other field values.
            Mapping:
            - f1: cycle_id
            - f2: next_action_score
            - f4: cong_viec_tiep_theo
            - f5: checkin_id
            - f7: checkin_since
            - f8: checkin_target_name
            - f9: checkin_kr_current_value
            - f10: checkin_user_id
            - f11: kr_name
    """
    url = f"{BASE_URL}/record/create"
    payload = {
        "access_token_v2": ACCESS_TOKEN,
        "table_id": table_id,
        "username": username,
        "_name": name,
    }
    if values:
        payload.update(values)
    
    try:
        response = requests.post(url, data=payload)
        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(
    name="update_record",
    description="Update the next_action_score (f2) for an existing record in Base Table.",
    tags=["table", "record", "update"]
)
def update_record(record_id: str, score: int, username: str = "SonTran") -> str:
    """
    Update the next_action_score for an existing record.
    
    Args:
        record_id: The ID of the record to update (Required).
        score: The score to update (maps to field f2).
        username: The username of the person updating the record (Default: SonTran).
    """
    url = f"{BASE_URL}/record/edit"
    payload = {
        "access_token_v2": ACCESS_TOKEN,
        "id": record_id,
        "username": username,
        "f2": str(score)
    }

    try:
        response = requests.post(url, data=payload)
        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(
    name="get_records",
    description="Retrieve records from a Base Table with optional filtering. Returns a list of flattened records.",
    tags=["table", "record", "get", "read"],
    annotations={"readOnlyHint": True}
)
def get_records(
    table_id: str = "81", 
    page_id: int = 1, 
    limit: int = 50,
    view_id: str | None = None
) -> str:
    """
    Get records from the Base Table.
    
    Args:
        table_id: The ID of the table (Default: 81).
        page: Page number (starts at 1).
        limit: Records per page (default 50).
        view_id: Optional view ID to filter by.
    """
    url = f"{BASE_URL}/table/records"
    payload = {
        "access_token_v2": ACCESS_TOKEN,
        "table_id": table_id,
        "page": page_id, # API uses 'page', not 'page_id' based on main.py/get_records.py usage
        "limit": limit
    }
    if view_id: payload["view_id"] = view_id

    try:
        response = requests.post(url, data=payload)
        data = response.json()
        
        records = data.get('data', [])
        flattened_records = []
        
        if records:
            for r in records:
                # Extract vals and include the record ID
                row = r.get('vals', {})
                row['id'] = str(r.get('id', ''))
                flattened_records.append(row)
                
        return json.dumps(flattened_records, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)