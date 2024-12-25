from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import uuid
from typing import Dict, Optional
from youtube_viewer import YouTubeViewer
import asyncio
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Store active tasks
tasks: Dict[str, dict] = {}

class ViewRequest(BaseModel):
    url: str
    num_views: int

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def process_views(task_id: str, url: str, num_views: int):
    """Process views in the background."""
    try:
        video_id = extract_video_id(url)
        if not video_id:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = "Invalid YouTube URL"
            return

        viewer = YouTubeViewer()
        tasks[task_id]["status"] = "running"
        
        for i in range(num_views):
            try:
                await asyncio.to_thread(viewer.watch_video, video_id)
                tasks[task_id]["completed_views"] += 1
                tasks[task_id]["current_view"] = i + 1
                logger.info(f"Task {task_id}: Completed view {i + 1}/{num_views}")
            except Exception as e:
                logger.error(f"Task {task_id}: Error processing view {i + 1}: {str(e)}")
                tasks[task_id]["errors"].append(str(e))
        
        tasks[task_id]["status"] = "completed"
        logger.info(f"Task {task_id}: All views completed")
    
    except Exception as e:
        logger.error(f"Task {task_id}: Fatal error: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

@app.post("/view")
async def create_view_task(request: ViewRequest, background_tasks: BackgroundTasks):
    """Create a new view task."""
    if request.num_views < 1 or request.num_views > 10:
        raise HTTPException(status_code=400, detail="Number of views must be between 1 and 10")
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "url": request.url,
        "num_views": request.num_views,
        "status": "pending",
        "completed_views": 0,
        "current_view": 0,
        "errors": []
    }
    
    background_tasks.add_task(process_views, task_id, request.url, request.num_views)
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/tasks")
async def get_all_tasks():
    """Get all active tasks."""
    return tasks

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 