# Base Table API MCP Server

An MCP server to interact with Base.vn Table API, specifically tailored for managing OKR check-in records and AI-scored next actions.

## Features

- **Create Record**: Add new check-in records to Base Table.
- **Update Score**: Update the "Next Action Score" for existing records.
- **Get Records**: Retrieve and filter check-in records.

## Setup

1.  **Environment Variables**:
    Ensure you have a `.env` file with the following:
    ```bash
    TABLE_ACCESS_TOKEN=your_base_table_access_token
    GOAL_ACCESS_TOKEN=your_base_goal_access_token
    ```

2.  **Dependencies**:
    Install required packages:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Key dependencies include `fastmcp`, `requests`, `python-dotenv`)*

## MCP Tools

### `create_record`
Creates a new record in Base Table.

*   **Args**:
    *   `name` (str): Content for the first column (`_name`). **Required**.
    *   `username` (str): User creating the record. Default: `"SonTran"`.
    *   `table_id` (str): Target table ID. Default: `"81"`.
    *   `values` (dict): Dictionary of other field values (e.g., `{"f1": "val"}`).

### `update_record`
Updates the "Next Action Score" (`f2`) for an existing record.

*   **Args**:
    *   `record_id` (str): The unique ID of the record to update. **Required**.
    *   `score` (int): The new score (1, 3, or 5). **Required**.
    *   `username` (str): User updating the record. Default: `"SonTran"`.

### `get_records`
Retrieves records from Base Table as a flattened list.

*   **Args**:
    *   `table_id` (str): Target table ID. Default: `"81"`.
    *   `page_id` (int): Page number to fetch (starts at 1). Default: `1`.
    *   `limit` (int): Records per page. Default: `50`.
    *   `view_id` (str, optional): Filter by a specific View ID.

## Running the Server

Run the server using the FastMCP CLI or directly via Python:

```bash
# Development mode
fastmcp dev server.py

# Or directly
python server.py
```
