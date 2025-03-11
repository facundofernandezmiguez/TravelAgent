import subprocess
import sys

if __name__ == '__main__':
    # Ejecutar streamlit directamente con subprocess
    try:
        result = subprocess.run(["streamlit", "run", "src/app.py"], 
                              check=True,
                              text=True)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error al ejecutar Streamlit: {e}")
        print("Puedes ejecutar la aplicación directamente con: streamlit run src/app.py")
        sys.exit(1)
