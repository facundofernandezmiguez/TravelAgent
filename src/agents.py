from crewai import Agent, Task, Crew , Process
from config import llm
from tools import BuscadorWeb, BuscadorVuelos
from datetime import datetime

# Definir agentes 
agente_actividades = Agent(
    role="Buscador de Actividades",
    goal="Encontrar actividades turísticas basadas en las preferencias del usuario",
    backstory=(
        "Sos un experto en descubrir planes geniales para viajeros. Cuando busques actividades, **enfocate en identificar las principales atracciones de cada ciudad.** " 
        "No necesitas buscar horarios detallados, precios o información de transporte en esta etapa. "         
        "No hagas sugerencias vagas, como 'Cena en un restaurante típico'. Si vas a recomendar un lugar para comer, o una actividad, debes explicitar el nombre del lugar."
    ),
    tools=[BuscadorWeb()],
    llm=llm,
    verbose=True,
    allow_delegation=True,
    max_iter=3
)

agente_vuelos = Agent(
    role="Buscador de Transportes",
    goal="Encontrar vuelos para los traslados especificados. **Encontrar una opción para cada traslado (ida y vuelta y entre ciudades).** Si es un vuelo, debes explicitar el nombre del vuelo.", 
    backstory=(
        "Sos un experto en encontrar vuelos de manera **rápida y eficiente**. **Los vuelos/trenes deben ser reales, no debes inventar informacion.** " 
        "Tu objetivo es encontrar **UNA SOLA OPCIÓN CONVENIENTE** para cada traslado necesario (ida y vuelta y entre ciudades). " 
        "IMPORTANTE: busca opciones directas. Si no hay, busca opciones con la menor cantidad de escalas posibles." 
        "Una vez que encuentres **UNA OPCIÓN RAZONABLE** para cada vuelo, **DETENÉ la búsqueda inmediatamente.** " 
        "**NO BUSQUES OPCIONES ADICIONALES, NO COMPARES PRECIOS EXTENSAMENTE, NO BUSQUES HORARIOS DETALLADOS.** " 
        "Simplemente encontrá una opción que parezca adecuada en términos de aerolínea y horario general, y pasá al siguiente traslado." 
        "Recordá, **UNA OPCIÓN POR TRASLADO ES SUFICIENTE.**" 
        "Para búsquedas de vuelos, utiliza códigos IATA de 3 letras para aeropuertos (ej: MAD para Madrid, BCN para Barcelona)."
    ),
    tools=[BuscadorWeb(), BuscadorVuelos()],
    llm=llm,
    verbose=True,
    allow_delegation=True,
    max_iter=3
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
    allow_delegation=True,
    max_iter=3
)

