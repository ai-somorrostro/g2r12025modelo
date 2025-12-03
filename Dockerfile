# 1. Imagen Base (Python ligero)
FROM python:3.9-slim

# 2. Directorio de trabajo
WORKDIR /app

# 3. Instalar dependencias del sistema (necesarias para compilar algunas librerías)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar y cargar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el certificado de seguridad (RA6 - Security by Design)
# El archivo debe estar en la misma carpeta que el Dockerfile al construir
COPY http_ca.crt .

# 6. Copiar el código fuente
# Copiamos la carpeta src entera al contenedor
COPY src/ ./src/

# 7. Exponer el puerto de Streamlit
EXPOSE 8501

# 8. Chequeo de salud (Healthcheck) - Criterio de "Despliegue robusto"
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 9. Comando de ejecución
# Streamlit buscará app.py dentro de la carpeta src
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]