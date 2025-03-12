# Planificador de viajes con IA 🚀 🌍

Esta aplicación utiliza inteligencia artificial para generar itinerarios de viaje personalizados. Luego de completar un breve formulario con lugar de origen, destinos, fechas y preferencias, la aplicación genera un itinerario detallado y atractivo.

Stack tecnológico utilizado:
- **LLM utilizado:** Qwen QWQ-32B servido a través de [Groq](https://groq.com/)
- **Orquestación de agentes:** Se basa en el framework [CrewAI](https://www.crewai.com/) y utiliza agentes especializados para buscar actividades turísticas, vuelos y hoteles.
- **Tool de búsqueda web:** Google search a través de [SERPER](https://serper.dev/)
- **APIs de vuelos:** [Amadeus](https://developers.amadeus.com/)
- **Frontend:** Streamlit

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


---

## Estructura del Proyecto

```
project/
│ 
├── src/
│   ├── agents.py    # Definición de agentes, tareas y función para generar el itinerario.
│   ├── tools.py     # Herramienta para realizar búsquedas en la web (utiliza SERPER_API_KEY y AMADEUS_API_KEY).
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
   AMADEUS_API_KEY = "tu_api_key_amadeus"
   AMADEUS_API_SECRET="tu_api_key_amadeus_secret"
   ```

   > **Nota:** Ambas claves API son necesarias para que la aplicación funcione correctamente.

2. **Obtener claves API:**
   - **GROQ_API_KEY**: Registrate en [groq.com](https://groq.com)
   - **SERPER_API_KEY**: Registrate en [serper.dev](https://serper.dev)

## Uso

### Ejecutar la Aplicación

Podés iniciar la aplicación de dos formas:

1. **Directamente desde el directorio raíz:**

   ```bash
   python app.py
   ```

2. **O ejecutando directamente con Streamlit:**

   ```bash
   streamlit run src/app.py
   ```

### Planificar un Viaje

1. Ingresá la ciudad de origen y los destinos (separados por comas)
2. Seleccioná las fechas de inicio y regreso
3. Agregá tus preferencias de viaje
4. Hacé clic en "🚀 Generar Itinerario"
5. Esperá mientras los agentes de IA trabajan (esto puede tomar unos minutos)
6. Listo! Revisá tu itinerario personalizado


