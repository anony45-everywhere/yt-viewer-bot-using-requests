# YouTube Viewer API

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

4. Run the application:
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

The application includes GitHub Actions workflow for automatic deployment to GitHub Pages:

1. Fork or clone this repository
2. Enable GitHub Pages in your repository settings:
   - Go to Settings > Pages
   - Select the `gh-pages` branch as the source
   - Save the settings
3. Push to the main branch to trigger deployment
4. Your site will be available at `https://yourusername.github.io/youtube-viewer-api`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 