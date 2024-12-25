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
git clone https://github.com/Likhithsai2580/yt-viewer-using-req.git
cd yt-viewer-using-req
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

This application is deployed using Netlify:

1. The frontend is served statically from the `dist` directory
2. The backend API runs as a Netlify Function
3. Automatic deployments occur when changes are pushed to the main branch

To deploy your own instance:

1. Fork this repository
2. Sign up for Netlify
3. Connect your forked repository to Netlify
4. Set the following environment variables in Netlify:
   - `NETLIFY_AUTH_TOKEN`
   - `NETLIFY_SITE_ID`
5. Deploy! Netlify will automatically build and deploy both frontend and backend

The application will be available at `https://your-site-name.netlify.app`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 