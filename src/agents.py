from crewai import Agent, Task, Crew , Process
from config import llm
from tools import BuscadorWeb
from datetime import datetime

# Definir agentes (tu código está bien en esta parte)
agente_actividades = Agent(
    role="Buscador de Actividades",
    goal="Encontrar actividades turísticas basadas en las preferencias del usuario",
    backstory=(
        "Sos un experto en descubrir planes geniales para viajeros. Cuando busques actividades, **enfocate en identificar las principales atracciones de cada ciudad.** " 
        "No necesitas buscar horarios detallados, precios o información de transporte en esta etapa. " 
        "Simplemente genera una lista de las actividades más populares por ciudad."
    ),
    tools=[BuscadorWeb()],
    llm=llm,
    verbose=True,
    allow_delegation= False
)

agente_vuelos = Agent(
    role="Buscador de Transportes",
    goal="Encontrar vuelos para los traslados especificados. **Encontrar UNA ÚNICA OPCIÓN para cada traslado (ida y vuelta y entre ciudades).** Si es un vuelo, debes explicitar el nombre del vuelo.", 
    backstory=(
        "Sos un experto en encontrar vuelos de manera **rápida y eficiente**. " 
        "Tu objetivo es encontrar **UNA SOLA OPCIÓN CONVENIENTE** para cada traslado necesario (ida y vuelta y entre ciudades). " 
        "**Realizá la MENOR CANTIDAD DE BÚSQUEDAS POSIBLES.** " 
        "Una vez que encuentres **UNA OPCIÓN RAZONABLE** para cada vuelo, **DETENÉ la búsqueda inmediatamente.** " 
        "**NO BUSQUES OPCIONES ADICIONALES, NO COMPARES PRECIOS EXTENSAMENTE, NO BUSQUES HORARIOS DETALLADOS.** " 
        "Simplemente encontrá una opción que parezca adecuada en términos de aerolínea y horario general, y pasá al siguiente traslado." 
        "Recordá, **UNA OPCIÓN POR TRASLADO ES SUFICIENTE.**" 
    ),
    tools=[BuscadorWeb()],
    llm=llm,
    verbose=True,
    allow_delegation= False
)
agente_hoteles = Agent(
    role="Buscador de Hoteles",
    goal="Encontrar hoteles para las ciudades en los destinos especificados. Buscar 2 opciones por ciudad (lujosa y económica)",
    backstory=(
        "Sos un experto en encontrar hoteles. **IMPORTANTE: Realizá SOLO UNA BÚSQUEDA por cada tipo de hotel (lujoso y económico) por ciudad.** "
        "Una vez que encuentres **DOS OPCIONES (una lujosa y una económica) PARA CADA CIUDAD**, DETENÉ la búsqueda inmediatamente. "
        "**NO REALICES BÚSQUEDAS ADICIONALES NI REPITAS BÚSQUEDAS INNECESARIAMENTE.** "
        "Tu objetivo es encontrar rápidamente dos buenas opciones por ciudad, no hacer una búsqueda exhaustiva."
    ),
    tools=[BuscadorWeb()],
    llm=llm,
    verbose=True,
    allow_delegation= False
)

agente_planificacion = Agent(
    role="Planificador de Itinerarios",
    goal="Crear un itinerario de viaje **DETALLADO, ATRACTIVO y en ESPAÑOL ARGENTINO con emojis.** **UTILIZANDO LA INFORMACIÓN PROPORCIONADA POR LOS OTROS AGENTES. NO REDUNDAR EN BÚSQUEDAS INNECESARIAS.**", 
    backstory=(
        "Sos el Manager y Planificador de Viajes principal. Tu función es COORDINAR a los agentes Buscador de Actividades, Buscador de Vuelos y Buscador de Hoteles. " 
        "Recibís la información de ellos y la USÁS para crear un itinerario detallado y atractivo. " 
        "Una vez que recibas informacion de vuelos, hoteles y actividades, presenta los datos de forma ordenada y detiene la busqueda inmediatamente"
        "**NO realizás búsquedas de actividades directamente. Tu foco es PLANIFICAR y PRESENTAR la información en un itinerario genial.**"
        "**Escribí en un ESPAÑOL ARGENTINO natural y amigable. Utiliza emojis** " 
        "**DESARROLLÁ CADA DÍA DEL ITINERARIO CON UN PÁRRAFO DESCRIPTIVO**, mencionando las actividades principales, "
        "dando **SUGERENCIAS CORTAS Y ATRACTIVAS** sobre qué hacer y ver en cada lugar. " 
        "Al final, **presentá las opciones de hoteles de forma clara y concisa**, destacando brevemente las características de cada hotel (lujoso y económico)." 
    ),
    llm=llm,
    verbose=True,
    allow_delegation= True
)

