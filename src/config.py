from crewai import LLM
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Obtener claves de API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

# Configurar LLM
llm = LLM(
    model="groq/qwen-qwq-32b",
    temperature=0.7,
    api_key=GROQ_API_KEY
)
