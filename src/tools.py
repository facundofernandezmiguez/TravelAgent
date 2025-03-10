import json
import requests
from crewai.tools import BaseTool
from src.config import SERPER_API_KEY , FIRECRAWL_API_KEY



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

 # Se asume que FirecrawlSearchTool usa esta API key internamente
'''
@tool
class BuscarVuelosSkyscanner(BaseTool):
    name: str = "buscar_vuelos_skyscanner"
    description: str = "Busca información sobre vuelos de ida y vuelta en skyscanner.net utilizando FirecrawlSearchTool."
    
    def _run(self, origen: str, destino: str, fecha_ida: str, fecha_vuelta: str) -> str:
        """
        Parámetros:
            origen (str): Ciudad o código IATA de origen.
            destino (str): Ciudad o código IATA de destino.
            fecha_ida (str): Fecha de salida en formato 'YYYY-MM-DD'.
            fecha_vuelta (str): Fecha de regreso en formato 'YYYY-MM-DD'.
        """
        try:
            if not (origen and destino and fecha_ida and fecha_vuelta):
                return "Error: Proporcione origen, destino, fecha de ida y fecha de vuelta."
            
            # Construir la consulta especificando el sitio de Skyscanner para afinar la búsqueda
            query = f"site:skyscanner.net vuelos de {origen} a {destino} ida {fecha_ida} vuelta {fecha_vuelta}"
            
            # Instanciar la herramienta FirecrawlSearchTool, la cual utiliza internamente la API key guardada
            firecrawl_tool = FirecrawlSearchTool()
            search_results = firecrawl_tool.search(query)
            
            if search_results:
                resultado = f"Resultados para: {query}\n\n"
                # Se asume que search_results es una lista de diccionarios con al menos 'title' y 'link'
                if isinstance(search_results, list):
                    for i, item in enumerate(search_results, 1):
                        title = item.get("title", "Sin título")
                        link = item.get("link", "Sin enlace")
                        resultado += f"{i}. {title} - {link}\n"
                else:
                    resultado += str(search_results)
                return resultado
            else:
                return "No se encontraron resultados para la búsqueda de vuelos."
        except Exception as e:
            return f"Error al buscar vuelos: {str(e)}"
'''