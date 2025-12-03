import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Cargar entorno
load_dotenv()

def test_connection():
    print("Iniciando prueba de conexión a Elasticsearch...")
    
    url = os.getenv("ELASTIC_URL")
    user = os.getenv("ELASTIC_USER")
    password = os.getenv("ELASTIC_PASSWORD")
    cert_path = os.getenv("ELASTIC_CERT_PATH")
    verify_ssl = os.getenv("ELASTIC_VERIFY_SSL") == "True"

    print(f"Intentando conectar a: {url}")
    print(f"Verificación SSL activada: {verify_ssl}")

    try:
        # Configuración del cliente
        if verify_ssl and os.path.exists(cert_path):
            client = Elasticsearch(
                url,
                basic_auth=(user, password),
                ca_certs=cert_path
            )
        else:
            if verify_ssl:
                print("ADVERTENCIA: SSL activado pero no encuentro el archivo .crt")
            else:
                print("ADVERTENCIA: SSL desactivado (Inseguro)")
            
            client = Elasticsearch(
                url,
                basic_auth=(user, password),
                verify_certs=False,
                ssl_show_warn=False
            )

        # Ping
        if client.ping():
            info = client.info()
            print("¡CONEXIÓN EXITOSA!")
            print(f"   Versión de Elastic: {info['version']['number']}")
            print(f"   Nombre del Cluster: {info['cluster_name']}")
        else:
            print("El servidor no responde al Ping.")

    except Exception as e:
        print(f"Error crítico de conexión: {e}")

if __name__ == "__main__":
    test_connection()