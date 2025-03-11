# Planificador de viajes con IA 🚀 🌍

Esta aplicación utiliza inteligencia artificial para generar itinerarios de viaje personalizados. Luego de completar un breve formulario con lugar de origen, destinos, fechas y preferencias, la aplicación genera un itinerario detallado y atractivo.

Stack tecnológico utilizado:
- LLM utilizado: Qwen QWQ-32B servido a través de **Groq**
- Orquestación de agentes: Se basa en el framework [CrewAI](https://www.crewai.com/) y utiliza agentes especializados para buscar actividades turísticas, vuelos y hoteles.
-Tool de búsqueda: **SERPER**
- Frontend: **Streamlit**

## Tabla de Contenidos

- [Características](#características)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Mejoras Implementadas](#mejoras-implementadas)
- [Contribuciones y Licencia](#contribuciones-y-licencia)

## Características

- **Agentes especializados:**  
  - **Buscador de Actividades:** Encuentra las principales atracciones turísticas por ciudad.  
  - **Buscador de Transportes:** Localiza una única opción conveniente para vuelos y traslados.  
  - **Buscador de Hoteles:** Investiga dos opciones de alojamiento (lujosa y económica) por ciudad.  
  - **Planificador de Itinerarios:** Coordina la información de los otros agentes para generar un itinerario detallado y atractivo.

- **Interfaz Web con Streamlit:** Permite ingresar ciudad de origen, destinos, fechas y preferencias para generar el itinerario.

- **Modelo de IA:** La aplicación utiliza el modelo qwen-qwq-32b servido a través de Groq.

- **Manejo de Límites de Tasa:** Implementa estrategias para manejar los límites de tasa (rate limits) en las APIs utilizadas.

---

## Estructura del Proyecto

```
project/
│ 
├── src/
│   ├── agents.py    # Definición de agentes, tareas y función para generar el itinerario.
│   ├── tools.py     # Herramienta para realizar búsquedas en la web (utiliza SERPER_API_KEY).
│   ├── config.py    # Configuración del modelo LLM y carga de claves API desde el archivo .env.
│   ├── app.py       # Aplicación Streamlit que interactúa con el usuario.
│ 
├── requirements.txt # Dependencias del proyecto.
├── app.py           # Archivo de entrada para ejecutar la aplicación.
└── .env             # Archivo para almacenar las claves API (no incluido en el repositorio).
```

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/facundofernandezmiguez/TravelAgent.git
   cd TravelAgent
   ```

2. **Crear y activar un entorno virtual (opcional, pero recomendado):**

   ```bash
   python -m venv venv
   
   # En Windows:
   venv\Scripts\activate
   
   # En macOS/Linux:
   source venv/bin/activate
   ```

3. **Instalar las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuración

1. **Crear archivo `.env` en la raíz del proyecto y agregar las siguientes claves:**

   ```
   GROQ_API_KEY=tu_groq_api_key
   SERPER_API_KEY=tu_serper_api_key
   ```

   > **Nota:** Ambas claves API son necesarias para que la aplicación funcione correctamente.

2. **Obtener claves API:**
   - **GROQ_API_KEY**: Registrate en [groq.com](https://groq.com)
   - **SERPER_API_KEY**: Registrate en [serper.dev](https://serper.dev)

## Uso

### Ejecutar la Aplicación

Puedes iniciar la aplicación de dos formas:

1. **Directamente desde el directorio raíz:**

   ```bash
   python app.py
   ```

2. **O ejecutando directamente con Streamlit:**

   ```bash
   streamlit run src/app.py
   ```

### Planificar un Viaje

1. Ingresa la ciudad de origen y los destinos (separados por comas)
2. Selecciona las fechas de inicio y regreso
3. Elige tus preferencias de viaje
4. Haz clic en "🚀 Generar Itinerario"
5. Espera mientras los agentes de IA trabajan (esto puede tomar varios minutos)
6. Revisa tu itinerario personalizado

## Mejoras Implementadas

- **Solución a los problemas de fecha**: Se ha implementado un sistema de manejo de estado para garantizar que la fecha de regreso siempre sea posterior a la fecha de inicio, incluso después de recargar la página.

- **Optimización para límites de tasa (rate limits)**: La aplicación está configurada para manejar eficientemente las solicitudes a la API de Groq.

- **Simplificación de búsquedas**: Los agentes están configurados para realizar búsquedas eficientes y específicas, evitando consultas redundantes.

## Contribuciones y Licencia

Este proyecto está disponible para uso personal y educativo. Si deseas contribuir, puedes abrir un issue o enviar un pull request.

---

 2023-2025 Facundo Fernandez Miguez. Todos los derechos reservados.
