# Quick Start Guide

Get the Legal & Compliance Agent running in 5 minutes.

## Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.11+ (for manual setup)

## Option 1: Docker (Recommended)

```bash
# 1. Navigate to directory
cd ~/new-agents/legal-compliance-agent

# 2. Copy environment file
cp .env.example .env

# 3. (Optional) Edit .env and add OpenAI API key
nano .env

# 4. Start all services
docker-compose up -d

# 5. Check status
docker-compose ps

# 6. View logs
docker-compose logs -f api

# 7. Access API
open http://localhost:8000/docs
```

That's it! The API is now running with PostgreSQL and ChromaDB.

## Option 2: Manual Setup

```bash
# 1. Run setup script
./setup.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Edit .env file
nano .env

# 4. Start PostgreSQL (if not using Docker)
# Install and start PostgreSQL on your system

# 5. Start ChromaDB (optional, or use Docker)
docker run -d -p 8001:8001 chromadb/chroma:latest

# 6. Start API server
uvicorn src.main:app --reload

# 7. Access API
open http://localhost:8000/docs
```

## First Request

Try your first API call:

```bash
curl -X POST http://localhost:8000/analyze-contract \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "This Employment Agreement is between Company and Employee. Salary: $100,000 per year. Either party may terminate with 30 days notice.",
    "detect_risks": true
  }'
```

## Run Examples

```bash
# Activate environment (if manual setup)
source venv/bin/activate

# Run all examples
python examples/example_usage.py
```

## Test the API

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Common Commands

```bash
# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart API
docker-compose restart api

# Run tests in Docker
docker-compose exec api pytest

# Access database
docker-compose exec postgres psql -U postgres -d legal_compliance
```

## Next Steps

1. Read the [full README](README.md)
2. Check [API documentation](docs/API.md)
3. Review [examples](examples/example_usage.py)
4. Understand the [legal disclaimer](docs/LEGAL_DISCLAIMER.md)

## Troubleshooting

### Port already in use
```bash
# Change port in .env
PORT=8001

# Or in docker-compose.yml
ports:
  - "8001:8000"
```

### Database connection error
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### OpenAI API errors
```bash
# Check your API key in .env
echo $OPENAI_API_KEY

# Or use without OpenAI (limited features)
# Just leave OPENAI_API_KEY empty
```

## Getting Help

- Documentation: See `docs/` folder
- Examples: See `examples/example_usage.py`
- Issues: GitHub Issues
- API Reference: http://localhost:8000/docs

---

**Ready to go!** 🚀
