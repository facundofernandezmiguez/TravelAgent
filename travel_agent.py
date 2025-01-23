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
    def __init__(self):
        self.origin = None
        self.destination = None
        self.start_date = None
        self.end_date = None
        self.num_travelers = None
        self.budget = None
        self.interests = []

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

class TravelAgent:
    def __init__(self):
        self.travel_info = TravelInfo()
        self.conversation_history = []
        self.api_key_manager = APIKeyManager()
        self.model_name = os.getenv('GROQ_MODEL_NAME')
        self.search = TravelSearch()
        
        # Create LLM with initial key
        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=self.api_key_manager.get_next_available_key(),
            model_name=self.model_name
        )
        
        # Create conversation memory
        self.memory = ConversationBufferMemory()
        
        # Create conversation chain
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=True
        )

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

    def process_message(self, message: str, retry_count: int = 0) -> str:
        """Process a message from the user and return a response."""
        try:
            # If we've retried too many times, give up
            if retry_count >= 2:
                return "Lo siento, estamos experimentando problemas técnicos en este momento. Por favor, intentá más tarde."
            
            # Wait if needed for rate limits
            self.api_key_manager.wait_if_needed(self.llm.groq_api_key)
            
            # Format conversation history
            conversation_text = ""
            for msg in self.conversation_history[-3:]:
                if msg["role"] == "user":
                    conversation_text += f"Usuario: {msg['content']}\n"
                else:
                    conversation_text += f"Asistente: {msg['content']}\n"
            
            # First get travel info from LLM without search results
            extraction_prompt = PROMPTS['extraction'].format(
                message=message,
                origin=self.travel_info.origin or "no especificado",
                destination=self.travel_info.destination or "no especificado",
                start_date=self.travel_info.start_date or "no especificado",
                end_date=self.travel_info.end_date or "no especificado",
                travelers=self.travel_info.num_travelers or "no especificado",
                budget=self.travel_info.budget or "no especificado",
                interests=", ".join(self.travel_info.interests) if self.travel_info.interests else "no especificado",
                conversation_history=conversation_text
            )
            
            # Get extraction response from LLM
            extraction_response = self.llm.invoke(extraction_prompt)
            response_text = extraction_response.content.strip()
            
            # Extract travel information from the response
            had_all_info = self.travel_info.has_required_info()
            try:
                # Look for JSON block in the response
                json_match = re.search(r'```json\s*({[^}]+})\s*```', response_text)
                if json_match:
                    info = json.loads(json_match.group(1))
                    # Update travel info with extracted values
                    for key in ["origin", "destination", "start_date", "end_date", "num_travelers", "budget"]:
                        if key in info and info[key]:
                            setattr(self.travel_info, key, info[key])
                    
                    if "interests" in info and info["interests"]:
                        new_interests = [i for i in info["interests"] if i not in self.travel_info.interests]
                        if new_interests:
                            self.travel_info.interests.extend(new_interests)
                    
                    # Remove the JSON block from the response
                    response_text = response_text.replace(json_match.group(0), "").strip()
            except Exception as e:
                print(f"Error extracting travel info from response: {str(e)}")
            
            # If we just got all required info, do a search and create itinerary
            if not had_all_info and self.travel_info.has_required_info():
                search_query = f"travel {self.travel_info.destination}"
                if self.travel_info.interests:
                    search_query += f" {' '.join(self.travel_info.interests)}"
                search_results = self.search_travel_info(search_query)
                
                # Get itinerary with search results
                itinerary_prompt = PROMPTS['itinerary'].format(
                    origin=self.travel_info.origin,
                    destination=self.travel_info.destination,
                    start_date=self.travel_info.start_date,
                    end_date=self.travel_info.end_date,
                    travelers=self.travel_info.num_travelers,
                    budget=self.travel_info.budget,
                    interests=", ".join(self.travel_info.interests),
                    search_results=search_results
                )
                itinerary_response = self.llm.invoke(itinerary_prompt)
                response_text = itinerary_response.content.strip()
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            return response_text
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error in process_message: {error_msg}")
            
            if "rate limit" in error_msg.lower():
                return self._handle_rate_limit_error(
                    error_msg,
                    self.process_message,
                    message,
                    retry_count + 1
                )
            
            return "Lo siento, ocurrió un error. Por favor, intentá nuevamente."

    def search_travel_info(self, query: str) -> str:
        """Search for travel information using the TravelSearch module."""
        return self.search.search(query, self.travel_info)

if __name__ == "__main__":
    # Test the agent
    agent = TravelAgent()
    print(agent.process_message("Hola, quiero viajar a Madrid"))
