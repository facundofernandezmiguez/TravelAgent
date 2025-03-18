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
        # Debug: Print API credentials (masked for security)
        api_key = AMADEUS_API_KEY
        api_secret = AMADEUS_API_SECRET
        key_masked = api_key[:4] + "****" if api_key and len(api_key) > 4 else "None"
        secret_masked = "****" + api_secret[-4:] if api_secret and len(api_secret) > 4 else "None"
        
        print(f"Debug - API Key: {key_masked}, API Secret: {secret_masked}")
        
        if not api_key or not api_secret:
            raise ValueError("Error: Amadeus API credentials not found in environment variables")
            
        return Client(
            client_id=api_key,
            client_secret=api_secret
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
            
            # Log the search parameters
            print(f"Debug - Buscando vuelos: Origen={origen}, Destino={destino}, Fecha={fecha}")
            
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
            try:
                amadeus = self._get_amadeus_client()
                print("Debug - Cliente Amadeus inicializado correctamente")
            except Exception as e:
                return f"Error al inicializar el cliente Amadeus: {str(e)}"
            
            # Búsqueda con reintentos
            max_reintentos = 3
            for intento in range(max_reintentos):
                try:
                    print(f"Debug - Intento {intento+1}/{max_reintentos} de búsqueda")
                    
                    # Construir los parámetros de la solicitud
                    params = {
                        "originLocationCode": origen,
                        "destinationLocationCode": destino,
                        "departureDate": fecha,
                        "adults": adultos,
                        "max": 5  # Limitar a 5 resultados para ahorrar tokens
                    }
                    print(f"Debug - Parámetros de búsqueda: {params}")
                    
                    # Realizar la solicitud
                    response = amadeus.shopping.flight_offers_search.get(**params)
                    
                    print(f"Debug - Respuesta recibida, contiene {len(response.data)} resultados")
                    
                    if not response.data:
                        return f"❌ No se encontraron vuelos para la ruta {origen} → {destino} en la fecha {fecha}."
                    
                    # Ordenar resultados por número de escalas (priorizar vuelos directos)
                    vuelos_ordenados = sorted(response.data, 
                                             key=lambda oferta: len(oferta['itineraries'][0]['segments']) - 1)
                    
                    # Formatear resultados
                    resultado = f"✈️ Vuelos de {origen} a {destino} para el {fecha}:\n\n"
                    
                    # Limitar a 3 opciones para optimizar tokens (ahora usando los ordenados por escalas)
                    for i, oferta in enumerate(vuelos_ordenados[:3], 1):
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
                    error_str = str(error)
                    error_code = error.response.status_code if hasattr(error, 'response') else "Unknown"
                    error_body = error.response.body if hasattr(error, 'response') else "No details"
                    
                    print(f"Debug - Amadeus API Error: Code={error_code}, Body={error_body}")
                    
                    if intento < max_reintentos - 1:
                        # Si es un error de límite de tasa, esperar y reintentar
                        if "429" in error_str or "rate" in error_str.lower():
                            tiempo_espera = (intento + 1) * 2  # Backoff exponencial
                            print(f"Debug - Rate limit detectado, esperando {tiempo_espera} segundos")
                            time.sleep(tiempo_espera)
                            continue
                    
                    return f"Error al buscar vuelos: [{error_code}] {error_body}"
                except Exception as e:
                    print(f"Debug - Error inesperado: {str(e)}")
                    if intento < max_reintentos - 1:
                        tiempo_espera = (intento + 1) * 2
                        time.sleep(tiempo_espera)
                        continue
                    
                    return f"Error inesperado: {str(e)}"
            
            return "Error: Se alcanzó el número máximo de reintentos sin éxito."
            
        except Exception as e:
            print(f"Debug - Error general en BuscadorVuelos: {str(e)}")
            return f"Error en la búsqueda de vuelos: {str(e)}"
