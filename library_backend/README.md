# Library Chatbot Backend

A modern, Django-based REST API powering the Library Chatbot project. It features an advanced recommendation engine and conversational agent powered dynamically by the Google Gemini SDK.

## Features
- **Dynamic Gemini Model Selection**: Automatically falls back and uses the best available Google Gemini model (e.g. gemini-2.5-flash) via the new `google-genai` SDK without crashing on model deprecation.
- **Smart Book Recommendations**: Ranks books based on a user's borrow history and semantic query.
- **Robust Startup Validation**: Fast-fails with clear error messages if critical environment configurations are missing or broken.
- **Dataset Import Engine**: Comes with built-in scripts to auto-generate and populate the database with sample library data.
- **Health Checks**: A custom management command ensures the environment is fully working.

---

## Installation Guide

### Prerequisites
- Python 3.13
- Virtual Environment (recommended)

### Environment Setup
1. Clone the repository and navigate into the `library_backend` directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy `.env.example` to `.env` and fill in the values:
   ```env
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=sqlite:///db.sqlite3
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   > **Note:** The server will refuse to start if `SECRET_KEY` or `GEMINI_API_KEY` are missing.

---

## Database & Dataset Setup

### Run Migrations
Generate and apply database migrations to prepare the schema.
```bash
python manage.py makemigrations
python manage.py migrate
```

### Import Sample Datasets
The project comes with a dataset importer that will generate sample library data if you don't have your own CSVs.
```bash
python manage.py import_datasets
```

### Create Superuser
To access the Django Admin panel:
```bash
python manage.py createsuperuser
```

---

## Health Check and Verification

Before running the server, verify the project's health.
```bash
python manage.py healthcheck
```
This command checks:
- Environment Variables
- Database Connection
- Pending Migrations
- Gemini API Connectivity & Model Availability
- Dataset Availability

---

## Running the Server

Start the Django development server:
```bash
python manage.py runserver
```

### API Documentation
Once the server is running, you can access the Swagger UI and ReDoc:
- **Swagger:** `http://localhost:8000/swagger/`
- **ReDoc:** `http://localhost:8000/redoc/`

### Admin Panel
Access the fully customized Django Admin panel at:
- **Admin:** `http://localhost:8000/admin/`

---

## Troubleshooting Guide

**Server crashes on startup:**
- Ensure your `.env` file exists and has `SECRET_KEY` and `GEMINI_API_KEY`. The `CoreConfig.ready()` function validates these.

**Gemini API errors:**
- Check your Google AI quota. The application dynamically chooses a model (e.g. `gemini-2.5-flash`); if it fails, verify your API key is active.

**N+1 Query Warnings / Performance:**
- The DRF views have been optimized with `select_related` and `prefetch_related`. If you add new nested serializers, be sure to update the view querysets.

**No books found during chat:**
- Make sure to run `python manage.py import_datasets` so the database is populated.
