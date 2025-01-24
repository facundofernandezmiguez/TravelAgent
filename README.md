# AI Travel Agent 🌎✈️

Un asistente de viajes inteligente implementado con Streamlit, LangChain, Groq y DuckDuckGo. Este agente ayuda a los usuarios a planificar sus viajes proporcionando recomendaciones en tiempo real y creando itinerarios detallados.

## Características

- Conversación interactiva en español con comprensión del lenguaje natural 🗣️
- Integración de búsqueda web en tiempo real para información actualizada 🔍
- Recopilación eficiente de información esencial de viaje 📝
- Generación automática de itinerarios sin necesidad de confirmación 📅
- Manejo optimizado de múltiples API keys para evitar límites de tasa 🔑
- Interfaz de usuario amigable con Streamlit 💻

## Configuración

1. Instala las dependencias requeridas:
```bash
pip install -r requirements.txt
```

2. Crea un archivo `.env` con tus API keys de Groq:
```
GROQ_API_KEY1=your_first_api_key
GROQ_API_KEY2=your_second_api_key
...
GROQ_API_KEY7=your_seventh_api_key
GROQ_MODEL_NAME=llama-3.3-70b-versatile
```

## Uso

Ejecuta la aplicación Streamlit:
```bash
streamlit run app.py
```

El agente:
- Recopila información esencial (origen, destino, fechas)
- Procede automáticamente con la búsqueda cuando tiene la información necesaria
- Genera un itinerario detallado sin necesidad de confirmaciones adicionales
- Maneja eficientemente múltiples API keys para evitar límites de tasa

## Estructura del Proyecto

- `app.py`: Aplicación principal de Streamlit
- `travel_agent.py`: Implementación del agente de viajes
- `api_key_manager.py`: Gestor de múltiples API keys con manejo de rate limits
- `prompts.yaml`: Plantillas de prompts para el agente
- `requirements.txt`: Dependencias del proyecto
- `.env`: Variables de entorno y configuración

## Tecnologías Utilizadas

- Streamlit: Para la interfaz de usuario web
- LangChain: Para el manejo de la conversación y el agente
- Groq: Modelo de lenguaje para procesamiento de texto
- DuckDuckGo Search: Para búsquedas web en tiempo real
- Python: Lenguaje de programación principal

## Características del Agente

- Recopilación eficiente de información:
  - Solo pregunta por información esencial (origen, destino, fechas)
  - No solicita confirmación para proceder con la búsqueda
  - Usa valores por defecto para preferencias no especificadas

- Manejo de API Keys:
  - Soporte para múltiples API keys de Groq
  - Rotación automática de keys para evitar límites de tasa
  - Manejo inteligente de rate limits y tiempos de espera

- Generación de Itinerarios:
  - Búsqueda automática al tener la información esencial
  - Generación de un único itinerario optimizado
  - Inclusión de actividades y lugares relevantes
