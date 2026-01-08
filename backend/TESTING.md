# Testing Guide

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

3. Update `.env` with your credentials:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `LLM_MODEL`: Model to use (default: gpt-4)

## Running the Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the candidate's skills?",
    "profile_id": 1
  }'
```

### Example Queries

**English:**
```json
{
  "query": "What technologies does the candidate know?",
  "profile_id": 1
}
```

**Turkish:**
```json
{
  "query": "Adayın hangi teknolojileri biliyor?",
  "profile_id": 1
}
```

## Database Setup

Make sure your PostgreSQL database has the required tables:
- profiles
- skills
- experiences
- projects

You can use SQLAlchemy to create tables:
```python
from backend.data_access.knowledge_base.postgres import Base
from backend.infrastructure.database import engine

Base.metadata.create_all(bind=engine)
```

## Testing with Sample Data

Insert a test profile:
```sql
INSERT INTO profiles (id, name, email, summary) 
VALUES (1, 'John Doe', 'john@example.com', 'Experienced Python developer');
```







