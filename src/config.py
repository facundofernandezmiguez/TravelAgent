import os
from dotenv import load_dotenv
from crewai.agent import LLM

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener claves API
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Verificar que la clave API esté cargada
if not GEMINI_API_KEY:
    raise ValueError("Error: GEMINI_API_KEY no está configurada en el archivo .env")

if not SERPER_API_KEY:
    raise ValueError("Error: SERPER_API_KEY no está configurada en el archivo .env")    

if not FIRECRAWL_API_KEY:
    raise ValueError("Error: FIRECRAWL_API_KEY no está configurada en el archivo .env")

'''
# Configurar el LLM
llm = LLM(
    model="gemini/gemini-2.0-flash-lite-001",
    temperature=0.7 ,
    api_key=GEMINI_API_KEY
)
'''
llm = LLM(
    model="groq/qwen-qwq-32b",
    temperature=0.7 ,
    api_key=GROQ_API_KEY
)