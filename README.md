# Memo Test1

Simple memo taking application with Python backend and React frontend.

## Features

- Create memo
- Delete memo
- List memos

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Running

### Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8501
```

### Frontend
```bash
cd frontend
npm run dev -- --port 8500
```

## Docker

```bash
docker-compose up
```

## Configuration

Copy `config/config.local.env` to `.env` and update as needed.

