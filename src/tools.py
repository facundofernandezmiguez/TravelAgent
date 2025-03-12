import json
import requests
import time
from crewai.tools import BaseTool
from src.config import SERPER_API_KEY, AMADEUS_API_KEY, AMADEUS_API_SECRET
from amadeus import Client, ResponseError
from typing import Optional

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

class BuscadorVuelos(BaseTool):
    name: str = "buscar_vuelos"
    description: str = "Busca vuelos reales utilizando la API de Amadeus. Usa el formato: 'ORIGEN,DESTINO,FECHA_SALIDA' (ej: 'MAD,JFK,2023-12-24'). IMPORTANTE: Usa códigos IATA para aeropuertos (3 letras)."
    
    # No inicializar el cliente en __init__ para evitar problemas con pydantic
    def _get_amadeus_client(self):
        return Client(
            client_id=AMADEUS_API_KEY,
            client_secret=AMADEUS_API_SECRET
        )
    
    def _run(self, consulta: str) -> str:
        try:
            # Parsear la consulta
            if not consulta or "," not in consulta:
                return "Error: La consulta debe tener formato 'ORIGEN,DESTINO,FECHA_SALIDA' (ej: 'MAD,JFK,2023-12-24')"
            
            partes = consulta.split(',')
            if len(partes) < 3:
                return "Error: La consulta debe incluir origen, destino y fecha separados por comas."
            
            origen = partes[0].strip().upper()
            destino = partes[1].strip().upper()
            fecha = partes[2].strip()
            
            # Validar el formato de los códigos IATA
            if len(origen) != 3 or len(destino) != 3:
                return "Error: Los códigos de aeropuerto deben ser códigos IATA de 3 letras (ej: MAD, JFK, BCN)"
            
            # Validar formato de fecha
            try:
                # Verificar formato yyyy-mm-dd
                año, mes, dia = fecha.split('-')
                if len(año) != 4 or len(mes) != 2 or len(dia) != 2:
                    raise ValueError("Formato de fecha incorrecto")
            except:
                return "Error: La fecha debe estar en formato YYYY-MM-DD (ej: 2023-12-24)"
            
            # Número de adultos (opcional, por defecto 1)
            adultos = 1
            if len(partes) > 3 and partes[3].strip().isdigit():
                adultos = int(partes[3].strip())
            
            # Inicializar el cliente de Amadeus
            amadeus = self._get_amadeus_client()
            
            # Búsqueda con reintentos
            max_reintentos = 3
            for intento in range(max_reintentos):
                try:
                    response = amadeus.shopping.flight_offers_search.get(
                        originLocationCode=origen,
                        destinationLocationCode=destino,
                        departureDate=fecha,
                        adults=adultos,
                        max=5  # Limitar a 5 resultados para ahorrar tokens
                    )
                    
                    if not response.data:
                        return f"❌ No se encontraron vuelos para la ruta {origen} → {destino} en la fecha {fecha}."
                    
                    # Formatear resultados
                    resultado = f"✈️ Vuelos de {origen} a {destino} para el {fecha}:\n\n"
                    
                    # Limitar a 3 opciones para optimizar tokens
                    for i, oferta in enumerate(response.data[:3], 1):
                        precio = oferta['price']['total']
                        moneda = oferta['price']['currency']
                        itinerario = oferta['itineraries'][0]
                        segmentos = itinerario['segments']
                        duracion = itinerario.get('duration', 'No disponible')
                        
                        # Info del primer segmento (salida)
                        primer_segmento = segmentos[0]
                        aerolinea_codigo = primer_segmento['carrierCode']
                        numero_vuelo = primer_segmento['number']
                        hora_salida = primer_segmento['departure']['at'].replace('T', ' ').split('+')[0]
                        aeropuerto_salida = primer_segmento['departure']['iataCode']
                        
                        # Info del último segmento (llegada final)
                        ultimo_segmento = segmentos[-1]
                        hora_llegada = ultimo_segmento['arrival']['at'].replace('T', ' ').split('+')[0]
                        aeropuerto_llegada = ultimo_segmento['arrival']['iataCode']
                        
                        # Número de escalas
                        escalas = len(segmentos) - 1
                        texto_escalas = "Directo" if escalas == 0 else f"{escalas} escala{'s' if escalas > 1 else ''}"
                        
                        # Formato de salida
                        resultado += f"OPCIÓN {i}:\n"
                        resultado += f"🛫 Aerolínea: {aerolinea_codigo}\n"
                        resultado += f"🔢 Vuelo: {aerolinea_codigo}{numero_vuelo}\n"
                        resultado += f"🕒 Salida: {hora_salida} ({aeropuerto_salida})\n"
                        resultado += f"🕞 Llegada: {hora_llegada} ({aeropuerto_llegada})\n"
                        resultado += f"⏱️ Duración: {duracion}\n"
                        resultado += f"🛑 Escalas: {texto_escalas}\n"
                        resultado += f"💰 Precio: {precio} {moneda}\n\n"
                    
                    return resultado
                
                except ResponseError as error:
                    if intento < max_reintentos - 1:
                        # Si es un error de límite de tasa, esperar y reintentar
                        if "429" in str(error) or "rate" in str(error).lower():
                            tiempo_espera = (intento + 1) * 2  # Backoff exponencial
                            time.sleep(tiempo_espera)
                            continue
                    return f"Error al buscar vuelos: {str(error)}"
                except Exception as e:
                    if intento < max_reintentos - 1:
                        tiempo_espera = (intento + 1) * 2
                        time.sleep(tiempo_espera)
                        continue
                    return f"Error inesperado: {str(e)}"
            
            return "Error: Se alcanzó el número máximo de reintentos sin éxito."
            
        except Exception as e:
            return f"Error en la búsqueda de vuelos: {str(e)}"