agente_planificacion = Agent(
    role="Planificador de Itinerarios",
    goal="Crear un itinerario de viaje de {dias} días **DETALLADO, ATRACTIVO y en ESPAÑOL ARGENTINO con emojis.** **UTILIZANDO LA INFORMACIÓN PROPORCIONADA POR LOS OTROS AGENTES. NO REDUNDAR EN BÚSQUEDAS INNECESARIAS.**", 
    backstory=(
        "Sos el Manager y Planificador de Viajes principal. Tu función es COORDINAR a los agentes: para buscar actividades recreativas debes delegar al 'Buscador de Actividades', para buscar transportes debes delegar al 'Buscador de Transportes' y para buscar hoteles debes delegar al 'Buscador de Hoteles'. " 
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
    allow_delegation=True
)

# Función para generar el itinerario
def generar_itinerario(origen, destinos, fecha_inicio, fecha_fin, preferencias):
    #Guardar el numero de dias de viaje para el itinerario
    dias = str((fecha_fin - fecha_inicio).days + 1)

    task_actividades = Task(
        description=f"""Basado en las preferencias del usuario: '{preferencias}', **busca las actividades turísticas MÁS POPULARES y RECONOCIDAS** en las siguientes ciudades: {destinos}.
    **Genera una lista CONCISA de las actividades MÁS POPULARES por ciudad.**
    **Debes tener en cuenta que el usuario está buscando actividades para un viaje de {dias} días, debes buscar una cantidad de actividades acorde a la cantidad de dias.**
    **NO incluyas detalles como horarios, precios, requisitos o información de transporte.**
    Simplemente enumera las atracciones principales que un turista debería considerar visitar en cada ciudad.""",
        agent=agente_actividades,
        expected_output=""
    )

    task_vuelos = Task(
    description=f"""Encuentra una opcion de vuelo de ida desde {origen} a {destinos[0]}, y de vuelta desde {destinos[-1]} a {origen} (si no está disponible por alguna razón, entonces encuentra una forma de volver a {destinos[0]} y de ahí a {origen}) para el {fecha_inicio} y {fecha_fin}. También encuentra una opcion de transporte de viaje entre ciudades de destino según itinerario (si hay más de uno): {destinos}.
    Si no encuentras un vuelo directo, debes buscar un vuelo que te permita llegar al destino, aunque contenga escalas.
    Usa la herramienta buscar_vuelos con códigos IATA de aeropuertos (3 letras, ej: MAD, BCN, JFK) y formato de fecha YYYY-MM-DD.
    Ejemplo de uso: 'MAD,JFK,2023-12-24' para buscar vuelos de Madrid a Nueva York el 24 de diciembre de 2023.
    Encuentra el horario del vuelo, pasaje, aerolinea y precio. **Los vuelos deben ser reales, no debes inventar informacion.** 
    Presenta la información de manera concisa: aerolínea, número de vuelo, horarios aproximados de salida y llegada, y precio.
    IMPORTANTE: busca opciones directas. Si no hay, busca opciones con la menor cantidad de escalas posibles.""",
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
        description=f"""Tu tarea principal es planificar un itinerario de viaje DETALLADO DÍA POR DÍA de {dias} días, escrito en ESPAÑOL ARGENTINO con EMOJIS.

        **INSTRUCCIONES DE DELEGACIÓN:**

        1. **Primero, DELEGA la tarea de encontrar vuelos** (ida y vuelta y entre ciudades) al agente 'Buscador de Transportes'. Asegúrate de proporcionarle toda la información necesaria: origen, destinos, fechas de viaje.
        2. **Luego, DELEGA la tarea de buscar actividades turísticas** en las ciudades de destino al agente 'Buscador de Actividades'.  Indícale las ciudades y las preferencias del usuario para las actividades (ej: '{preferencias}').
        3. **Finalmente, DELEGA la tarea de encontrar opciones de hoteles** (lujosos y económicos) en cada ciudad de destino al agente 'Buscador de Hoteles'.

        **Una vez que hayas recibido la información de vuelos, actividades y hoteles de los agentes delegados, procede a CREAR el itinerario detallado.**
        ES FUNDAMENTAL QUE RESPETES EL ITINERARIO DESEADO:
        **Formato de Itinerario Deseado:**
        Itinerario de {dias} Días: [Ciudad 1] y [Ciudad 2]

**Día 1: [Fecha dia 1] - [Ciudad 1]**

Mañana:
Actividad: [Descripción de la actividad] [Emoji].
Transporte: [Horario de transporte, aerolínea, tren, número de vuelo (si está disponible)] [Emoji]
Tarde:
Actividad: [Descripción de la actividad] [Emoji].
Almuerzo: [Sugerencia de almuerzo, si aplica] [Emoji].
Noche:
Actividad: [Descripción de la actividad] [Emoji].
Cena: [Sugerencia de cena, si aplica] [Emoji].

**Día 2: [Fecha dia 2] - [Ciudad 2]**
... (y así sucesivamente para cada día)

**Opciones de Alojamiento 🏨:**

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

**Opciones de Transporte ✈️:**

Desde [Origen] hasta [Ciudad 1]:
Empresa: [Nombre de la aerolínea o tren o colectivo]
Pasaje: [Nº de vuelo o tren (si está disponible)]
Horario: [Horario de salida] - [Horario de llegada]
Precio: [Precio del vuelo]
Enlace: [Enlace al sitio web de la busqueda]

Desde [Ciudad1] hasta [Ciudad 2] [Emoji]:
Empresa: [Nombre de la aerolínea o tren o colectivo]
Pasaje: [Nº de vuelo o tren (si está disponible)]
Horario: [Horario de salida] - [Horario de llegada]
Precio: [Precio del vuelo]
Enlace: [Enlace al sitio web de la busqueda]

Desde [Ciudad N] hasta [Origen] [Emoji]: 
Empresa: [Nombre de la aerolínea o tren o colectivo] 
Pasaje: [Nº de vuelo o tren (si está disponible)]
Horario: [Horario de salida] - [Horario de llegada]
Precio: [Precio del vuelo]
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
