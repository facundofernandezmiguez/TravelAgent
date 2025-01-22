from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from duckduckgo_search import DDGS

class TravelSearch:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, travel_info: Any) -> str:
        """Search for comprehensive travel information including flights, hotels, and activities.
        
        Args:
            query: The search query
            travel_info: TravelInfo object containing trip details
            
        Returns:
            JSON string containing search results
        """
        try:
            results = []
            
            # Parse the query to extract travel info
            destination = travel_info.destination or self._extract_destination(query)
            if not destination:
                return json.dumps({"error": "No destination found in query", "results": []})
            
            # Search for flights
            if travel_info.origin:
                flight_query = (
                    f"flight tickets from {travel_info.origin} to {destination} "
                    f"{travel_info.start_date if travel_info.start_date else ''} "
                    "price schedule site:skyscanner.com OR site:kayak.com OR site:expedia.com"
                )
                flight_results = list(self.ddgs.text(flight_query, max_results=4))
                if flight_results:
                    results.append(("Flights", flight_results))
            
            # Search for hotels
            room_type = self._get_room_type(travel_info.num_travelers)
            hotel_query = (
                f"hotels in {destination} {room_type} price per night rating "
                f"{travel_info.budget if travel_info.budget else ''} "
                "site:booking.com OR site:hotels.com"
            )
            hotel_results = list(self.ddgs.text(hotel_query, max_results=4))
            if hotel_results:
                results.append(("Hotels", hotel_results))
            
            # Search for activities based on interests
            if travel_info.interests:
                for interest in travel_info.interests:
                    activity_query = (
                        f"top rated {interest} activities {destination} price duration "
                        "site:getyourguide.com OR site:viator.com"
                    )
                    activity_results = list(self.ddgs.text(activity_query, max_results=2))
                    if activity_results:
                        results.append((f"{interest.title()} Activities", activity_results))
            
            # Add metadata to help format results
            formatted_results = {
                "search_criteria": {
                    "query": query,
                    "destination": destination,
                    "origin": travel_info.origin,
                    "start_date": travel_info.start_date,
                    "end_date": travel_info.end_date,
                    "travelers": travel_info.num_travelers,
                    "budget": travel_info.budget,
                    "interests": travel_info.interests
                },
                "results": results,
                "timestamp": datetime.now().isoformat(),
                "required_format": {
                    "flights": " [Precio] [Aerolínea - Horario](link)",
                    "hotels": " [Precio/noche] [Nombre - Estrellas](link)",
                    "activities": " [Precio] [Nombre - Duración](link)"
                }
            }
            
            return json.dumps(formatted_results, ensure_ascii=False)
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return json.dumps({"error": str(e), "results": []})

    def _extract_destination(self, query: str) -> Optional[str]:
        """Extract destination from query string."""
        try:
            parts = query.lower().split()
            for i, word in enumerate(parts):
                if word in ["to", "in", "at", "destination"]:
                    return parts[i + 1].title()
            return None
        except:
            return None

    def _get_room_type(self, num_travelers: Optional[int]) -> str:
        """Get appropriate room type based on number of travelers."""
        if not num_travelers:
            return ""
        if num_travelers == 1:
            return "single room"
        if num_travelers == 2:
            return "double room"
        return "family room"
