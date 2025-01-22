import os
import time
import re
from typing import Optional, Dict, List

class APIKeyManager:
    def __init__(self, prefix: str = "GROQ_API_KEY"):
        """Initialize API Key Manager.
        
        Args:
            prefix: Prefix for environment variables containing API keys (e.g., GROQ_API_KEY)
        """
        self.prefix = prefix
        self.api_keys: List[str] = []
        self.current_key_index = 0
        self.key_rate_limits: Dict[str, Dict] = {}  # Track rate limits for each key
        self.load_api_keys()

    def load_api_keys(self) -> None:
        """Load API keys from environment variables PREFIX_1, PREFIX_2, etc."""
        i = 1
        while True:
            key = os.getenv(f'{self.prefix}{i}')
            if not key:
                break
            # Remove quotes if present
            key = key.strip('"\'')
            self.api_keys.append(key)
            self.key_rate_limits[key] = {
                'used_tokens': 0,
                'window_start': time.time(),
                'last_used': 0
            }
            i += 1
        
        if not self.api_keys:
            # Fallback to the original API key without number
            key = os.getenv(self.prefix)
            if key:
                # Remove quotes if present
                key = key.strip('"\'')
                self.api_keys.append(key)
                self.key_rate_limits[key] = {
                    'used_tokens': 0,
                    'window_start': time.time(),
                    'last_used': 0
                }

    def get_next_available_key(self) -> Optional[str]:
        """Get the next available API key that hasn't hit rate limits."""
        if not self.api_keys:
            return None

        start_index = self.current_key_index
        current_time = time.time()

        # Try each key in rotation
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_key_index]
            limits = self.key_rate_limits[key]
            
            # Reset window if needed
            if current_time - limits['window_start'] >= 60:  # 60 second window
                limits['used_tokens'] = 0
                limits['window_start'] = current_time

            # Check if key is available
            if limits['used_tokens'] < 100000:  # Token limit per minute
                return key

            # Try next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            # If we've tried all keys and come back to start, wait for the first one to reset
            if self.current_key_index == start_index:
                oldest_window = min(v['window_start'] for v in self.key_rate_limits.values())
                wait_time = 60 - (current_time - oldest_window)
                if wait_time > 0:
                    print(f"All API keys are at rate limit. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    return self.get_next_available_key()

        return None

    def update_rate_limit(self, key: str, tokens_used: int) -> None:
        """Update the rate limit tracking for a key."""
        if key in self.key_rate_limits:
            self.key_rate_limits[key]['used_tokens'] += tokens_used
            self.key_rate_limits[key]['last_used'] = time.time()

    def handle_rate_limit_error(self, error_message: str, current_key: str) -> Optional[str]:
        """Handle rate limit error by finding the next available key.
        
        Args:
            error_message: The error message from the API
            current_key: The key that hit the rate limit
            
        Returns:
            The next available key, or None if no keys are available
        """
        try:
            # Extract tokens used from error message
            tokens_match = re.search(r'Used (\d+)', error_message)
            if tokens_match:
                tokens_used = int(tokens_match.group(1))
                self.update_rate_limit(current_key, tokens_used)

            # Get next available key
            return self.get_next_available_key()

        except Exception as e:
            print(f"Error in handle_rate_limit_error: {str(e)}")
            return None

    def wait_if_needed(self, key: str) -> None:
        """Wait if needed to respect rate limits for a specific key."""
        current_time = time.time()
        
        if key not in self.key_rate_limits:
            return

        limits = self.key_rate_limits[key]
        
        # Wait for minimum interval between calls
        time_since_last = current_time - limits['last_used']
        if time_since_last < 1:
            time.sleep(1 - time_since_last)
        
        # If we're close to the rate limit, wait for window reset
        if limits['used_tokens'] > 100000 * 0.9:  # 90% of limit
            time_until_reset = 60 - (current_time - limits['window_start'])
            if time_until_reset > 0:
                print(f"Approaching rate limit, waiting {int(time_until_reset)} seconds for reset...")
                time.sleep(time_until_reset)
                limits['used_tokens'] = 0
                limits['window_start'] = time.time()
        
        limits['last_used'] = time.time()
