from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="Base Goal OKR Scoring API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def run_goal_sync():
    """Executes the goal_new.py script logic directly"""
    try:
        print("Starting goal_new.py sync (Imported)...")
        import goal_new # Import the module LAZILY to avoid cold start crash
        goal_new.main() # Call the main function
        print("Sync completed.")
            
    except Exception as e:
        print(f"Error running script: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Base Goal OKR Scoring API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /sync": "Trigger Goal/OKR Sync"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    """
    Endpoint triggered by Google Sheets to start the sync process.
    Runs in background to avoid timeout in Apps Script.
    """
    background_tasks.add_task(run_goal_sync)
    return {"status": "started", "message": "Sync process started in background."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)