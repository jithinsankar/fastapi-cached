# fastapicachex/cache.py
import json
import itertools
from functools import wraps
from pathlib import Path
from typing import Callable, Any

from .inspector import get_discrete_params

class FastAPICachex:
    """
    A class to provide pre-computation and caching for FastAPI endpoints
    with discrete parameters (Enum, Literal).
    """

    def __init__(self, cache_file_path: str = "fastapi_cache.json"):
        self.cache_file = Path(cache_file_path)
        self._cache: dict[str, Any] = {}
        self._precompute_targets: list[Callable] = []

    def _load_from_file(self):
        """Loads the cache from the JSON file if it exists."""
        if self.cache_file.exists():
            print(f"Loading cache from '{self.cache_file}'...")
            try:
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
                print(f"Cache loaded successfully with {len(self._cache)} items.")
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from '{self.cache_file}'. Starting with an empty cache.")
                self._cache = {}
        else:
            print("No existing cache file found. Starting with an empty cache.")
            self._cache = {}

    def _save_to_file(self):
        """Saves the current in-memory cache to the JSON file."""
        with open(self.cache_file, "w") as f:
            # Use default=str to handle complex types like Enums gracefully
            json.dump(self._cache, f, indent=4, default=str)

    def _generate_cache_key(self, func: Callable, kwargs: dict) -> str:
        """Generates a stable cache key from the function and its arguments."""
        # Sorting kwargs ensures that the key is the same regardless of argument order
        sorted_kwargs = tuple(sorted(kwargs.items(), key=lambda item: item[0]))
        return f"{func.__name__}::{str(sorted_kwargs)}"

    def precompute(self, func: Callable) -> Callable:
        """
        A decorator that marks a function for pre-computation and enables caching.
        """
        # Register the function for the startup computation
        self._precompute_targets.append(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # During a live request, generate key and serve from cache
            key = self._generate_cache_key(func, kwargs)
            if key in self._cache:
                print(f"Cache HIT for key: {key}")
                return self._cache[key]
            
            # This part is a fallback. In a fully pre-computed scenario,
            # it should ideally not be reached.
            print(f"Cache MISS for key: {key}. Executing original function.")
            result = await func(*args, **kwargs)
            # We can optionally add the result to the cache here as well
            # self._cache[key] = result
            # self._save_to_file()
            return result

        return wrapper

    async def run_precomputation(self):
        """
        The main pre-computation logic. Should be called on application startup.
        """
        print("--- Starting fastapicachex Pre-computation ---")
        self._load_from_file()

        total_new_computations = 0

        for func in self._precompute_targets:
            print(f"\nAnalyzing function: '{func.__name__}'")
            param_options = get_discrete_params(func)

            if not param_options:
                print(f"-> No discrete parameters (Enum/Literal) found for '{func.__name__}'. Skipping.")
                continue

            param_names = list(param_options.keys())
            value_combinations = list(itertools.product(*param_options.values()))
            
            print(f"-> Found {len(param_names)} discrete params: {', '.join(param_names)}")
            print(f"-> Total combinations to check: {len(value_combinations)}")

            for combo in value_combinations:
                kwargs = dict(zip(param_names, combo))
                key = self._generate_cache_key(func, kwargs)

                # This is the "resume" logic. If key exists, we skip.
                if key in self._cache:
                    continue
                
                # If not in cache, compute it now.
                print(f"Computing and caching for: {kwargs}...")
                try:
                    # Execute the original, slow function
                    result = await func(**kwargs)
                    self._cache[key] = result
                    total_new_computations += 1
                    # Save after each computation to ensure progress is not lost
                    self._save_to_file()
                except Exception as e:
                    print(f"ERROR computing for {kwargs}: {e}")

        print("\n--- fastapicachex Pre-computation Finished ---")
        if total_new_computations > 0:
            print(f"Completed {total_new_computations} new computations and saved to '{self.cache_file}'.")
        else:
            print("All combinations were already cached. No new computations were needed.")