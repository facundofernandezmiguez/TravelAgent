import os
from dotenv import load_dotenv
from crewai.agent import LLM

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener claves API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# Verificar que las claves API necesarias estén cargadas
if not GROQ_API_KEY:
    raise ValueError("Error: GROQ_API_KEY no está configurada en el archivo .env")

if not SERPER_API_KEY:
    raise ValueError("Error: SERPER_API_KEY no está configurada en el archivo .env")    


llm = LLM(
    model="groq/qwen-qwq-32b",
    temperature=0.7,
    api_key=GROQ_API_KEY
)