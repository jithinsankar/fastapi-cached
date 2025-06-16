# FastAPICache

A simple Python package to pre-compute and cache FastAPI endpoints that have parameters with discrete values (like Enums or Literals). This is ideal for slow, data-intensive endpoints where the inputs are predictable and the data does not change frequently.

## Features

- **Automatic Pre-computation:** Runs on server startup to compute all possible outcomes.
- **Persistent Caching:** Saves results to a JSON file, so you don't re-compute on every server restart.
- **Resume Support:** If the startup computation is interrupted, it resumes where it left off.
- **Easy to Use:** Requires only a simple decorator and a startup event hook.
- **Automatic Parameter Detection:** Infers discrete values from type hints like `Enum` and `typing.Literal`.
- **Editable Cache:** The JSON cache file is human-readable and can be edited manually if needed.

## Installation

(Assuming you place the `fastapicache` folder in your project root)

You can install it locally for your project. If you are using Poetry:

```bash
poetry add ./fastapicache
```

Or with pip:
```bash
pip install ./fastapicache
```

## How to Use
Here is a complete example of how to integrate fastapicache into your FastAPI application.

```python
# main.py
from enum import Enum
from fastapi import FastAPI
import asyncio
from fastapicache import FastAPICache

# 1. Initialize FastAPI and FastAPICache
app = FastAPI()
cache = FastAPICache(cache_file_path="sales_report_cache.json")

# --- Define your types ---
class SubregionEnum(str, Enum):
    EMEA = "EMEA"
    APAC = "APAC"
    AMER = "AMER"

class StoreIDEnum(str, Enum):
    STORE_101 = "101"
    STORE_202 = "202"
    ONLINE = "ONLINE"

# 2. Apply the decorator to your slow endpoint
@app.get("/sales-report")
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

# 3. Register the pre-computation to run on startup
@app.on_event("startup")
async def on_startup():
    await cache.run_precomputation()
```

How It Works
Initialization: cache = FastAPICache(...) creates a cache manager instance.
Decoration: The @cache.precompute decorator wraps your route function. It registers the function for pre-computation and replaces it with a new function that will read from the cache during live requests.
Startup: When the FastAPI server starts, the on_startup event fires cache.run_precomputation().
The cache loads any existing data from sales_report_cache.json.
It inspects get_sales_report and finds the SubregionEnum and StoreIDEnum parameters.
It generates all possible combinations (e.g., EMEA/101, EMEA/202, APAC/101...).
For each combination that is not already in the cache, it calls the original get_sales_report function, waits for the result, and saves it to both the in-memory cache and the JSON file.
Live Requests: When a request like GET /sales-report?subregion=APAC&store_id=ONLINE comes in, the decorator instantly looks up the key in its cache and returns the pre-computed JSON response without running the slow 2-second logic.


Running the Server
From your terminal in the fastapicache-project directory:


