# Base Goal OKR Scoring & Reporting

Automated system to fetch OKR data from Base.vn, analyze performance, generate Excel reports, and sync structured data to Google Sheets.

## Features
- **Fetch Data**: Retrieves Cycles, OKRs, and Check-in data from Base.vn APIs.
- **Analysis**: Calculates "Next Action Scores" and "OKR Shift" to evaluate progress.
- **Reporting**: Generates a comprehensive `OKR_Analysis_Report.xlsx`.
- **Sync**: Automatically pushes the report structure to Google Sheets with detailed formatting.
- **Automation**: Includes a FastAPI server to trigger updates directly from Google Sheets.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file based on `.env.example` (not included for security):
    ```ini
    GOAL_ACCESS_TOKEN=your_base_goal_token
    ACCOUNT_ACCESS_TOKEN=your_base_account_token
    TABLE_ACCESS_TOKEN=your_base_table_token
    GG_SCRIPT_URL=your_google_apps_script_web_app_url
    ```

## Usage

### Manual Run
Run the main script to generate the report and sync:
```bash
python goal_new.py
```

### API Server (for Google Sheet Trigger)
Start the FastAPI server to listen for triggers:
```bash
python api.py
```
*Note: Use ngrok to expose port 8000 if running locally.*

## Project Structure
- `goal_new.py`: Main logic for fetching, analyzing, and syncing.
- `excel_generator.py`: Handles Excel file creation and payload generation for Google Sheets.
- `api.py`: FastAPI server for triggering the script remotely.
- `ggsheet.py` & `table_client.py`: Helper modules for Google Sheets and Base Table integration.
