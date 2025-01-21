# AI Travel Agent 🌎✈️

Un asistente de viajes inteligente implementado con Streamlit, LangChain y Groq. Este agente ayuda a los usuarios a planificar sus viajes proporcionando recomendaciones en tiempo real y creando itinerarios detallados.

## Características

- Conversación interactiva en español con comprensión del lenguaje natural 🗣️
- Integración de búsqueda web en tiempo real para información actualizada 🔍
- Recopilación estructurada de preferencias de viaje 📝
- Planificación completa de viajes con itinerarios detallados 📅
- Interfaz de usuario amigable con Streamlit 💻

## Configuración

1. Instala las dependencias requeridas:
```bash
pip install -r requirements.txt
```

2. Crea un archivo `.env` con las siguientes variables:
```
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=llama-3.3-70b-versatile
```

## Uso

Ejecuta la aplicación Streamlit:
```bash
streamlit run app.py
```

El agente iniciará una interfaz web interactiva donde podrás:
- Mantener conversaciones naturales sobre tus planes de viaje
- Obtener información en tiempo real sobre destinos
- Recibir recomendaciones personalizadas
- Obtener itinerarios detallados basados en tus preferencias

## Estructura del Proyecto

- `app.py`: Aplicación principal de Streamlit
- `travel_agent.py`: Implementación del agente de viajes
- `prompts.yaml`: Plantillas de prompts para el agente
- `requirements.txt`: Dependencias del proyecto
- `.env`: Variables de entorno y configuración

## Tecnologías Utilizadas

- Streamlit: Para la interfaz de usuario web
- LangChain: Para el manejo de la conversación y el agente
- Groq: Modelo de lenguaje para procesamiento de texto
- DuckDuckGo Search: Para búsquedas web en tiempo real
