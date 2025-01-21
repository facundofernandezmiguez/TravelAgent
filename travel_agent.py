from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_groq import ChatGroq
from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
import json
import yaml
from duckduckgo_search import DDGS

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Load API keys
groq_api_key = os.getenv('GROQ_API_KEY')
model_name = os.getenv('GROQ_MODEL_NAME')

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
        
    def is_complete(self):
        """Check if all required information is gathered."""
        required_fields = ['origin', 'destination', 'start_date', 'end_date', 'num_travelers', 'budget']
        return all(getattr(self, field) is not None for field in required_fields)
    
    def get_missing_info(self):
        """Get list of missing information fields."""
        missing = []
        if not self.origin:
            missing.append("origen")
        if not self.destination:
            missing.append("destino")
        if not self.start_date:
            missing.append("fecha de inicio")
        if not self.end_date:
            missing.append("fecha de fin")
        if not self.num_travelers:
            missing.append("número de viajeros")
        if not self.budget:
            missing.append("presupuesto")
        return missing

class TravelAgent:
    def __init__(self):
        self.travel_info = TravelInfo()
        self.conversation_history = []
        
        # Create LLM
        self.llm = ChatGroq(
            temperature=0.7,
            model_name=model_name,
            groq_api_key=groq_api_key
        )
        
        # Initialize the agent with memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # Create tools list
        tools = [
            Tool(
                name="search_flights",
                func=self._search_flights,
                description="Search for specific flights, hotels, and activities. Returns actual links to booking pages."
            )
        ]
        
        # Initialize the agent
        self.agent = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=10,
            max_execution_time=30,
            memory=self.memory
        )

    def get_conversation_history(self):
        """Return the conversation history in a format suitable for Streamlit."""
        return self.conversation_history

    def _search_flights(self, query: str) -> str:
        """Search for flights and travel information."""
        results = []
        
        try:
            with DDGS() as ddgs:
                # Search for flights with more specific parameters
                flight_results = list(ddgs.text(
                    f"flight tickets {query} price schedule site:skyscanner.com OR site:kayak.com OR site:expedia.com",
                    max_results=4
                ))
                if flight_results:
                    results.append(("Flights", flight_results))
                
                # Search for hotels with ratings and prices
                destination = query.split('to')[1].strip().split()[0]  # Get just the city name
                hotel_results = list(ddgs.text(
                    f"hotels in {destination} price per night rating site:booking.com OR site:hotels.com",
                    max_results=4
                ))
                if hotel_results:
                    results.append(("Hotels", hotel_results))
                
                # Search for activities with prices and duration
                activity_results = list(ddgs.text(
                    f"top rated tourist activities {destination} price duration site:getyourguide.com OR site:viator.com",
                    max_results=4
                ))
                if activity_results:
                    results.append(("Activities", activity_results))
            
            # Add metadata to help format results
            formatted_results = {
                "search_criteria": query,
                "results": results,
                "timestamp": datetime.now().isoformat(),
                "required_format": {
                    "flights": "✈️ [Precio] [Aerolínea - Horario](link)",
                    "hotels": "🏨 [Precio/noche] [Nombre - Estrellas](link)",
                    "activities": "🎯 [Precio] [Nombre - Duración](link)"
                }
            }
            
            return json.dumps(formatted_results, ensure_ascii=False)
        except Exception as e:
            print(f"Search error: {str(e)}")
            return json.dumps({"error": str(e), "results": []})

    def _extract_info_from_message(self, message: str) -> bool:
        """Extract travel information from user message using LLM.
        Returns True if any information was updated."""
        try:
            # Debug: Print input message
            print(f"Extracting info from: {message}")
            
            response = self.llm.invoke(PROMPTS['extraction'].format(message=message))
            
            # Debug: Print LLM response
            print(f"LLM response: {response.content}")
            
            info = json.loads(response.content)
            
            # Debug: Print parsed info
            print(f"Parsed info: {info}")
            
            updated = False
            # Update travel info with extracted values
            if "origin" in info and self.travel_info.origin is None:
                self.travel_info.origin = info["origin"]
                updated = True
            if "destination" in info and self.travel_info.destination is None:
                self.travel_info.destination = info["destination"]
                updated = True
            if "start_date" in info and self.travel_info.start_date is None:
                self.travel_info.start_date = info["start_date"]
                updated = True
            if "end_date" in info and self.travel_info.end_date is None:
                self.travel_info.end_date = info["end_date"]
                updated = True
            if "num_travelers" in info and self.travel_info.num_travelers is None:
                self.travel_info.num_travelers = info["num_travelers"]
                updated = True
            if "budget" in info and self.travel_info.budget is None:
                self.travel_info.budget = info["budget"]
                updated = True
            
            # Debug: Print final state
            print(f"Updated: {updated}")
            print(f"Current travel info: {vars(self.travel_info)}")
            
            return updated
            
        except Exception as e:
            print(f"Error extracting information: {str(e)}")
            print(f"Response content: {response.content if 'response' in locals() else 'No response'}")
            return False

    async def process_message(self, user_input: str) -> str:
        """Process a user message and return a response."""
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Try to extract information from the message
            self._extract_info_from_message(user_input)
            
            # Always check if we need more information
            if not self.travel_info.is_complete():
                missing_info = self.travel_info.get_missing_info()
                next_info = missing_info[0] if missing_info else None
                
                # Map field names to friendly questions in Spanish
                question_map = {
                    "origen": "¿Desde qué ciudad querés viajar? 🛫",
                    "destino": "¿A qué ciudad te gustaría ir? 🌎",
                    "fecha de inicio": "¿En qué fecha te gustaría empezar el viaje? 📅",
                    "fecha de fin": "¿Cuándo pensás volver? 📅",
                    "número de viajeros": "¿Cuántas personas van a viajar? 👥",
                    "presupuesto": "¿Cuál es tu presupuesto aproximado para el viaje? 💰"
                }
                
                friendly_question = question_map.get(next_info, f"¿Me podrías decir {next_info}?")
                
                # Format the conversation prompt
                prompt = PROMPTS['conversation'].format(
                    question=friendly_question,
                    origin=self.travel_info.origin or '❓',
                    destination=self.travel_info.destination or '❓',
                    start_date=self.travel_info.start_date or '❓',
                    end_date=self.travel_info.end_date or '❓',
                    travelers=self.travel_info.num_travelers or '❓',
                    budget=self.travel_info.budget or '❓'
                )
                
                response = await self.agent.ainvoke({"input": prompt})
                response_text = response["output"]
                self.conversation_history.append({"role": "assistant", "content": response_text})
                return response_text
                
            # Only if we have all information, proceed with itinerary
            search_query = (
                f"flights from {self.travel_info.origin} to {self.travel_info.destination} "
                f"from {self.travel_info.start_date} to {self.travel_info.end_date}"
            )
            
            # Use search query in the itinerary request
            itinerary_request = PROMPTS['itinerary'].format(
                search_query=search_query,
                origin=self.travel_info.origin,
                destination=self.travel_info.destination,
                start_date=self.travel_info.start_date,
                end_date=self.travel_info.end_date,
                travelers=self.travel_info.num_travelers,
                budget=self.travel_info.budget
            )
            
            response = await self.agent.ainvoke({"input": itinerary_request})
            response_text = response["output"]
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
            
        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            raise

if __name__ == "__main__":
    # Test the conversational agent
    agent = TravelAgent()
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            break
        
        response = agent.process_message(user_input)
        print(f"\nAgent: {response}")
