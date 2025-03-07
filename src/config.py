import os
from dotenv import load_dotenv
from crewai.agent import LLM

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener claves API
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Verificar que la clave API esté cargada
if not GEMINI_API_KEY:
    raise ValueError("Error: GEMINI_API_KEY no está configurada en el archivo .env")

if not SERPER_API_KEY:
    raise ValueError("Error: SERPER_API_KEY no está configurada en el archivo .env")


# Configurar el LLM
llm = LLM(
    model="gemini/gemini-2.0-flash-lite-001",
    temperature=0.7 ,
    api_key=GEMINI_API_KEY
)