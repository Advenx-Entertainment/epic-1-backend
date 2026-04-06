# My work — Environment & REST Endpoints

## My files
- `main.py` — FastAPI app with /api/ready, /api/status, /api/reset, /health
- `requirements.txt` — all dependencies
- `.env.example` — I copy this to .env and fill in my DB details
- `test_person1.py` — I run this to verify my work

## My setup (run once)
```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

## How I start the server
```bash
uvicorn main:app --reload --port 8000
```

## How I test my endpoints
```bash
python test_person1.py
```

Or I open Swagger UI: http://localhost:8000/docs

## My responsibilities
- [x] venv setup + pip install
- [x] POST /api/ready  — increments counter, calls broadcast() at count==2
- [x] GET  /api/status — shows how many teams are ready
- [x] POST /api/reset  — clears state for new round
- [x] GET  /health     — server liveness check
- [x] broadcast() stub — interface I agreed on with my teammate

## My handoff to my teammate
I give them:
1. My `main.py` — they will fill in the WebSocket endpoint and broadcast()
2. The agreed broadcast() interface: `async def broadcast(payload: dict)`

## API reference

### POST /api/ready?team_id=<name>
Marks a team ready. When 2 teams are ready, broadcasts game:start.
```json
// Response when waiting
{ "status": "waiting", "ready_count": 1, "waiting_for": 1 }

// Response when both ready
{ "status": "game_started", "ready_count": 2, "teams": ["team_a", "team_b"] }
```

### GET /api/status
```json
{ "ready_count": 1, "ready_teams": ["team_a"], "waiting_for": 1 }
```

### POST /api/reset
```json
{ "status": "reset", "message": "Ready state cleared" }
```
