import time
import asyncio
from fastapi import FastAPI, Depends

app = FastAPI(title="Project 1A - Sync vs Async Playground")

# ---------------------------
# Dependency (DI example)
# ---------------------------

class TimerService:
    """
    Simple service to simulate work.
    This is OOPS + DI in the smallest possible form.
    """

    def blocking_sleep(self, seconds: int):
        time.sleep(seconds)

    async def non_blocking_sleep(self, seconds: int):
        await asyncio.sleep(seconds)


def get_timer_service():
    """
    Dependency Injection:
    FastAPI creates and injects this for us.
    """
    return TimerService()

# ---------------------------
# 1️⃣ Sync + Blocking (BAD but common)
# ---------------------------

@app.get("/sync-blocking")
def sync_blocking(timer: TimerService = Depends(get_timer_service)):
    start = time.time()
    timer.blocking_sleep(5)
    end = time.time()
    return {
        "type": "sync-blocking",
        "time_taken": end - start
    }

# ---------------------------
# 2️⃣ Sync + CPU-bound (Still blocking)
# ---------------------------

@app.get("/sync-cpu")
def sync_cpu():
    start = time.time()
    total = 0
    for i in range(10_000_000):
        total += i
    end = time.time()
    return {
        "type": "sync-cpu",
        "time_taken": end - start
    }

# ---------------------------
# 3️⃣ Async + Blocking (WORST CASE)
# ---------------------------

@app.get("/async-blocking")
async def async_blocking(timer: TimerService = Depends(get_timer_service)):
    start = time.time()
    timer.blocking_sleep(5)   # ❌ BLOCKS EVENT LOOP
    end = time.time()
    return {
        "type": "async-blocking",
        "time_taken": end - start
    }

# ---------------------------
# 4️⃣ Async + Non-blocking (CORRECT)
# ---------------------------

@app.get("/async-non-blocking")
async def async_non_blocking(timer: TimerService = Depends(get_timer_service)):
    start = time.time()
    await timer.non_blocking_sleep(5)  # ✅ YIELDS CONTROL
    end = time.time()
    return {
        "type": "async-non-blocking",
        "time_taken": end - start
    }
