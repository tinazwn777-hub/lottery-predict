# Course Summary Image Generator

A web application that automatically extracts content from web pages and PDFs to generate beautiful summary images.

## Features

- **Web URL Parsing**: Extract content from any public web page
- **PDF Upload**: Parse PDF documents and extract text
- **Two Theme Styles**: Light (minimal white) and Dark themes
- **Preview & Download**: Preview generated images and download them
- **Task History**: View and manage previously generated images

## Tech Stack

### Backend
- **FastAPI**: High-performance async API framework
- **Playwright**: Web scraping with dynamic page rendering
- **PyMuPDF**: High-performance PDF parsing
- **Pillow**: Image generation with Chinese font support
- **SQLite**: Lightweight database for task storage

### Frontend
- **Vue 3**: Modern reactive framework
- **Element Plus**: Enterprise-grade UI component library
- **Pinia**: State management
- **Axios**: HTTP client

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Playwright browsers (`playwright install`)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p uploads outputs data

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access the Application

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## API Endpoints

### Tasks
- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks/{task_id}` - Get task details
- `GET /api/v1/tasks/{task_id}/status` - Get task status
- `GET /api/v1/tasks` - List all tasks
- `DELETE /api/v1/tasks/{task_id}` - Delete a task

### Uploads
- `POST /api/v1/uploads/file` - Upload a file

### Files
- `GET /api/v1/files/outputs/{filename}` - Get generated file
- `GET /api/v1/files/uploads/{filename}` - Get uploaded file

## Project Structure

```
course-summary-generator/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Configuration
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   │   ├── parser/    # Web & PDF parsers
│   │   │   └── image/     # Image generator
│   │   ├── workers/       # Celery tasks
│   │   └── main.py        # Application entry
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── views/         # Page components
│   │   ├── stores/        # State management
│   │   └── styles/        # Global styles
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## License

MIT
