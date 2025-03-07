# Planificador de Viajes Inteligente

Esta aplicación utiliza inteligencia artificial para generar itinerarios de viaje personalizados. Se basa en el framework [CrewAI](https://github.com/crewai-ai/crewai) y utiliza agentes especializados para buscar actividades turísticas, vuelos y hoteles. Además, la aplicación presenta el itinerario generado en **Streamlit**, con descripciones atractivas en español argentino y emojis.

---

## Tabla de Contenidos

- [Características](#características)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Correcciones Realizadas](#correcciones-realizadas)
- [Contribuciones y Licencia](#contribuciones-y-licencia)

---

## Características

- **Agentes especializados:**  
  - **Buscador de Actividades:** Encuentra las principales atracciones turísticas por ciudad.  
  - **Buscador de Transportes:** Localiza una única opción conveniente para vuelos y traslados.  
  - **Buscador de Hoteles:** Investiga dos opciones de alojamiento (lujosa y económica) por ciudad.  
  - **Planificador de Itinerarios:** Coordina la información de los otros agentes para generar un itinerario detallado y atractivo.

- **Interfaz Web con Streamlit:** Permite ingresar ciudad de origen, destinos, fechas y preferencias para generar el itinerario.

- **Búsqueda en la Web:** Utiliza la herramienta `BuscadorWeb` para obtener resultados rápidos sin búsquedas exhaustivas.

---

## Estructura del Proyecto

project/ │ ├── src/ │ ├── agents.py # Definición de agentes, tareas y función para generar el itinerario. │ ├── tools.py # Herramienta para realizar búsquedas en la web (utiliza SERPER_API_KEY). │ ├── config.py # Configuración del LLM y carga de claves API desde el archivo .env. │ └── app.py # Aplicación Streamlit que interactúa con el usuario. │ ├── requirements.txt # Dependencias del proyecto. └── app.py # Archivo de entrada (corregido) para lanzar la aplicación.

yaml
Copiar
Editar

---

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/tu_usuario/planificador-viajes-inteligente.git
   cd planificador-viajes-inteligente
Crear y activar un entorno virtual (opcional, pero recomendado):

python -m venv venv
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
Instalar las dependencias:

pip install -r requirements.txt
Configurar las variables de entorno:

Crea un archivo .env en la raíz del proyecto y agrega las siguientes claves:

dotenv
Copiar
Editar
SERPER_API_KEY=tu_serper_api_key
GEMINI_API_KEY=tu_gemini_api_key
Nota: En el archivo config.py se detecta un error que valida la variable GROQ_API_KEY en lugar de GEMINI_API_KEY. Asegurate de reemplazar la condición:

python
Copiar
Editar
if not GROQ_API_KEY:
    raise ValueError("Error: GROQ_API_KEY no está configurada en el archivo .env")
por:


if not GEMINI_API_KEY:
    raise ValueError("Error: GEMINI_API_KEY no está configurada en el archivo .env")
Uso
Ejecutar la Aplicación con Streamlit
Puedes iniciar la aplicación de dos formas:

Directamente desde el directorio src:

bash
Copiar
Editar
streamlit run src/app.py
Ejecutando el archivo app.py que se encuentra en la raíz (archivo corregido):

bash
Copiar
Editar
python app.py
Este archivo está configurado para invocar Streamlit y correr la aplicación ubicada en src/app.py.

Correcciones Realizadas
1. Corrección en el archivo app.py (raíz)
El contenido original de app.py en la raíz no iniciaba la aplicación. Se ha actualizado el código para que, al ejecutar python app.py, se inicie la aplicación Streamlit correctamente. El nuevo contenido es:

python
Copiar
Editar
import streamlit.cli as stcli
import sys

if __name__ == '__main__':
    sys.argv = ["streamlit", "run", "src/app.py"]
    sys.exit(stcli.main())
2. Corrección en config.py
Se encontró que el archivo validaba la variable GROQ_API_KEY en lugar de GEMINI_API_KEY. Se recomienda modificar esa validación para evitar errores de configuración:

python
Copiar
Editar
if not GEMINI_API_KEY:
    raise ValueError("Error: GEMINI_API_KEY no está configurada en el archivo .env")
Contribuciones y Licencia
Si deseas contribuir a este proyecto, por favor abre un issue o envía un pull request.
Este proyecto está bajo la licencia MIT.

¡Disfrutá planificando tus viajes y descubrí nuevas aventuras con esta herramienta inteligente!

yaml
Copiar
Editar

---