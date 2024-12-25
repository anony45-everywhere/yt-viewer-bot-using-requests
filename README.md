# YouTube Viewer API
[![Netlify Status](https://api.netlify.com/api/v1/badges/18582b2e-91c9-4d69-ab3f-6aebb1438a06/deploy-status)](https://app.netlify.com/sites/yt-viewer-using-req/deploys)

A FastAPI-based web application that provides an API for simulating YouTube views using proxy servers.

## Features

- Simple web interface for submitting YouTube URLs
- Background task processing for view simulation
- Real-time progress tracking
- Proxy support with automatic speed testing
- Secure API endpoints
- Progress visualization with Bootstrap UI

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-viewer-api.git
cd youtube-viewer-api
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application locally:
```bash
uvicorn app:app --reload
```

The application will be available at `http://localhost:8000`

## API Endpoints

- `POST /view`: Create a new view task
  - Request body: `{"url": "youtube_url", "num_views": number}`
  - Returns: `{"task_id": "uuid"}`

- `GET /status/{task_id}`: Get task status
  - Returns: Task details including status and progress

- `GET /tasks`: List all active tasks
  - Returns: Dictionary of all active tasks

## Deployment

The application uses separate GitHub Actions workflows for backend and frontend:

### Backend Deployment
1. The backend API runs on GitHub Actions
2. Automatically deploys when changes are made to:
   - `app.py`
   - `youtube_viewer.py`
   - `requirements.txt`
3. Access the API at the GitHub Actions runner's URL

### Frontend Deployment
1. The frontend is deployed to GitHub Pages
2. Automatically deploys when changes are made to:
   - `templates/`
   - `static/`
3. Access the frontend at `https://yourusername.github.io/youtube-viewer-api`

Note: For production use, consider using a proper hosting service like:
- DigitalOcean
- AWS EC2
- Google Cloud Run
- Azure App Service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 