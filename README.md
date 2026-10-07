# Caching Service

A robust FastAPI microservice that processes lists of strings, applies a simulated external transformation, interleaves the results, and caches the outcomes for optimal performance.

## 🚀 Features

- **FastAPI Backend:** High-performance asynchronous API framework.
- **Smart Caching:** Minimizes external service calls by caching individual string transformations and entire payload results using SHA-256 hashing.
- **Concurrency Handling:** Gracefully handles race conditions during parallel processing using database transaction rollbacks.
- **CLI Tool:** A dedicated Python command-line interface for programmatic interaction with the API, built with `argparse` and validated via `Pydantic Settings`.
- **Database Agnostic:** Configured to use PostgreSQL in Docker and SQLite for local development and testing.
- **Dockerized:** Fully containerized with `docker-compose` including database health checks.
- **CI/CD Ready:** Configured GitHub Actions pipeline for linting, formatting (Ruff), and testing (Pytest).

## 📋 Prerequisites

- **Docker** and **Docker Compose** (for containerized deployment)
- **Python 3.13+** (for local development)

## 🛠️ Installation & Setup

### Option 1: Run with Docker (Recommended)

1. Clone the repository:

   ```bash
   git clone <your-repository-url>
   cd caching-service
   ```

2. Start the application and the PostgreSQL database:
   ```bash
   docker compose up -d --build
   ```

The API will be available at `http://localhost:8000`.

### Option 2: Local Development Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the application (uses SQLite by default):
   ```bash
   uvicorn app.main:app --reload
   ```

## 📖 API Reference

Detailed interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs` when the server is running.

### 1. Create a Payload

**Endpoint:** `POST /payload`

**Request Body:**

```json
{
  "list_1": ["first string", "second string", "third string"],
  "list_2": ["other string", "another string", "last string"]
}
```

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Payload successfully generated."
}
```

### 2. Read a Payload

**Endpoint:** `GET /payload/{id}`

**Response (200 OK):**

```json
{
  "output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
}
```

## 💻 CLI Tool Usage

The project includes a CLI tool to interact with the service programmatically.

**General Syntax:**

```bash
python -m cli.cli [-h|--host URL] [-r|--repeat N] [-i|--input FILE|-] [-j|--json JSON] [-o|--output FILE|-]
```

**Examples:**

1. **Using inline JSON:**

   ```bash
   python -m cli.cli --host http://localhost:8000 -j '{"list_1": ["apple", "banana"], "list_2": ["cherry", "orange"]}'
   ```

2. **Reading from a file and outputting to a file:**

   ```bash
   python -m cli.cli --input payload.json --output result.txt
   ```

3. **Repeating the request to test caching:**
   ```bash
   python -m cli.cli -j '{"list_1": ["a"], "list_2": ["b"]}' --repeat 5
   ```

## 🧪 Testing

The project uses `pytest` for unit and integration testing.

To run the test suite locally:

```bash
pytest
```

To run tests with coverage reporting:

```bash
pytest --cov=app --cov-report=term-missing
```

## 📂 Project Structure

```text
.
├── .github/workflows/   # CI/CD pipelines
├── app/                 # Main FastAPI application directory
│   ├── main.py          # Application entry point
│   ├── config.py        # Environment variables & settings
│   ├── database.py      # SQLAlchemy setup & session management
│   ├── models.py        # Database ORM models
│   ├── schemas.py       # Pydantic models for request/response validation
│   └── services.py      # Business logic & caching mechanisms
├── cli/                 # Command-line interface tool
│   └── cli.py
├── tests/               # Pytest test suite
│   └── tests.py
├── docker-compose.yml   # Multi-container Docker configuration
├── Dockerfile           # Backend container instructions
├── requirements.txt     # Python dependencies
└── pytest.ini           # Pytest configuration
```
