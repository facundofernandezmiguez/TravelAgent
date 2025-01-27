from datetime import datetime
import os
import time
from dotenv import load_dotenv
from pathlib import Path
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import json
import yaml
import re
from api_key_manager import APIKeyManager
from duckduckgo_tool import TravelSearch

# Load environment variables
load_dotenv()

# Load prompts
prompts_path = Path(__file__).parent / "prompts.yaml"
with open(prompts_path, 'r', encoding='utf-8') as f:
    PROMPTS = yaml.safe_load(f)

class TravelInfo:
    """Class to store travel information."""
    def __init__(self):
        self.origin = None
        self.destination = None
        self.start_date = None
        self.end_date = None
        self.num_travelers = None
        self.budget = None
        self.interests = []
        # Preferences as individual fields
        self.accommodation = None
        self.location = None
        self.transport = None
        self.meals = None
        self.requirements = None

    def get_missing_info(self):
        """Return a list of missing required information."""
        missing = []
        if self.origin is None:
            missing.append("origen")
        if self.destination is None:
            missing.append("destino")
        if self.start_date is None:
            missing.append("fecha de inicio")
        if self.end_date is None:
            missing.append("fecha de fin")
        if self.num_travelers is None:
            missing.append("número de viajeros")
        if self.budget is None:
            missing.append("presupuesto")
        if not self.interests:
            missing.append("intereses")
        return missing

    def has_required_info(self):
        """Check if we have all required information for an itinerary."""
        return not bool(self.get_missing_info())

    def _format_value(self, value):
        """Format a value for display."""
        if value is None:
            return "None"
        if isinstance(value, list):
            return [str(v) for v in value]
        return str(value)

    def __str__(self) -> str:
        """String representation of travel info."""
        info = [
            "Current Travel Info:",
            f"Origin: {self._format_value(self.origin)}",
            f"Destination: {self._format_value(self.destination)}",
            f"Start Date: {self._format_value(self.start_date)}",
            f"End Date: {self._format_value(self.end_date)}",
            f"Travelers: {self._format_value(self.num_travelers)}",
            f"Budget: {self._format_value(self.budget)}",
            f"Interests: {self._format_value(self.interests)}"
        ]
        
        # Add preferences section
        preferences = []
        if any([self.accommodation, self.location, self.transport, self.meals, self.requirements]):
            preferences.extend([
                "Preferencias:",
                f"  - Alojamiento: {self._format_value(self.accommodation)}",
                f"  - Ubicación: {self._format_value(self.location)}",
                f"  - Transporte: {self._format_value(self.transport)}",
                f"  - Comidas: {self._format_value(self.meals)}",
                f"  - Requisitos: {self._format_value(self.requirements)}"
            ])
            info.extend(preferences)
        
        return "\n".join(info)

