# fastapi-cacher

A simple Python package to pre-compute and cache FastAPI endpoints that have parameters with discrete values (like Enums or Literals). This is ideal for slow, data-intensive endpoints where the inputs are predictable and the data does not change frequently.

## Features

- **Automatic Pre-computation:** Runs on server startup to compute all possible outcomes.
- **Persistent Caching:** Saves results to a JSON file, so you don't re-compute on every server restart.
- **Resume Support:** If the startup computation is interrupted, it resumes where it left off.
- **Easy to Use:** Requires only a simple decorator and a startup event hook.
- **Automatic Parameter Detection:** Infers discrete values from type hints like `Enum` and `typing.Literal`.
- **Editable Cache:** The JSON cache file is human-readable and can be edited manually if needed.

## Installation

(Assuming you place the `fastapi-cacher` folder in your project root)

You can install it locally for your project. If you are using Poetry:

```bash
poetry add fastapi-cacher
```

Or with pip:

```bash
pip install fastapi-cacher
```

## How to Use

Here is a complete example of how to integrate `fastapi-cacher` into your FastAPI application using the modern `lifespan` event handler.

```python
# main.py
import asyncio
from contextlib import asynccontextmanager
from enum import Enum
from fastapi import FastAPI
from fastapi-cacher import fastapi-cacher

# 1. Initialize fastapi-cacher
cache = fastapi-cacher(cache_file_path="sales_report_cache.json")

# 2. Define the lifespan manager to run pre-computation on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    await cache.run_precomputation()
    yield
    # This code runs on shutdown (optional)
    print("Application has shut down.")

# 3. Initialize FastAPI with the lifespan handler
app = FastAPI(lifespan=lifespan)

# --- Define your types ---
class SubregionEnum(str, Enum):
    EMEA = "EMEA"
    APAC = "APAC"
    AMER = "AMER"

class StoreIDEnum(str, Enum):
    STORE_101 = "101"
    STORE_202 = "202"
    ONLINE = "ONLINE"

# 4. Apply the decorator to your slow endpoint
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
```

### How It Works

1.  **Initialization:** `cache = fastapi-cacher(...)` creates a cache manager instance.
2.  **Lifespan Manager:** The `lifespan` function is defined using `@asynccontextmanager`. The code before the `yield` statement is designated as startup logic.
3.  **Startup:** When initializing FastAPI via `app = FastAPI(lifespan=lifespan)`, FastAPI knows to execute the startup portion of the `lifespan` manager. This triggers `cache.run_precomputation()`.
    - The cache loads any existing data from `sales_report_cache.json`.
    - It inspects `get_sales_report` for `Enum` or `Literal` parameters.
    - It iterates through all combinations not already in the cache, executes the original function, and saves the result.
4.  **Decoration & Live Requests:** The `@cache.precompute` decorator works as before. It registers the function for pre-computation and replaces it with a fast version that serves results directly from the cache during live requests.



---

### 4. How to Run the Example

Place all the files as described in the structure.

#### `examples/main.py`

Use the example code from the `README.md` and save it in this file.

```python
# examples/main.py

from enum import Enum
from fastapi import FastAPI
import asyncio
from fastapi-cacher import fastapi-cacher # Assuming fastapi-cacher is installed or in PYTHONPATH

# 1. Initialize FastAPI and fastapi-cacher
app = FastAPI()
# Give the cache file a descriptive name
cache = fastapi-cacher(cache_file_path="sales_report_cache.json")

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

# Example of a response model if you want to use one
from pydantic import BaseModel
class Report(BaseModel):
    subregion: SubregionEnum
    store_id: StoreIDEnum
    data: dict

# 2. Apply the decorator to your slow endpoint
# The response_model is still useful for validation and documentation
@app.get("/sales-report", response_model=Report)
@cache.precompute
async def get_sales_report(subregion: SubregionEnum, store_id: StoreIDEnum):
    """
    A slow endpoint that simulates complex database queries.
    This original function will only be called during the pre-computation phase.
    """
    # This print statement shows when the *actual* logic is running
    print(f"--- Running original slow function for {subregion.value}/{store_id.value} ---")
    await asyncio.sleep(2)  # Simulate a 2-second delay for database queries

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

#### Running the Server

From your terminal in the `fastapi-cacher-project` directory:

```bash
# First, ensure dependencies are installed (FastAPI and Uvicorn)
pip install fastapi "uvicorn[standard]"

# Run the example app
uvicorn examples.main:app --reload
```

**First Run:**
You will see the pre-computation logs in your terminal, taking about `3 subregions * 5 stores * 2 seconds = 30 seconds`.

**Subsequent Runs:**
When you restart the server, you will see a log saying "All combinations were already cached," and the server will start instantly. Any request to the endpoint will be served immediately from the cache.

**Generated `sales_report_cache.json`:**
A file will be created in your `examples` directory that looks like this (truncated):

```json
{
    "get_sales_report::(('store_id', <StoreIDEnum.STORE_101: '101'>), ('subregion', <SubregionEnum.EMEA: 'EMEA'>))": {
        "subregion": "EMEA",
        "store_id": "101",
        "data": {
            "revenue": 101000
        }
    },
    "get_sales_report::(('store_id', <StoreIDEnum.STORE_202: '202'>), ('subregion', <SubregionEnum.EMEA: 'EMEA'>))": {
        "subregion": "EMEA",
        "store_id": "202",
        "data": {
            "revenue": 202000
        }
    },
    "...": "..."
}
```
You can manually edit the revenue values in this file, restart the server, and your API will serve the new, edited values.