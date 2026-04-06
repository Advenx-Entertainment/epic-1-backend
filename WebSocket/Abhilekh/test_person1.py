"""
Person 1 — manual test script
Run this to verify all your endpoints work before handing off to Person 2.

Usage:
    # Terminal 1 — start server
    uvicorn main:app --reload --port 8000

    # Terminal 2 — run tests
    python test_person1.py
"""
import httpx
import asyncio


BASE = "http://localhost:8000"


async def run():
    async with httpx.AsyncClient() as client:

        print("\n── Test 1: Health check ─────────────────────────")
        r = await client.get(f"{BASE}/health")
        print(f"GET /health → {r.status_code} {r.json()}")
        assert r.json()["status"] == "ok", "FAIL: health check"
        print("PASS")

        print("\n── Test 2: Status (no teams ready) ──────────────")
        r = await client.get(f"{BASE}/api/status")
        print(f"GET /api/status → {r.json()}")
        assert r.json()["ready_count"] == 0, "FAIL: should be 0"
        print("PASS")

        print("\n── Test 3: Team A readies up ────────────────────")
        r = await client.post(f"{BASE}/api/ready?team_id=team_a")
        print(f"POST /api/ready?team_id=team_a → {r.json()}")
        assert r.json()["status"] == "waiting", "FAIL: should be waiting"
        assert r.json()["ready_count"] == 1, "FAIL: count should be 1"
        print("PASS")

        print("\n── Test 4: Same team readies again (no double count)")
        r = await client.post(f"{BASE}/api/ready?team_id=team_a")
        print(f"POST /api/ready?team_id=team_a again → {r.json()}")
        assert r.json()["ready_count"] == 1, "FAIL: set should prevent double count"
        print("PASS")

        print("\n── Test 5: Team B readies up → game starts ──────")
        r = await client.post(f"{BASE}/api/ready?team_id=team_b")
        print(f"POST /api/ready?team_id=team_b → {r.json()}")
        assert r.json()["status"] == "game_started", "FAIL: should be game_started"
        assert r.json()["ready_count"] == 2, "FAIL: count should be 2"
        print("PASS")

        print("\n── Test 6: Reset ─────────────────────────────────")
        r = await client.post(f"{BASE}/api/reset")
        print(f"POST /api/reset → {r.json()}")
        assert r.json()["status"] == "reset", "FAIL: reset failed"
        r2 = await client.get(f"{BASE}/api/status")
        assert r2.json()["ready_count"] == 0, "FAIL: count should be 0 after reset"
        print("PASS")

        print("\n─────────────────────────────────────────────────")
        print("All Person 1 tests passed!")
        print("Hand off main.py + requirements.txt to Person 2.")


asyncio.run(run())
