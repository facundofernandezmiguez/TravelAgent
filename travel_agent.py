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

    def process_message(self, message: str, retry_count: int = 0) -> str:
        """Process a message from the user and return a response."""
        try:
            # If we've retried too many times, give up
            if retry_count >= 2:
                return "Lo siento, estamos experimentando problemas técnicos en este momento. Por favor, intentá más tarde."
            
            # Get a fresh API key and update the LLM
            self.llm.groq_api_key = self.api_key_manager.get_api_key()
            
            # Print current info for debugging
            print("\n=== TRAVEL INFO ANTES ===")
            self._debug_print_info()
            print("===========================\n")
            
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
            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower():
                    print(f"Rate limit error with key {self.llm.groq_api_key[-8:]}")
                    self.api_key_manager.handle_rate_limit(self.llm.groq_api_key, error_msg)
                    return self.process_message(message, retry_count)
                raise e
            
            print("\n=== RESPUESTA DEL LLM ===")
            print(response_text)
            print("===========================\n")
            
            # Extract info and response parts
            info_match = re.search(r'<EXTRACTED_INFO>\s*({[\s\S]*?})\s*</EXTRACTED_INFO>', response_text)
            response_match = re.search(r'<RESPONSE>\s*([\s\S]*?)\s*</RESPONSE>', response_text)
            
            # Update travel info if we have extracted info
            if info_match:
                try:
                    json_str = info_match.group(1)
                    travel_info = json.loads(json_str)
                    
                    # Update travel info with new values, only if they're not empty or "no especificado"
                    if travel_info.get('destination') and travel_info['destination'] != "no especificado":
                        self.travel_info.destination = travel_info['destination']
                    if travel_info.get('origin') and travel_info['origin'] != "no especificado":
                        self.travel_info.origin = travel_info['origin']
                    if travel_info.get('start_date') and travel_info['start_date'] != "no especificado":
                        self.travel_info.start_date = travel_info['start_date']
                    if travel_info.get('end_date') and travel_info['end_date'] != "no especificado":
                        self.travel_info.end_date = travel_info['end_date']
                    if travel_info.get('num_travelers') and travel_info['num_travelers'] != "no especificado":
                        self.travel_info.num_travelers = travel_info['num_travelers']
                    if travel_info.get('budget') and travel_info['budget'] != "no especificado":
                        self.travel_info.budget = travel_info['budget']
                    # Solo actualizar interests si es una lista válida y no contiene "no especificado"
                    if (travel_info.get('interests') and 
                        isinstance(travel_info['interests'], list) and 
                        travel_info['interests'] and 
                        "no especificado" not in travel_info['interests']):
                        self.travel_info.interests = travel_info['interests']
                    # Update preferences if present and valid
                    for pref in ['accommodation', 'location', 'transport', 'meals', 'requirements']:
                        if travel_info.get(pref) and travel_info[pref] != "no especificado":
                            setattr(self.travel_info, pref, travel_info[pref])
                    
                    print("\n=== TRAVEL INFO DESPUÉS ===")
                    self._debug_print_info()
                    print("===========================\n")
                except Exception as e:
                    print(f"Error parsing travel info: {str(e)}")
            
            # Get the actual response text
            response_text = response_match.group(1).strip() if response_match else "Lo siento, hubo un error procesando tu mensaje."
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Check if user confirmed and we should start search
            if (response_match and 
                "Dame un momento mientras preparo un itinerario detallado" in response_match.group(1)):
                # Perform the search
                search_results = self.travel_search.search("", self.travel_info)
                
                # Format itinerary prompt with search results
                itinerary_prompt = PROMPTS['itinerary'].format(
                    origin=self.travel_info.origin,
                    destination=self.travel_info.destination,
                    start_date=self.travel_info.start_date,
                    end_date=self.travel_info.end_date,
                    travelers=self.travel_info.num_travelers,
                    budget=self.travel_info.budget,
                    interests=", ".join(self.travel_info.interests) if self.travel_info.interests else "no especificado",
                    preferences=preferences_str,
                    search_results=search_results
                )
                
                # Get itinerary from LLM
                itinerary_response = self.llm.invoke(itinerary_prompt)
                return itinerary_response.content.strip()
            
            return response_text
            
        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            if retry_count < 2:
                return self.process_message(message, retry_count + 1)
            return "Lo siento, hubo un error procesando tu mensaje. Por favor, intentá de nuevo."

if __name__ == "__main__":
    # Test the agent
    agent = TravelAgent()
    print(agent.process_message("Hola, quiero viajar a Madrid"))
