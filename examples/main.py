# examples/main.py (Updated with lifespan)

import asyncio
from contextlib import asynccontextmanager
from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel

from fastapicachex import FastAPICachex # Assuming fastapicachex is installed or in PYTHONPATH

# 1. Initialize the cache manager first
# Give the cache file a descriptive name
cache = FastAPICachex(cache_file_path="sales_report_cache.json")

# 2. Define the lifespan context manager for the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Application startup: Running pre-computation...")
    await cache.run_precomputation()
    
    yield # The application is now running
    
    # Code to run on shutdown (optional)
    print("Application shutdown.")

# 3. Initialize FastAPI and pass the lifespan manager
app = FastAPI(lifespan=lifespan)


# --- Define your types ---
class SubregionEnum(str, Enum):
    EMEA = "EMEA"
    APAC = "APAC"
    AMER = "AMER"

class StoreIDEnum(str, Enum):
    STORE_101 = "101"
    STORE_202 = "202"
    STORE_303 = "303"
    STORE_404 = "404"
    ONLINE = "ONLINE"

class Report(BaseModel):
    subregion: SubregionEnum
    store_id: StoreIDEnum
    data: dict

# 4. Apply the decorator to your slow endpoint (this part is unchanged)
@app.get("/sales-report", response_model=Report)
@cache.precompute
async def get_sales_report(subregion: SubregionEnum, store_id: StoreIDEnum):
    """
    A slow endpoint that simulates complex database queries.
    This original function will only be called during the pre-computation phase.
    """
    print(f"--- Running original slow function for {subregion.value}/{store_id.value} ---")
    await asyncio.sleep(2)  # Simulate a 2-second delay

    if store_id == StoreIDEnum.ONLINE:
        revenue = len(subregion.value) * 5000
    else:
        revenue = int(store_id.value) * 1000

    return {
        "subregion": subregion,
        "store_id": store_id,
        "data": {"revenue": revenue}
    }