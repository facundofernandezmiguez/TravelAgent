"""Streamlit app for travel agent."""
import streamlit as st
from travel_agent import TravelAgent
import traceback

def initialize_session_state():
    """Initialize session state variables."""
    if "travel_agent" not in st.session_state:
        st.session_state.travel_agent = TravelAgent()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "error_count" not in st.session_state:
        st.session_state.error_count = 0

def process_message(agent: TravelAgent, message: str) -> str:
    """Process a message using the travel agent."""
    try:
        # Reset error count on successful message
        st.session_state.error_count = 0
        return agent.process_message(message)
    except Exception as e:
        st.session_state.error_count += 1
        error_msg = str(e)
        
        # Log the full error for debugging
        print(f"Error processing message: {error_msg}")
        print(traceback.format_exc())
        
        # Handle different error scenarios
        if "rate_limit_exceeded" in error_msg:
            wait_time = agent.extract_wait_time(error_msg)
            return f"Lo siento, el servicio está un poco ocupado. Por favor, intentá de nuevo en {wait_time} minutos."
        elif "context_length_exceeded" in error_msg:
            # Clear conversation history if too long
            st.session_state.messages = st.session_state.messages[-5:]
            return "Lo siento, la conversación es muy larga. He limpiado un poco el historial. ¿Podrías repetir tu última pregunta?"
        elif st.session_state.error_count >= 3:
            # Reset agent if multiple errors occur
            st.session_state.travel_agent = TravelAgent()
            st.session_state.error_count = 0
            return "Lo siento, estoy teniendo problemas. He reiniciado el sistema. ¿Podrías empezar de nuevo?"
        else:
            return "Lo siento, hubo un error. ¿Podrías intentarlo de nuevo?"

def display_welcome_message():
    """Display welcome message and instructions."""
    st.markdown("""
    # 🌎 Asistente de Viajes

    ¡Hola! Soy tu asistente personal de viajes. Te puedo ayudar a:
    - 🛫 Planificar tu próximo viaje
    - 🏨 Encontrar hoteles
    - 🎯 Descubrir actividades
    - 💰 Ajustar todo a tu presupuesto

    **¿Cómo empezar?**
    Simplemente contame:
    - A dónde te gustaría ir
    - Cuándo querés viajar
    - Tu presupuesto aproximado
    """)

def main():
    """Main app function."""
    initialize_session_state()
    
    # Display welcome message only on first load
    if not st.session_state.messages:
        display_welcome_message()

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("¿En qué te puedo ayudar?"):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                # Process message 
                with st.spinner("Pensando..."):
                    response = process_message(st.session_state.travel_agent, prompt)
                
                # Update chat
                message_placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = "Lo siento, hubo un error inesperado. Por favor, intentá de nuevo."
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                print(f"Unexpected error: {str(e)}")
                print(traceback.format_exc())

if __name__ == "__main__":
    main()
