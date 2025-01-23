import os
import random
import time
from datetime import datetime, timedelta

class APIKeyManager:
    def __init__(self):
        """Initialize the API key manager."""
        self.api_keys = []
        self.rate_limits = {}  # key -> (limit_until, remaining_tokens)
        
        # Load all available API keys
        for i in range(1, 8):  # We have keys from 1 to 7
            key = os.getenv(f'GROQ_API_KEY{i}')
            if key:
                self.api_keys.append(key)
                self.rate_limits[key] = (None, None)  # (limit_until, remaining_tokens)
        
        if not self.api_keys:
            raise ValueError("No API keys found in environment variables")

    def get_next_available_key(self) -> str:
        """Get the next available API key that's not rate limited."""
        current_time = datetime.now()
        available_keys = []
        
        for key in self.api_keys:
            limit_until, _ = self.rate_limits[key]
            if limit_until is None or current_time > limit_until:
                available_keys.append(key)
        
        if not available_keys:
            # Calculate the shortest wait time
            wait_times = [(limit_until - current_time).total_seconds() 
                         for limit_until, _ in self.rate_limits.values() 
                         if limit_until is not None]
            if wait_times:
                min_wait = min(wait_times)
                print(f"All API keys are rate limited. Shortest wait time: {min_wait:.2f} seconds")
                time.sleep(min_wait + 1)  # Add 1 second buffer
                return self.get_next_available_key()
            
            raise Exception("No API keys available and no rate limit information")
        
        return random.choice(available_keys)

    def handle_rate_limit(self, key: str, error_message: str):
        """Handle rate limit error for a specific key."""
        # Extract wait time from error message
        import re
        wait_time_match = re.search(r'try again in (\d+)m([\d.]+)s', error_message)
        if wait_time_match:
            minutes = int(wait_time_match.group(1))
            seconds = float(wait_time_match.group(2))
            wait_time = timedelta(minutes=minutes, seconds=seconds)
            self.rate_limits[key] = (datetime.now() + wait_time, 0)
            print(f"API key {key[-8:]} rate limited. Will be available in {minutes}m {seconds:.2f}s")
        else:
            # If we can't parse the wait time, set a default of 5 minutes
            self.rate_limits[key] = (datetime.now() + timedelta(minutes=5), 0)
            print(f"API key {key[-8:]} rate limited. Setting default wait time of 5 minutes")

    def update_rate_limit(self, key: str, remaining_tokens: int):
        """Update the remaining tokens for a key."""
        self.rate_limits[key] = (None, remaining_tokens)

    def get_api_key(self) -> str:
        """Get an API key that's not rate limited."""
        return self.get_next_available_key()

    def wait_if_needed(self, key: str):
        """Check if we need to wait for rate limits and wait if necessary."""
        limit_until, _ = self.rate_limits.get(key, (None, None))
        if limit_until:
            current_time = datetime.now()
            if current_time < limit_until:
                wait_time = (limit_until - current_time).total_seconds()
                print(f"Waiting {wait_time:.2f} seconds for rate limit on key {key[-8:]}")
                time.sleep(wait_time + 1)  # Add 1 second buffer