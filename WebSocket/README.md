# Game Ready Backend — Merged Project

## Folder structure

```
merged_backend/
├── main.py            ← single app file (Person 1 + Person 2 merged)
├── requirements.txt   ← all dependencies combined
├── test_all.py        ← combined test file (REST + WebSocket)
├── .env.example       ← copy to .env and fill in DB details
└── README.md          ← this file
```

---

## What each person contributed

### Person 1
- `GET  /health`           — server liveness check
- `GET  /api/status`       — how many teams are ready
- `POST /api/ready`        — marks a team ready, triggers game:start at count == 2
- `POST /api/reset`        — clears state for a new round
- `broadcast()` function   — sends JSON to all WebSocket clients

### Person 2
- `WS   /ws`               — WebSocket endpoint with ping/pong latency support
- `GET  /person2/health`   — Person 2 health check
- `GET  /person2/status`   — shows connected WebSocket client count
- `GET  /person2/ready`    — Person 2 ready confirmation

---

## Step 1 — Setup (run once)

```bash
# Mac/Linux
python3.12 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

Install all dependencies:
```bash
pip install -r requirements.txt
pip install websockets    # needed for WebSocket tests
```

Create your `.env` file:
```bash
# Mac/Linux
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `.env` and set your database URL:
```
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/gamedb
```

---

## Step 2 — Start the server

```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

## Step 3 — Verify it is running

Open in browser: http://localhost:8000/health

Expected response:
```json
{ "status": "ok" }
```

Open Swagger UI to see all endpoints: http://localhost:8000/docs

---

## Step 4 — Run the tests

Open a second terminal (keep server running in the first).

**Run all tests:**
```bash
python test_all.py
```

**Run only REST tests (Person 1):**
```bash
python test_all.py --rest
```

**Run only WebSocket tests (Person 2):**
```bash
python test_all.py --ws
```

**Run only Person 2 endpoint tests:**
```bash
python test_all.py --person2
```

---

## Step 5 — Test the WebSocket manually

Open browser console (F12) and paste:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => console.log('EVENT:', JSON.parse(e.data));
ws.onopen = () => console.log('Connected!');
```

Then in a second tab open Swagger UI and call POST /api/ready twice with different team IDs.
You will see `game:start` appear in the console instantly.

---

## Step 6 — Test latency manually

In the browser console (after connecting above):
```javascript
// Send a ping and measure round-trip
const ts = Date.now();
ws.send(JSON.stringify({ type: 'ping', ts }));
ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  if (msg.type === 'pong') {
    console.log(`Latency: ${((Date.now() - msg.ts) / 2).toFixed(2)}ms`);
  }
};
```

Expected on localhost: under 1ms
Expected on LAN: 1–5ms
Expected over internet: 20–100ms

---

## All endpoints reference

| Method | Endpoint          | Who built it | What it does                          |
|--------|-------------------|--------------|---------------------------------------|
| GET    | /health           | Person 1     | Server liveness check                 |
| GET    | /api/status       | Person 1     | Current ready count                   |
| POST   | /api/ready        | Person 1     | Mark a team ready, trigger game:start |
| POST   | /api/reset        | Person 1     | Clear state for new round             |
| WS     | /ws               | Person 2     | WebSocket with ping/pong              |
| GET    | /person2/health   | Person 2     | Person 2 health check                 |
| GET    | /person2/status   | Person 2     | Connected client count                |
| GET    | /person2/ready    | Person 2     | Person 2 ready confirmation           |

---

## Common errors

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'websockets'` | `pip install websockets` |
| `Connection refused` | Make sure server is running in another terminal |
| `ModuleNotFoundError: No module named 'asyncpg'` | `pip install asyncpg greenlet` |
| `Address already in use` | Use `--port 8001` and update BASE in test_all.py |
