"""
Merged test file — covers both Person 1 (REST) and Person 2 (WebSocket) work.

Usage:
    # Terminal 1 — start server
    uvicorn main:app --reload --port 8000

    # Terminal 2 — run all tests
    python test_all.py

    # Or run only one section
    python test_all.py --rest
    python test_all.py --ws
    python test_all.py --person2
"""
import httpx
import asyncio
import json
import time
import sys

try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

BASE   = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# ─────────────────────────────────────────────────────────────
# Person 1 — REST tests
# ─────────────────────────────────────────────────────────────

async def test_rest():
    print("\n╔══════════════════════════════════════════════════╗")
    print("║         Person 1 — REST endpoint tests          ║")
    print("╚══════════════════════════════════════════════════╝")

    async with httpx.AsyncClient() as client:

        # Reset first so tests start clean
        await client.post(f"{BASE}/api/reset")

        print("\n── Test 1: Health check ─────────────────────────")
        r = await client.get(f"{BASE}/health")
        print(f"GET /health → {r.status_code} {r.json()}")
        assert r.json()["status"] == "ok", "FAIL: health check"
        print("PASS ✓")

        print("\n── Test 2: Status (no teams ready) ──────────────")
        r = await client.get(f"{BASE}/api/status")
        print(f"GET /api/status → {r.json()}")
        assert r.json()["ready_count"] == 0, "FAIL: should be 0"
        print("PASS ✓")

        print("\n── Test 3: Team A readies up ────────────────────")
        r = await client.post(f"{BASE}/api/ready?team_id=team_a")
        print(f"POST /api/ready?team_id=team_a → {r.json()}")
        assert r.json()["status"] == "waiting", "FAIL: should be waiting"
        assert r.json()["ready_count"] == 1, "FAIL: count should be 1"
        print("PASS ✓")

        print("\n── Test 4: Same team readies again (no double count)")
        r = await client.post(f"{BASE}/api/ready?team_id=team_a")
        print(f"POST /api/ready?team_id=team_a again → {r.json()}")
        assert r.json()["ready_count"] == 1, "FAIL: set should prevent double count"
        print("PASS ✓")

        print("\n── Test 5: Team B readies up → game starts ──────")
        r = await client.post(f"{BASE}/api/ready?team_id=team_b")
        print(f"POST /api/ready?team_id=team_b → {r.json()}")
        assert r.json()["status"] == "game_started", "FAIL: should be game_started"
        assert r.json()["ready_count"] == 2, "FAIL: count should be 2"
        print("PASS ✓")

        print("\n── Test 6: Reset ─────────────────────────────────")
        r = await client.post(f"{BASE}/api/reset")
        print(f"POST /api/reset → {r.json()}")
        assert r.json()["status"] == "reset", "FAIL: reset failed"
        r2 = await client.get(f"{BASE}/api/status")
        assert r2.json()["ready_count"] == 0, "FAIL: count should be 0 after reset"
        print("PASS ✓")

    print("\n── All Person 1 REST tests passed! ──────────────\n")


# ─────────────────────────────────────────────────────────────
# Person 2 — extra endpoint tests
# ─────────────────────────────────────────────────────────────

async def test_person2_endpoints():
    print("\n╔══════════════════════════════════════════════════╗")
    print("║       Person 2 — extra endpoint tests           ║")
    print("╚══════════════════════════════════════════════════╝")

    async with httpx.AsyncClient() as client:

        print("\n── Test 1: Person 2 health ───────────────────────")
        r = await client.get(f"{BASE}/person2/health")
        print(f"GET /person2/health → {r.json()}")
        assert r.json()["health"] == "ok", "FAIL"
        print("PASS ✓")

        print("\n── Test 2: Person 2 status ───────────────────────")
        r = await client.get(f"{BASE}/person2/status")
        print(f"GET /person2/status → {r.json()}")
        assert r.json()["status"] == "running", "FAIL"
        print("PASS ✓")

        print("\n── Test 3: Person 2 ready ────────────────────────")
        r = await client.get(f"{BASE}/person2/ready")
        print(f"GET /person2/ready → {r.json()}")
        assert r.json()["status"] == "person2 ready", "FAIL"
        print("PASS ✓")

    print("\n── All Person 2 endpoint tests passed! ──────────\n")


# ─────────────────────────────────────────────────────────────
# Person 2 — WebSocket tests
# ─────────────────────────────────────────────────────────────

async def test_websocket():
    if not WS_AVAILABLE:
        print("\n⚠  websockets package not installed.")
        print("   Run: pip install websockets")
        print("   Then re-run this script.\n")
        return

    print("\n╔══════════════════════════════════════════════════╗")
    print("║        Person 2 — WebSocket tests               ║")
    print("╚══════════════════════════════════════════════════╝")

    async with websockets.connect(WS_URL) as ws:

        print("\n── Test 1: WebSocket connects ────────────────────")
        print(f"Connected to {WS_URL}")
        print("PASS ✓")

        print("\n── Test 2: Ping/pong latency ─────────────────────")
        latencies = []
        for i in range(5):
            ts = time.time() * 1000
            await ws.send(json.dumps({"type": "ping", "ts": ts}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "pong", "FAIL: expected pong"
            assert resp["ts"] == ts, "FAIL: ts mismatch"
            latency = (time.time() * 1000 - resp["ts"]) / 2
            latencies.append(latency)

        avg = sum(latencies) / len(latencies)
        print(f"Latency over 5 samples:")
        print(f"  avg: {avg:.2f}ms")
        print(f"  min: {min(latencies):.2f}ms")
        print(f"  max: {max(latencies):.2f}ms")
        print("PASS ✓")

        print("\n── Test 3: game:start broadcast ──────────────────")
        async with httpx.AsyncClient() as client:
            await client.post(f"{BASE}/api/reset")
            await client.post(f"{BASE}/api/ready?team_id=team_a")
            await client.post(f"{BASE}/api/ready?team_id=team_b")

        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
        print(f"Received WS event → {msg}")
        # The reset also sends a broadcast so we may need to skip it
        if msg["type"] == "game:reset":
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            print(f"Received next WS event → {msg}")
        assert msg["type"] == "game:start", f"FAIL: expected game:start, got {msg['type']}"
        assert "teams" in msg, "FAIL: no teams in payload"
        print("PASS ✓")

    print("\n── All WebSocket tests passed! ───────────────────\n")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

async def main():
    args = sys.argv[1:]

    try:
        if not args or "--rest" in args:
            await test_rest()
        if not args or "--person2" in args:
            await test_person2_endpoints()
        if not args or "--ws" in args:
            await test_websocket()

        print("╔══════════════════════════════════════════════════╗")
        print("║           All tests passed!                      ║")
        print("╚══════════════════════════════════════════════════╝\n")

    except AssertionError as e:
        print(f"\n✗ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("  Is the server running? → uvicorn main:app --reload --port 8000")
        sys.exit(1)


asyncio.run(main())
