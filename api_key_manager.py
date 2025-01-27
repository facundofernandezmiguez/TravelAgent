import os
import random
import time
from datetime import datetime, timedelta
import re

class APIKeyManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APIKeyManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not APIKeyManager._initialized:
            """Initialize the API key manager."""
            print("\nCargando API keys:")
            self.api_keys = []
            self.rate_limits = {}  # key -> (limit_until, remaining_tokens)
            
            # Load all available API keys
            for i in range(1, 9):  # Aumentamos a 8 para incluir la nueva key
                key = os.getenv(f'GROQ_API_KEY{i}')
                if key and key.strip():  # Verificar que la key no esté vacía
                    key = key.strip()  # Eliminar espacios
                    if key not in self.api_keys:  # Evitar duplicados
                        print(f"API Key {i} encontrada: {key[-8:]}")
                        self.api_keys.append(key)
                        self.rate_limits[key] = (None, None)  # (limit_until, remaining_tokens)
                else:
                    print(f"API Key {i} no encontrada")
            
            print(f"Total de API keys cargadas: {len(self.api_keys)}\n")
            
            if not self.api_keys:
                raise ValueError("No API keys found in environment variables")
            
            APIKeyManager._initialized = True

    def handle_rate_limit(self, key: str, error_message: str):
        """Handle rate limit error for a specific key."""
        # Solo marcar como rate limited si el mensaje realmente indica un rate limit
        if "try again in" in error_message.lower() and "rate limit" in error_message.lower():
            # Extract organization ID
            org_match = re.search(r'organization `([^`]+)`', error_message)
            org_id = org_match.group(1) if org_match else "Unknown"
            print(f"\nAPI key {key[-8:]} pertenece a la organización: {org_id}")
            
            # Extract wait time from error message
            wait_time_match = re.search(r'try again in (\d+)m([\d.]+)s', error_message)
            if wait_time_match:
                minutes = int(wait_time_match.group(1))
                seconds = float(wait_time_match.group(2))
                wait_time = timedelta(minutes=minutes, seconds=seconds)
                self.rate_limits[key] = (datetime.now() + wait_time, None)
                print(f"API key {key[-8:]} rate limited. Will be available in {minutes}m {seconds:.2f}s")
            else:
                # Si no podemos parsear el tiempo, usar un tiempo más corto
                self.rate_limits[key] = (datetime.now() + timedelta(seconds=30), None)
                print(f"API key {key[-8:]} rate limited. Setting default wait time of 30 seconds")
        else:
            print(f"Error no relacionado con rate limit para key {key[-8:]}: {error_message}")

    def get_next_available_key(self) -> str:
        """Get the next available API key that's not rate limited."""
        current_time = datetime.now()
        
        print("\nVerificando disponibilidad de API keys:")
        for key in self.api_keys:
            limit_until, _ = self.rate_limits[key]
            if limit_until is None or current_time > limit_until:
                print(f"API key {key[-8:]} está disponible")
                return key
            else:
                wait_time = (limit_until - current_time).total_seconds()
                print(f"API key {key[-8:]} en rate limit por {wait_time:.2f} segundos")
        
        # Si llegamos aquí, todas las keys están limitadas
        # Encontrar la key que estará disponible más pronto
        min_wait_time = float('inf')
        for key in self.api_keys:
            limit_until, _ = self.rate_limits[key]
            if limit_until:
                wait_time = (limit_until - current_time).total_seconds()
                min_wait_time = min(min_wait_time, wait_time)
        
        raise Exception(f"All API keys are rate limited. Shortest wait time: {min_wait_time:.2f} seconds")

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