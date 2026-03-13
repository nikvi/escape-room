## Escape Room Booking API
Desc: Build an API for booking escape room time slots with a "hold" mechanism - teams
can temporarily reserve a slot for 5 minutes while coordinating with friends before
completing the booking.

## Overview:
```
Client
  │
  ▼
FastAPI (app/main.py)
  ├── Redis  ──► temporary holds (5-min TTL)
  └── SQLite ──► confirmed bookings (permanent)
```

## Constraints and decisions
Very simple API 
- only creates/holds/releases the hold
- the concurrency control is handled by Redis's single-threaded nature. By using the NX (Not Exists) flag, the system guarantees that only one user can hold a specific slot at a time, even if multiple API calls arrive simultaneously.
- the db is used as source of truth
- assumption is the slot id provided is already authenticated and valid
- there are no checks into the database 
**Note:** The current implementation does not cross-check the database on `/hold`, so a slot confirmed in SQLite can be re-held in Redis. The DB remains the authoritative source of truth for completed bookings.
- generic http error codes used

### Components:

### FastAPI Application
Exposes three endpoints, all accepting a `slot_id` and `team_name`:

| Endpoint | Method | Description |
|---|---|---|
| `/hold` | POST | Temporarily reserves a slot for 5 minutes |
| `/confirm` | POST | Converts an active hold into a permanent booking |
| `/release` | POST | Explicitly cancels an active hold |

### Infrastructure (Docker Compose)
Two containers are defined in `docker-compose.yml`:

- **redis** — `redis:7-alpine` on port 6379
- **api** — the FastAPI app on port 8000, with the project directory mounted as a volume

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for running tests locally)

### Start the app

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.


### Run tests locally

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Run all tests
pytest tests/
```

### Example requests

```bash
# Hold a slot
curl -X POST http://localhost:8000/hold \
  -H "Content-Type: application/json" \
  -d '{"slot_id": "slot-1", "team_name": "TeamA"}'

# Confirm a booking
curl -X POST http://localhost:8000/confirm \
  -H "Content-Type: application/json" \
  -d '{"slot_id": "slot-1", "team_name": "TeamA"}'

# Release a hold
curl -X POST http://localhost:8000/release \
  -H "Content-Type: application/json" \
  -d '{"slot_id": "slot-1", "team_name": "TeamA"}'
```

## Tools used:
-  used FastAPI and Redis as fastest was to create a API endpoint and proper handling of Race condition/concurrency need
-  the testing code and /gitignore has been generated used Claude code plugin in visual studio.
-  also used to generate the endpoint descriptions here.
