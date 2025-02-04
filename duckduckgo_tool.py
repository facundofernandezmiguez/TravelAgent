from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from duckduckgo_search import ddg

class TravelSearch:
    def __init__(self):
        pass

    def search(self, query: str, travel_info: Any) -> str:
        """Search for travel information using DuckDuckGo search.
        
        Args:
            query: The search query
            travel_info: TravelInfo object
            
        Returns:
            JSON string with search results
        """
        try:
            results = []
            destination = travel_info.destination
            
            # Search for attractions
            attractions_query = f"best tourist attractions in {destination}"
            duck_results = ddg(attractions_query, max_results=5) or []
            attractions_results = []
            for result in duck_results[:3]:
                title = result.get('title', 'No Title')
                url = result.get('href', '')
                snippet = result.get('body', '') or result.get('snippet', '')
                content = snippet if snippet else f"Información sobre atracciones en {destination} no disponible."
                attractions_results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "content": content[:500]
                })
            
            if attractions_results:
                results.append(("Tourist Attractions", attractions_results))
            
            # Search for travel tips
            tips_query = f"travel tips for visiting {destination}"
            tips_duck_results = ddg(tips_query, max_results=5) or []
            tips_results = []
            for result in tips_duck_results[:2]:
                title = result.get('title', 'No Title')
                url = result.get('href', '')
                snippet = result.get('body', '') or result.get('snippet', '')
                content = snippet if snippet else f"Información sobre consejos de viaje para {destination} no disponible."
                tips_results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "content": content[:500]
                })
            
            if tips_results:
                results.append(("Travel Tips", tips_results))
            
            if not results:
                raise Exception("No se pudieron obtener resultados de búsqueda. Por favor, intentá nuevamente.")
            
            formatted_results = {
                "search_criteria": {
                    "destination": destination,
                    "start_date": travel_info.start_date,
                    "end_date": travel_info.end_date,
                    "travelers": travel_info.num_travelers,
                    "budget": travel_info.budget
                },
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(formatted_results, ensure_ascii=False)
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return json.dumps({"error": str(e), "results": []})
