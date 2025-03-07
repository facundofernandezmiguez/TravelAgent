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

with st.form(key="form_planificacion"):
    col1, col2 = st.columns(2)
    with col1:
        # Sin valor por defecto para evitar hardcodeo
        origen = st.text_input("📍 Ciudad de origen")
        destinos_input = st.text_input("🏙️ Destinos (separados por coma)")
        destinos = [d.strip() for d in destinos_input.split(",") if d.strip()]
        fecha_inicio = st.date_input("🗓️ Fecha de inicio", value=fecha_inicio_default, min_value=fecha_actual)
    with col2:
        # Valor predeterminado igual a la fecha de inicio para forzar que el usuario elija otra fecha
        fecha_fin = st.date_input("🗓️ Fecha de regreso", min_value=fecha_inicio)
        preferencias = st.multiselect("🌟 Preferencias de viaje", 
                                      ["Cultura", "Gastronomía", "Aventura", "Relax", "Naturaleza", "Historia", "Arte", "Compras"],
                                      default=[])
    submit_button = st.form_submit_button(label="🚀 Generar Itinerario")

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
    elif not preferencias:
        st.error("❌ Por favor, selecciona al menos una preferencia de viaje.")
    else:
        with st.spinner("Generando tu itinerario..."):
            try:
                itinerario = generar_itinerario(origen, destinos, fecha_inicio, fecha_fin, preferencias)
                st.success("✅ ¡Itinerario generado exitosamente!")
                st.markdown("### Tu itinerario personalizado:")
                st.markdown(itinerario)
            except Exception as e:
                st.error(f"❌ Ocurrió un error al generar el itinerario: {str(e)}")
