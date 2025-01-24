import os
import random
import time
from datetime import datetime, timedelta

class APIKeyManager:
    def __init__(self):
        """Initialize the API key manager."""
        self.api_keys = []
        self.rate_limits = {}  # key -> (limit_until, remaining_tokens)
        self.tried_keys = set()  # Conjunto de keys ya intentadas en el ciclo actual
        
        # Load all available API keys
        for i in range(1, 9):  # Aumentamos a 8 para incluir la nueva key
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
        
        # Si ya intentamos todas las keys, reiniciar el conjunto de intentadas
        if len(self.tried_keys) >= len(self.api_keys):
            self.tried_keys.clear()
        
        # First try to find keys that's not rate limited and no han sido intentadas
        for key in self.api_keys:
            limit_until, _ = self.rate_limits[key]
            if key not in self.tried_keys and (limit_until is None or current_time > limit_until):
                available_keys.append(key)
        
        if not available_keys:
            # Si no hay keys disponibles que no se hayan intentado, calcular tiempo de espera
            wait_times = [(limit_until - current_time).total_seconds() 
                         for limit_until, _ in self.rate_limits.values() 
                         if limit_until is not None]
            if wait_times:
                min_wait = min(wait_times)
                raise Exception(f"All API keys are rate limited. Please wait {min_wait:.2f} seconds before trying again.")
            
            raise Exception("No API keys available")
        
        # Usar la primera key disponible que no hemos intentado
        selected_key = available_keys[0]
        self.tried_keys.add(selected_key)
        return selected_key

    def handle_rate_limit(self, key: str, error_message: str):
        """Handle rate limit error for a specific key."""
        # Extract wait time from error message
        import re
        wait_time_match = re.search(r'try again in (\d+)m([\d.]+)s', error_message)
        if wait_time_match:
            minutes = int(wait_time_match.group(1))
            seconds = float(wait_time_match.group(2))
            wait_time = timedelta(minutes=minutes, seconds=seconds)
            self.rate_limits[key] = (datetime.now() + wait_time, None)
            print(f"API key {key[-8:]} rate limited. Will be available in {minutes}m {seconds:.2f}s")
        else:
            # If we can't parse the wait time, set a default of 2 minutes
            self.rate_limits[key] = (datetime.now() + timedelta(minutes=2), None)
            print(f"API key {key[-8:]} rate limited. Setting default wait time of 2 minutes")

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