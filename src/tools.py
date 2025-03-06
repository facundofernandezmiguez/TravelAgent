import json
import requests
from crewai.tools import BaseTool
from src.config import SERPER_API_KEY

class BuscadorWeb(BaseTool):
    name: str = "buscar_en_web"
    description: str = "Busca información sobre vuelos, hoteles o atracciones turísticas."
    
    def _run(self, query: str) -> str:
        try:
            if not query:
                return "Error: Proporciona una consulta válida."
                
            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": query, "num": 3})
            headers = {
                'X-API-KEY': SERPER_API_KEY,
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers=headers, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                resultado = f"Búsqueda: '{query}'\n\n"
                if 'organic' in data and data['organic']:
                    resultado += "RESULTADOS:\n"
                    for i, item in enumerate(data['organic'][:2], 1):
                        title = item.get('title', 'Sin título')
                        link = item.get('link', 'Sin enlace')
                        resultado += f"{i}. {title} - {link}\n"
                else:
                    resultado += "Sin resultados."
                return resultado
            else:
                return f"Error {response.status_code}"
        except Exception as e:
            return f"Error de búsqueda: {str(e)}"