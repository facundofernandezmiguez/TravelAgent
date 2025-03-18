from crewai import Agent, Task, Crew , Process
from config import llm
from tools import BuscadorWeb, BuscadorVuelos
from datetime import datetime

# Función para generar el itinerario
def generar_itinerario(origen, destinos, fecha_inicio, fecha_fin, preferencias, dias):
    
    # Definir agentes 
    agente_actividades = Agent(
        role="Buscador de Actividades",
        goal="Encontrar actividades turísticas basadas en las preferencias del usuario.",
        backstory=(f"""Basado en las preferencias del usuario: '{preferencias}', **busca las actividades turísticas MÁS POPULARES y RECONOCIDAS** en las siguientes ciudades: {destinos} para un viaje de {dias} días.
        **Genera una lista CONCISA de las actividades MÁS POPULARES por ciudad.**
        **Debes tener en cuenta que el usuario está buscando actividades para un viaje de {dias} días, debes buscar una cantidad de actividades acorde a la cantidad de dias.**
        **NO incluyas detalles como horarios, precios, requisitos o información de transporte.**
        Simplemente enumera las atracciones principales que un turista debería considerar visitar en cada ciudad."""),
    tools=[BuscadorWeb()],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3
    )

    agente_vuelos = Agent(
        role="Buscador de Transportes",
        goal="Encontrar vuelos para los traslados especificados. **Encontrar una opción para cada traslado (ida y vuelta y entre ciudades).** Si es un vuelo, debes explicitar el nombre del vuelo.", 
        backstory=(f"""Encuentra una opcion de vuelo de ida desde {origen} a {destinos[0]}, y de vuelta desde {destinos[-1]} a {origen} (si no está disponible por alguna razón, entonces encuentra una forma de volver a {destinos[0]} y de ahí a {origen}) para el {fecha_inicio.strftime('%Y-%m-%d')} y {fecha_fin.strftime('%Y-%m-%d')}.
        También encuentra una opcion de transporte de viaje entre ciudades de destino según itinerario (si hay más de uno): {destinos}.
        Si no encuentras un vuelo directo, debes buscar un vuelo que te permita llegar al destino, aunque contenga escalas.
    Usa la herramienta buscar_vuelos con códigos IATA de 3 letras para aeropuertos (3 letras, ej: MAD, BCN, JFK) y formato de fecha YYYY-MM-DD.
    IMPORTANTE: Para la fecha de ida, usa EXACTAMENTE: {fecha_inicio.strftime('%Y-%m-%d')}
    IMPORTANTE: Para la fecha de vuelta, usa EXACTAMENTE: {fecha_fin.strftime('%Y-%m-%d')}
    Ejemplo de uso: 'MAD,JFK,2025-04-24' para buscar vuelos de Madrid a Nueva York el 24 de abril de 2025.
    Encuentra el horario del vuelo, pasaje, aerolinea y precio. **Los vuelos deben ser reales, no debes inventar informacion.** 
    Presenta la información de manera concisa: aerolínea, número de vuelo, horarios aproximados de salida y llegada, y precio.
    IMPORTANTE: busca opciones directas. Si no hay, busca opciones con la menor cantidad de escalas posibles."""
    ),
    tools=[BuscadorWeb(), BuscadorVuelos()],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3
    )

    agente_hoteles = Agent(
    role="Buscador de Hoteles",
    goal="Encontrar hoteles para las ciudades en los destinos especificados. Buscar 2 opciones por ciudad (lujosa y económica)",
    backstory=(f"""Investiga y encuentra enlaces a listas de hoteles lujosos y económicos en cada una de las ciudades de {destinos}. 
    Proporcioná un enlace para hoteles lujosos y un enlace para hoteles económicos por cada ciudad. 
    **Realizá SOLO UNA BÚSQUEDA por tipo de hotel (lujoso y económico) por ciudad y DETENETE una vez que tengas los enlaces.**
    No es necesario buscar nombres específicos de hoteles, simplemente entrega los enlaces a las listas relevantes."""
    ),
    tools=[BuscadorWeb()],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3
    )

    agente_planificacion = Agent(
    role="Planificador de Itinerarios",
    goal=f"Crear un itinerario de viaje de {dias} días **DETALLADO, ATRACTIVO y en ESPAÑOL ARGENTINO con emojis.** **UTILIZANDO LA INFORMACIÓN PROPORCIONADA POR LOS OTROS AGENTES. NO REDUNDAR EN BÚSQUEDAS INNECESARIAS.**", 
    backstory=(
        "Sos el Manager y Planificador de Viajes principal. Tu función es COORDINAR a los agentes: para buscar actividades recreativas debes delegar al 'Buscador de Actividades', para buscar transportes debes delegar al 'Buscador de Transportes' y para buscar hoteles debes delegar al 'Buscador de Hoteles'. " 
        "Recibís la información de ellos y la USÁS para crear un itinerario detallado y atractivo. " 
        "Una vez que recibas informacion de vuelos, hoteles y actividades, presenta los datos de forma ordenada y DETENÉ LA BÚSQUEDA INMEDIATAMENTE. NO REALICES BÚSQUEDAS ADICIONALES BAJO NINGUNA CIRCUNSTANCIA."
        "**NO realizás búsquedas de actividades directamente. Tu foco es PLANIFICAR y PRESENTAR la información en un itinerario genial.**"
        f"Es fundamental que respetes la cantidad de {dias} días del viaje. Es FUNDAMENTAL que cada día tenga su actividad de mañana,tarde y noche."
        "**MANEJO PRECISO DE LOS DÍAS DE VIAJE:** Tenés que tener especial cuidado con los horarios de vuelo. Si un vuelo sale el día 1 a la noche y llega el día 3 por la mañana, NO programes actividades en destino durante los días 1 y 2, ya que el viajero está en tránsito. Solo programa actividades DESPUÉS de que el viajero haya llegado físicamente al destino."
        "**Escribí en un ESPAÑOL ARGENTINO natural y amigable. Utiliza emojis** " 
        "**DESARROLLÁ CADA DÍA DEL ITINERARIO CON UN PÁRRAFO DESCRIPTIVO**, mencionando las actividades principales, "
        "dando **SUGERENCIAS CORTAS Y ATRACTIVAS** sobre qué hacer y ver en cada lugar. " 
        "Al final, **presentá las opciones de hoteles de forma clara y concisa**, destacando brevemente las características de cada hotel (lujoso y económico)." 
    ),
    llm=llm,
    verbose=True,
    allow_delegation=True,
    max_iter=3
    )


    task_planificacion_itinerario = Task(
        description=f"""Tu tarea principal es planificar un itinerario de viaje DETALLADO DÍA POR DÍA de {dias} días, partiendo desde {origen} y yendo a las ciudades {destinos}. Debe estar escrito en ESPAÑOL ARGENTINO con EMOJIS. NO PUEDE FALTAR NINGUN DIA.

        **INSTRUCCIONES DE DELEGACIÓN:**

        IMPORTANTE: Solo el agente planificador (Manager) debe ejecutar esta tarea. 
        Como Manager, debes DELEGAR las siguientes tareas:
        
        1. DELEGA la tarea de buscar vuelos al agente 'Buscador de Transportes'.
        2. DELEGA la tarea de buscar actividades al agente 'Buscador de Actividades'.
        3. DELEGA la tarea de buscar hoteles al agente 'Buscador de Hoteles'.
        
        **CREACION DE ITINERARIO**
        Una vez que hayas recibido la información de todos los agentes, crea el itinerario detallado.
        
        **IMPORTANTE: DESPUÉS DE RECIBIR LA INFORMACIÓN DE TODOS LOS AGENTES, NO REALICES BÚSQUEDAS ADICIONALES.**
        
        **ATENCIÓN A LAS FECHAS DE VIAJE:**
        - NO PROGRAMES ACTIVIDADES DURANTE LOS DÍAS DE VIAJE.
        - Las actividades en destino SOLO DEBEN EMPEZAR DESPUÉS de que el viajero haya llegado físicamente.
        - Si un vuelo llega, por ejemplo, el día {fecha_inicio.strftime('%d/%m')} por la mañana, programa actividades solo a partir de la tarde.
        
        Tips: 
            -No olvides que todos los dias deben estar detallados en mañana, tarde y noche.
            -Debes tener en cuenta que el transporte consume tiempo.
            -Recuerda incluir aerolínea, horarios y precios de los vuelos.
        
        ES FUNDAMENTAL QUE RESPETES EL ITINERARIO DESEADO:
        **Formato de Itinerario Deseado:**
        Itinerario de {dias} Días: [Ciudad 1] y [Ciudad 2]

**Día 1: [{fecha_inicio.strftime('%d/%m/%Y')}] - [Ciudad X]**
# Si este día es un día de viaje (vuelo de ida), indicar claramente que es un día de viaje y NO programar actividades turísticas hasta la llegada.

-Mañana:
Actividad: [Descripción de la actividad] [Emoji].
Transporte: [Horario de transporte, aerolínea, tren, número de vuelo (si está disponible)] [Emoji]
-Tarde:
Actividad: [Descripción de la actividad] [Emoji].
Almuerzo: [Sugerencia de almuerzo, si aplica] [Emoji].
-Noche:
Actividad: [Descripción de la actividad] [Emoji].
Cena: [Sugerencia de cena, si aplica] [Emoji].

[CONTINÚA PARA CADA DÍA...]

**Opciones de Alojamiento 🏨:**

[Ciudad 1]:
[Tipo de Hotel - Lujo/Económico]:
[Nombre del Hotel] ⭐⭐⭐⭐⭐
Dirección: [Dirección]
Enlace: [Enlace]

**Opciones de Transporte ✈️:**

**IDA ({fecha_inicio.strftime('%d/%m')}):**
✈️ **Vuelo [Nombre del vuelo] - [Nombre de la aerolinea]:**
- **Salida:** [Hora de salida] ({origen}) ➔ **Llegada:** [Hora de llegada] ([Ciudad 2])
- **Precio:** **$[Precio del vuelo]**

**Entre ciudades de destino:** 
[emoji segun sea transporte de avion, tren, etc]
- **Salida:** [Hora de salida] ([Ciudad 1]) ➔ **Llegada:** [Hora de llegada] ([Ciudad 2])
- **Precio:** **$[Precio del vuelo]**

**VUELTA ({fecha_fin.strftime('%d/%m')}):**
✈️ **Vuelo [Nombre del vuelo] - [Nombre de la aerolinea]:**
- **Salida:** [Hora de salida] ([Ciudad 2]) ➔ **Llegada:** [Hora de llegada] ({origen})
- **Precio:** **$[Precio del vuelo] **
""",
        agent=agente_planificacion,
        expected_output=""
    )


    crew = Crew(
        agents=[agente_actividades, agente_vuelos, agente_hoteles],
        tasks=[task_planificacion_itinerario],
        manager_agent=agente_planificacion,
        process=Process.sequential,
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