class TravelAgent:
    def __init__(self):
        """Initialize the travel agent."""
        self.api_key_manager = APIKeyManager()
        self.llm = ChatGroq(
            temperature=0.7,
            groq_api_key=self.api_key_manager.get_api_key(),
            model_name=os.getenv('GROQ_MODEL_NAME')
        )
        self.travel_info = TravelInfo()
        self.conversation_history = []  # Restaurar historial
        self.travel_search = TravelSearch()  # Inicializar el buscador

    def _debug_print_info(self):
        """Debug method to print current travel info"""
        print("\nCurrent Travel Info:")
        print(f"Origin: {self.travel_info.origin}")
        print(f"Destination: {self.travel_info.destination}")
        print(f"Start Date: {self.travel_info.start_date}")
        print(f"End Date: {self.travel_info.end_date}")
        print(f"Travelers: {self.travel_info.num_travelers}")
        print(f"Budget: {self.travel_info.budget}")
        print(f"Interests: {self.travel_info.interests}\n")
        print(f"Preferences:")
        print(f"  - Alojamiento: {self.travel_info.accommodation}")
        print(f"  - Ubicación: {self.travel_info.location}")
        print(f"  - Transporte: {self.travel_info.transport}")
        print(f"  - Comidas: {self.travel_info.meals}")
        print(f"  - Requisitos: {self.travel_info.requirements}\n")

    def _handle_rate_limit_error(self, error_message: str, retry_function, *args, **kwargs):
        """Handle rate limit error by rotating API keys and retrying."""
        # Get next available key
        next_key = self.api_key_manager.handle_rate_limit_error(error_message, self.llm.groq_api_key)
        if next_key:
            print(f"Switching to next API key...")
            self.llm.groq_api_key = next_key
            return retry_function(*args, **kwargs)
        else:
            print("No API keys available. All are at rate limit.")
            wait_time = self._get_wait_time_from_error(error_message)
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
            return retry_function(*args, **kwargs)

    def _get_wait_time_from_error(self, error_message: str) -> int:
        """Extract wait time from rate limit error message."""
        try:
            time_match = re.search(r'try again in (\d+)m(\d+)', error_message)
            if time_match:
                minutes, seconds = map(int, time_match.groups())
                return (minutes * 60) + int(seconds)
        except:
            pass
        return 2  # default wait time

    def _extract_json(self, text: str) -> dict:
        """Extract and parse JSON from text using multiple patterns."""
        print("\nTrying to extract JSON from:", text)
        
        # List of possible JSON patterns from most to least specific
        patterns = [
            r'```json\s*(\{[^}]+\})\s*```',  # Standard code block
            r'```\s*(\{[^}]+\})\s*```',      # Code block without json
            r'\{\s*"[^"]+"\s*:\s*"[^"]+"\s*\}', # Simple one-field JSON
            r'\{\s*"[^}]+\}'                  # Any JSON-like structure
        ]
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    print(f"\nMatched pattern: {pattern}")
                    print(f"Extracted JSON string: {json_str}")
                    
                    # Clean up the JSON string
                    json_str = re.sub(r'[\n\r\t\s]+', ' ', json_str)
                    json_str = json_str.strip()
                    print(f"Cleaned JSON string: {json_str}")
                    
                    # Parse JSON
                    info = json.loads(json_str)
                    print(f"Successfully parsed JSON: {info}")
                    return info
            except Exception as e:
                print(f"Failed with pattern {pattern}: {str(e)}")
                continue
        
        raise ValueError("No valid JSON found in response")

    def process_message(self, message: str) -> str:
        """Process a message from the user and return a response."""
        # Print current info for debugging (solo una vez)
        print("\n=== TRAVEL INFO ANTES ===")
        self._debug_print_info()
        print("===========================\n")
        
        while True:
            try:
                # Get a fresh API key and update the LLM
                try:
                    self.llm.groq_api_key = self.api_key_manager.get_api_key()
                except Exception as e:
                    if "rate limited" in str(e).lower():
                        return f"Lo siento, todas las API keys están en rate limit. {str(e)}"
                    return "Lo siento, estamos experimentando problemas técnicos en este momento. Por favor, intentá más tarde."
                
                # Add user message to history
                self.conversation_history.append({"role": "user", "content": message})
                
                # Format conversation history
                history_text = ""
                for msg in self.conversation_history[-6:-1]:  # Last 5 messages excluding current
                    if msg["role"] == "user":
                        history_text += f"Usuario: {msg['content']}\n"
                    else:
                        history_text += f"Asistente: {msg['content']}\n"
                
                # Format preferences for prompt
                preferences = {
                    "accommodation": self.travel_info.accommodation,
                    "location": self.travel_info.location,
                    "transport": self.travel_info.transport,
                    "meals": self.travel_info.meals,
                    "requirements": self.travel_info.requirements
                }
                preferences_str = ", ".join(f"{k}: {v}" for k, v in preferences.items() if v) or "no especificado"
                
                # Format travel info for the prompt
                extraction_prompt = PROMPTS['extraction'].format(
                    message=message,
                    conversation_history=history_text,
                    origin=self.travel_info.origin or "no especificado",
                    destination=self.travel_info.destination or "no especificado",
                    start_date=self.travel_info.start_date or "no especificado",
                    end_date=self.travel_info.end_date or "no especificado",
                    travelers=self.travel_info.num_travelers or "no especificado",
                    budget=self.travel_info.budget or "no especificado",
                    interests=", ".join(self.travel_info.interests) if self.travel_info.interests else "no especificado",
                    preferences=preferences_str
                )
                
                try:
                    # Get extraction response from LLM
                    extraction_response = self.llm.invoke(extraction_prompt)
                    response_text = extraction_response.content.strip()
                    
                    print("\n=== RESPUESTA DEL LLM ===")
                    print(response_text)
                    print("===========================\n")
                    
                    # Try to extract JSON from response if present
                    try:
                        info = self._extract_json(response_text)
                        
                        # Update travel info with new values, only if they're not empty or "no especificado"
                        if info.get('destination') and info['destination'] != "no especificado":
                            self.travel_info.destination = info['destination']
                        if info.get('origin') and info['origin'] != "no especificado":
                            self.travel_info.origin = info['origin']
                        if info.get('start_date') and info['start_date'] != "no especificado":
                            self.travel_info.start_date = info['start_date']
                        if info.get('end_date') and info['end_date'] != "no especificado":
                            self.travel_info.end_date = info['end_date']
                        if info.get('num_travelers') and info['num_travelers'] != "no especificado":
                            self.travel_info.num_travelers = info['num_travelers']
                        if info.get('budget') and info['budget'] != "no especificado":
                            self.travel_info.budget = info['budget']
                        if (info.get('interests') and 
                            isinstance(info['interests'], list) and 
                            info['interests'] and 
                            "no especificado" not in info['interests']):
                            self.travel_info.interests = info['interests']
                        for pref in ['accommodation', 'location', 'transport', 'meals', 'requirements']:
                            if info.get(pref) and info[pref] != "no especificado":
                                setattr(self.travel_info, pref, info[pref])
                    except ValueError as e:
                        # Si no hay JSON, asumimos que es una respuesta de seguimiento
                        if "No valid JSON found" in str(e):
                            print("No JSON found - assuming follow-up response")
                        else:
                            raise e
                    
                    # Try to extract response from the LLM's output
                    response_match = re.search(r'<RESPONSE>(.*?)</RESPONSE>', response_text, re.DOTALL)
                    if response_match:
                        response = response_match.group(1).strip()
                    else:
                        # If no <RESPONSE> tag is found, use the entire response text
                        response = response_text.strip()
                    
                    # Verificar si tenemos toda la información requerida
                    if self.travel_info.has_required_info():
                        if "¡Perfecto! Creo que ya tenemos bastante informacion" in response:
                            if any(confirm in message.lower() for confirm in ["si", "sí", "dale", "ok", "listo", "perfecto"]):
                                destination = self.travel_info.destination
                                response = f"¡Excelente! Vamos a crear un itinerario increíble para tu viaje a {destination}. \n\nComenzaré buscando las mejores actividades y lugares que se ajusten a tus intereses y presupuesto.\n\nDame un momento mientras preparo un itinerario detallado para vos... ✨"
                    
                    self.conversation_history.append({"role": "assistant", "content": response})
                    return response
                    
                except Exception as e:
                    print(f"\n=== ERROR COMPLETO ===")
                    print(f"Tipo de error: {type(e)}")
                    print(f"Mensaje de error: {str(e)}")
                    print("===========================\n")
                    
                    if "rate limit" in str(e).lower():
                        print(f"Rate limit error with key {self.llm.groq_api_key[-8:]}")
                        self.api_key_manager.handle_rate_limit(self.llm.groq_api_key, str(e))
                        continue  # Intentar con la siguiente key
                    raise e
                    
            except Exception as e:
                return f"Lo siento, ocurrió un error: {str(e)}"

if __name__ == "__main__":
    # Test the agent
    agent = TravelAgent()
    print(agent.process_message("Hola, quiero viajar a Madrid"))
