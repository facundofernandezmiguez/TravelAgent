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
        self.additional_notes = None

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
            f"Budget: {self._format_value(self.budget)}"
        ]
        
        if self.additional_notes:
            info.append(f"Additional Notes: {self._format_value(self.additional_notes)}")
        
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
        self.search_completed = False
        self.itinerary_created = False

    def _debug_print_info(self):
        """Debug method to print current travel info"""
        print("\nCurrent Travel Info:")
        print(f"Origin: {self.travel_info.origin}")
        print(f"Destination: {self.travel_info.destination}")
        print(f"Start Date: {self.travel_info.start_date}")
        print(f"End Date: {self.travel_info.end_date}")
        print(f"Travelers: {self.travel_info.num_travelers}")
        print(f"Budget: {self.travel_info.budget}")
        if self.travel_info.additional_notes:
            print(f"Additional Notes: {self.travel_info.additional_notes}\n")

    def _handle_rate_limit_error(self, error_message: str, retry_function, *args, **kwargs):
        """Handle rate limit error by rotating API keys and retrying."""
        # Handle rate limit error: update the current key and retry
        print("Handling rate limit error...")
        self.api_key_manager.handle_rate_limit(self.llm.groq_api_key, error_message)
        next_key = self.api_key_manager.get_api_key()
        print("Switching to next API key...")
        self.llm.groq_api_key = next_key
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
                    preferences=self.travel_info.additional_notes or "no especificado"
                )
                
                try:
                    # Get extraction response from LLM
                    max_retries = 3
                    retry_count = 0
                    while retry_count < max_retries:
                        try:
                            extraction_response = self.llm.invoke(extraction_prompt)
                            response_text = extraction_response.content.strip()
                            break
                        except Exception as e:
                            error_str = str(e).lower()
                            print("\n=== ERROR COMPLETO ===")
                            print(f"Tipo de error: {type(e)}")
                            print(f"Mensaje de error: {str(e)}")
                            print("===========================\n")
                            
                            if ("503" in error_str or "service unavailable" in error_str) and retry_count < max_retries - 1:
                                retry_count += 1
                                print(f"Reintentando... ({retry_count}/{max_retries})")
                                time.sleep(2)  # Wait 2 seconds before retry
                                continue
                            elif "rate limit" in error_str:
                                return self._handle_rate_limit_error(str(e), self.process_message, message)
                            else:
                                if "503" in error_str or "service unavailable" in error_str:
                                    return ("Lo siento, el servicio está temporalmente no disponible. "
                                           "Por favor, intentá nuevamente en unos minutos. 🔄")
                                else:
                                    return ("Disculpá, hubo un problema al procesar tu mensaje. "
                                           "Por favor, intentá nuevamente. Si el problema persiste, contactá al soporte. 🔧")
                    
                    print("\n=== RESPUESTA DEL LLM ===")
                    print(response_text)
                    print("===========================\n")
                    
                    # Extract only the RESPONSE content
                    response_match = re.search(r'<RESPONSE>\s*(.*?)\s*</RESPONSE>', response_text, re.DOTALL)
                    if response_match:
                        response = response_match.group(1).strip()
                    else:
                        response = "Lo siento, hubo un problema al procesar la respuesta. Por favor, intentá nuevamente. 🔧"
                    
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
                        if info.get('additional_notes') and info['additional_notes'] != "no especificado":
                            self.travel_info.additional_notes = info['additional_notes']
                    except ValueError as e:
                        # Si no hay JSON, asumimos que es una respuesta de seguimiento
                        if "No valid JSON found" in str(e):
                            print("No JSON found - assuming follow-up response")
                        else:
                            raise e
                    
                    # Verificar si tenemos toda la información requerida
                    if self.travel_info.has_required_info():
                        # Check if this is a confirmation response
                        user_confirmed = any(word in message.lower() for word in [
                            "si", "sí", "ok", "dale", "listo", "estamos listos", "estamos bien", "perfecto"
                        ])
                        
                        if user_confirmed and not self.search_completed:
                            # Set flag and perform search
                            self.search_completed = True
                            
                            # Send the searching message
                            searching_msg = (f"¡Excelente! Vamos a crear un itinerario increíble para tu viaje a {self.travel_info.destination}. \n\n"
                                          "Comenzaré buscando las mejores actividades y lugares que se ajusten a tus intereses y presupuesto.\n\n"
                                          "Dame un momento mientras preparo un itinerario detallado para vos... ✨")
                            
                            self.conversation_history.append({"role": "assistant", "content": searching_msg})
                            
                            # Perform the search
                            try:
                                # Search for attractions
                                attractions_query = f"best tourist attractions things to do travel guide {self.travel_info.destination}"
                                web_results = search_web(query=attractions_query)
                                
                                results = []
                                attractions_results = []
                                
                                # Process top 3 attraction results
                                for result in web_results[:3]:
                                    try:
                                        content = read_url_content(Url=result["url"])
                                        if content:
                                            attractions_results.append({
                                                "title": result["title"],
                                                "url": result["url"],
                                                "snippet": result["snippet"],
                                                "content": content[:500]  # Limit content length
                                            })
                                    except Exception as e:
                                        print(f"Error reading URL {result['url']}: {str(e)}")
                                        continue
                                
                                if attractions_results:
                                    results.append(("Tourist Attractions", attractions_results))
                                
                                # Search for travel tips
                                if results:
                                    tips_query = f"travel tips recommendations best time to visit {self.travel_info.destination} tourist guide"
                                    tips_web_results = search_web(query=tips_query)
                                    
                                    tips_results = []
                                    for result in tips_web_results[:2]:
                                        try:
                                            content = read_url_content(Url=result["url"])
                                            if content:
                                                tips_results.append({
                                                    "title": result["title"],
                                                    "url": result["url"],
                                                    "snippet": result["snippet"],
                                                    "content": content[:500]
                                                })
                                        except Exception as e:
                                            print(f"Error reading URL {result['url']}: {str(e)}")
                                            continue
                                    
                                    if tips_results:
                                        results.append(("Travel Tips", tips_results))
                                
                                # If we got no results at all, return error
                                if not results:
                                    self.search_completed = False
                                    return "No pude encontrar información sobre ese destino. ¿Podrías confirmar si el destino está bien escrito? 🤔"
                                
                                # Format the itinerary prompt with search results
                                itinerary_prompt = PROMPTS['itinerary'].format(
                                    destination=self.travel_info.destination,
                                    start_date=self.travel_info.start_date,
                                    end_date=self.travel_info.end_date,
                                    travelers=self.travel_info.num_travelers,
                                    budget=self.travel_info.budget,
                                    search_results=json.dumps(results, ensure_ascii=False)
                                )
                                
                                # Get itinerary from LLM
                                try:
                                    itinerary_response = self.llm.invoke(itinerary_prompt)
                                    self.itinerary_created = True
                                    
                                    # Extract only the response content
                                    response_match = re.search(r'<RESPONSE>\s*(.*?)\s*</RESPONSE>', itinerary_response.content, re.DOTALL)
                                    if response_match:
                                        return response_match.group(1).strip()
                                    return itinerary_response.content.strip()
                                except Exception as e:
                                    error_str = str(e).lower()
                                    print("\n=== ERROR COMPLETO ===")
                                    print(f"Tipo de error: {type(e)}")
                                    print(f"Mensaje de error: {str(e)}")
                                    print("===========================\n")
                                    
                                    if "organization_restricted" in str(e):
                                        return ("Lo siento, hay un problema con el servicio de IA en este momento. "
                                               "Por favor, contactá al soporte técnico para resolver el problema de acceso. 🔧")
                                    elif "rate limit" in error_str:
                                        return ("El servicio está temporalmente ocupado. "
                                               "Por favor, intentá nuevamente en unos minutos. 🕒")
                                    else:
                                        return ("Hubo un problema al generar el itinerario. "
                                               "Por favor, intentá nuevamente. Si el problema persiste, contactá al soporte. 🔧")
                                
                            except json.JSONDecodeError:
                                print("Error parsing search results JSON")
                                self.search_completed = False
                                return "Hubo un problema procesando la información. ¿Podemos intentarlo nuevamente? 🔄"
                            except Exception as e:
                                print(f"Error during search: {str(e)}")
                                self.search_completed = False
                                if "Ratelimit" in str(e):
                                    return "El servicio está temporalmente no disponible por límite de uso. Por favor, intentá nuevamente en unos minutos. 🔄"
                                return "Lo siento, hubo un problema al buscar la información. ¿Podemos intentarlo nuevamente? 🔄"
                        
                        elif not user_confirmed or not self.search_completed:
                            # Show the confirmation message
                            confirmation_msg = (f"¡Perfecto! Creo que ya tenemos bastante informacion para planear tu itinerario. "
                                   "Antes confirmemos estos datos:\n\n"
                                   f"- Viaje: de {self.travel_info.origin} a {self.travel_info.destination}\n"
                                   f"- Fechas: del {self.travel_info.start_date} al {self.travel_info.end_date}\n"
                                   f"- Viajeros: {self.travel_info.num_travelers}\n"
                                   f"- Presupuesto: {self.travel_info.budget}\n"
                                   "¿Estamos listos para empezar la busqueda, o querés cambiar algo? ✨")
                            self.conversation_history.append({"role": "assistant", "content": confirmation_msg})
                            return confirmation_msg
                    
                    self.conversation_history.append({"role": "assistant", "content": response})
                    return response
                    
                except Exception as e:
                    error_str = str(e).lower()
                    print("\n=== ERROR COMPLETO ===")
                    print(f"Tipo de error: {type(e)}")
                    print(f"Mensaje de error: {str(e)}")
                    print("===========================\n")
                    
                    if "503" in error_str or "service unavailable" in error_str:
                        return ("Lo siento, el servicio está temporalmente no disponible. "
                               "Por favor, intentá nuevamente en unos minutos. 🔄")
                    elif "rate limit" in error_str:
                        return self._handle_rate_limit_error(str(e), self.process_message, message)
                    elif "APITimeoutError" in error_str:
                        print("Timeout error encountered, retrying after brief wait...")
                        time.sleep(2)
                        continue
                    else:
                        return ("Disculpá, hubo un problema al procesar tu mensaje. "
                               "Por favor, intentá nuevamente. Si el problema persiste, contactá al soporte. 🔧")
                    
            except Exception as e:
                return f"Lo siento, ocurrió un error: {str(e)}"

if __name__ == "__main__":
    # Test the agent
    agent = TravelAgent()
    print(agent.process_message("Hola, quiero viajar a Madrid"))
