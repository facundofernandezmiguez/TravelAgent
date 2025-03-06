import os
from dotenv import load_dotenv
from crewai.agent import LLM

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener claves API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Verificar que la clave API esté cargada
if not GROQ_API_KEY:
    raise ValueError("Error: GROQ_API_KEY no está configurada en el archivo .env")

# Configurar el LLM
llm = LLM(
    model="gemini/gemini-2.0-flash-lite-001",
    temperature=0.7 ,
    api_key=GEMINI_API_KEY
)