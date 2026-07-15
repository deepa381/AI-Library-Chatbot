# AI-Powered Library Management System

A full-stack, AI-powered library management system featuring a smart chatbot, intelligent book recommendations, and comprehensive library operations.

## Architecture

- **Backend:** Django, Django REST Framework, SQLite (for dev)
- **Frontend:** React 19, TypeScript, TailwindCSS v3, Vite
- **AI Integration:** OpenAI API (GPT-4) for chatbot and recommendations
- **State Management:** Zustand, TanStack Query

## Features

- **Authentication:** JWT-based login/registration.
- **Dashboard:** Real-time metrics and charts (Recharts).
- **Book Management:** Browse, search, and view detailed information.
- **Operations:** Borrowing, waitlisting/reservations, and fine tracking.
- **AI Chatbot:** A knowledgeable AI librarian capable of answering queries and checking availability.
- **AI Recommendations:** Context-aware book suggestions based on reading history and preferences.

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.12+
- Docker & Docker Compose (Optional for containerized setup)

### Running Locally (Without Docker)

**1. Backend**
```bash
cd library_backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_kaggle_dataset  # Populate database
python manage.py runserver
```

**2. Frontend**
```bash
cd library_frontend
npm install
npm run dev
```

### Running with Docker

```bash
# Add your OpenAI API key to environment or export it
export OPENAI_API_KEY=your_key_here

docker-compose up --build
```
Backend will be available at `http://localhost:8000` and Frontend at `http://localhost:5173`.

## Deployment

### Frontend (Vercel)
A `vercel.json` is included in the `library_frontend` folder. Simply connect your GitHub repository to Vercel and deploy the `library_frontend` directory.

### Backend (Railway / Render / Heroku)
The `library_backend` includes a standard Django `Dockerfile` and `requirements.txt`. Connect your repository to a PaaS provider, set the `OPENAI_API_KEY` and Django `SECRET_KEY` environment variables, and it will build and deploy automatically.

## API Documentation
Please see [API_GUIDE.md](./API_GUIDE.md) for complete details on the REST endpoints available.