# Función para generar el itinerario
def generar_itinerario(origen, destinos, fecha_inicio, fecha_fin, preferencias):
    #Guardar el numero de dias de viaje para el itinerario
    dias = str((fecha_fin - fecha_inicio).days + 1)

    task_actividades = Task(
        description=f"""Basado en las preferencias del usuario: '{preferencias}', **busca las actividades turísticas MÁS POPULARES y RECONOCIDAS** en las siguientes ciudades: {destinos}.
    **Genera una lista CONCISA de las actividades MÁS POPULARES por ciudad.**
    **NO incluyas detalles como horarios, precios, requisitos o información de transporte.**
    Simplemente enumera las atracciones principales que un turista debería considerar visitar en cada ciudad.""",
        agent=agente_actividades,
        expected_output=""
    )

    task_vuelos = Task(
    description=f"""Encuentra **UNA ÚNICA OPCIÓN** de vuelo de ida y vuelta desde {origen} a uno de los destinos para el {fecha_inicio} y {fecha_fin}. También encuentra una opcion de transporte de viaje entre ciudades de destino según itinerario: {destinos}.
    **BUSCA LA OPCIÓN MÁS RAZONABLE EN TÉRMINOS DE PRECIO Y HORARIO GENERAL, PERO NO NECESITAS HACER UNA BÚSQUEDA EXHAUSTIVA NI COMPARAR DETALLADAMENTE.**
    **Proporciona el enlace a un sitio donde el usuario pueda ver las opciones de vuelos y tren.**
    Presenta la información de manera concisa: aerolínea, número de vuelo (si está disponible), horarios aproximados de salida y llegada, y precio estimado (si lo encuentras fácilmente).""",
    agent=agente_vuelos,
    expected_output="" 
    )

    task_hoteles = Task(
        description=f"""Investiga y encuentra enlaces a listas de hoteles lujosos y económicos en cada una de las ciudades de {destinos}. 
    Proporcioná un enlace para hoteles lujosos y un enlace para hoteles económicos por cada ciudad. 
    **Realizá SOLO UNA BÚSQUEDA por tipo de hotel (lujoso y económico) por ciudad y DETENETE una vez que tengas los enlaces.**
    No es necesario buscar nombres específicos de hoteles, simplemente entrega los enlaces a las listas relevantes.""",
        agent=agente_hoteles,
        expected_output=""
    )

    task_planificacion_itinerario = Task(
        description=f"""Utilizando la información recopilada sobre actividades, vuelos y hoteles, **crea un itinerario de viaje DETALLADO DÍA POR DÍA de {dias} días, escrito en ESPAÑOL ARGENTINO con EMOJIS.**
        **Para cada día, escribe un PÁRRAFO CORTO Y DESCRIPTIVO** que inspire al viajero, mencionando las actividades principales y dando sugerencias atractivas.
        **NO HAGAS SOLO UNA LISTA, SINO UN TEXTO ENGANCHADOR.**
        **Formato de Itinerario Deseado:**
        Itinerario de {dias} Días: [Ciudad 1] y [Ciudad 2]

Día 1: [Fecha dia 1] - [Ciudad 1]

Mañana:
Actividad: [Descripción de la actividad] [Emoji].
Transporte: [Horario de transporte, aerolínea, tren, número de vuelo (si está disponible)] [Emoji]
Tarde:
Actividad: [Descripción de la actividad] [Emoji].
Almuerzo: [Sugerencia de almuerzo, si aplica] [Emoji].
Noche:
Actividad: [Descripción de la actividad] [Emoji].
Cena: [Sugerencia de cena, si aplica] [Emoji].

Día 2: [Fecha dia 2] - [Ciudad 2]
... (y así sucesivamente para cada día)

Opciones de Alojamiento [Emoji]:

[Ciudad 1]:
[Tipo de Hotel - Lujo/Económico]:
[Nombre del Hotel] ⭐⭐⭐⭐⭐
Dirección: [Dirección]
Enlace: [Enlace]

[Ciudad 2]:
[Tipo de Hotel - Lujo/Económico]:
[Nombre del Hotel] ⭐⭐⭐
Dirección: [Dirección]
Enlace: [Enlace]

Opciones de Transporte [Emoji]:
Desde [Origen] hasta [Ciudad 1]:
Empresa: [Nombre de la aerolínea o tren o colectivo]
Pasaje: [Nº de vuelo o tren (si está disponible)]
Enlace: [Enlace al sitio web de la busqueda]

Desde [Ciudad1] hasta [Ciudad 2] [Emoji]:
Empresa: [Nombre de la aerolínea o tren o colectivo]
Pasaje: [Nº de vuelo o tren (si está disponible)]
Enlace: [Enlace al sitio web de la busqueda]

Desde [Ciudad N] hasta [Origen] [Emoji]: 
Empresa: [Nombre de la aerolínea o tren o colectivo] 
Pasaje: [Nº de vuelo o tren (si está disponible)]
Enlace: [Enlace al sitio web de la busqueda]
"""
,
    agent=agente_planificacion,
    expected_output=""
    )


    crew = Crew(
        agents=[agente_actividades, agente_vuelos, agente_hoteles],
        tasks=[task_actividades, task_vuelos, task_hoteles, task_planificacion_itinerario], 
        manager_agent=agente_planificacion,
        process=Process.hierarchical,
        verbose=True
    )

    # Iniciar el proceso con los inputs proporcionados
    resultado = crew.kickoff(inputs={
        "origen": origen,
        "destinos": destinos,
        "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
        "preferencias": preferencias
    })

    return resultado