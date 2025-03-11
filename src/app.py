import streamlit as st
from datetime import datetime, timedelta
from agents import generar_itinerario 

# Título de la aplicación
st.title("🌍 Planificador de Viajes Inteligente")
st.markdown("""
Esta aplicación te ayuda a planificar tu próximo viaje utilizando inteligencia artificial.
Ingresa tus preferencias y generaremos un itinerario personalizado.
""")

# Fecha actual y fecha de inicio por defecto
fecha_actual = datetime.now().date()
fecha_inicio_default = fecha_actual + timedelta(days=30)
fecha_fin_default = fecha_inicio_default + timedelta(days=7)  # Por defecto, una semana después

# Inicialización de estado de sesión para mantener las fechas entre recargas
if 'fecha_inicio' not in st.session_state:
    st.session_state.fecha_inicio = fecha_inicio_default
if 'fecha_fin' not in st.session_state:
    st.session_state.fecha_fin = fecha_fin_default

with st.form(key="form_planificacion"):
    col1, col2 = st.columns(2)
    with col1:
        # Sin valor por defecto para evitar hardcodeo
        origen = st.text_input("📍 Ciudad de origen")
        destinos_input = st.text_input("🏙️ Ciudades de destino")
        destinos = [d.strip() for d in destinos_input.split(",") if d.strip()]
        fecha_inicio = st.date_input(
            "🗓️ Fecha de inicio", 
            value=st.session_state.fecha_inicio, 
            min_value=fecha_actual,
            key="fecha_inicio_input"
        )
    with col2:
        # Usamos la fecha_fin del estado de sesión como valor predeterminado
        fecha_fin = st.date_input(
            "🗓️ Fecha de regreso", 
            value=st.session_state.fecha_fin, 
            min_value=fecha_actual,  # Será validado después
            key="fecha_fin_input"
        )
        preferencias = st.multiselect("🌟 Preferencias de viaje", 
                                      ["Cultura", "Gastronomía", "Relax", "Naturaleza", "Historia", "Arte", "Compras", "Vida nocturna"],
                                      default=[])
    submit_button = st.form_submit_button(label="🚀 Generar Itinerario")

# Actualizamos los valores en el estado de sesión después de enviar el formulario
if submit_button:
    st.session_state.fecha_inicio = fecha_inicio
    # Aseguramos que la fecha de fin sea al menos un día después de la fecha de inicio
    if fecha_fin <= fecha_inicio:
        fecha_fin = fecha_inicio + timedelta(days=1)
    st.session_state.fecha_fin = fecha_fin

# Procesar el formulario al enviarlo
if submit_button:
    # Validaciones: se requiere que se ingrese la ciudad de origen, al menos un destino,
    # que la fecha de regreso sea posterior a la de inicio y que se seleccionen preferencias.
    if not origen:
        st.error("❌ Por favor, ingresa la ciudad de origen.")
    elif not destinos:
        st.error("❌ Por favor, ingresa al menos un destino.")
    elif fecha_fin <= fecha_inicio:
        st.error("❌ Debes seleccionar una fecha de regreso posterior a la fecha de inicio.")
        # Corregimos automáticamente la fecha
        fecha_fin = fecha_inicio + timedelta(days=1)
        st.session_state.fecha_fin = fecha_fin
    elif not preferencias:
        st.error("❌ Por favor, selecciona al menos una preferencia de viaje.")
    else:
        with st.spinner("Generando tu itinerario... Esto puede tardar algunos minutos ⏳"):
            try:
                itinerario = generar_itinerario(origen, destinos, fecha_inicio, fecha_fin, preferencias)
                
                st.success("✅ ¡Itinerario generado exitosamente!")
                st.markdown("### Tu itinerario personalizado:")
                st.markdown(itinerario)
            except Exception as e:
                st.error(f"❌ Ocurrió un error al generar el itinerario: {str(e)}")
