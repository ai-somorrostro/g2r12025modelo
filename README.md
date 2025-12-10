# NewsAI Studio - Sistema de Análisis de Noticias mediante Inteligencia Artificial

NewsAI Studio es una aplicación de software diseñada para la consulta y análisis de noticias en tiempo real utilizando una arquitectura RAG (Retrieval-Augmented Generation).

El sistema permite a los usuarios interactuar mediante lenguaje natural con una base de datos corporativa (Elasticsearch), garantizando respuestas veraces, actualizadas y libres de alucinaciones gracias a un estricto filtrado ético y de seguridad.

## Tabla de Contenidos
1.  Descripción del Sistema
2.  Requisitos Previos
3.  Instalación y Configuración
4.  Despliegue con Docker Compose
5.  Manual de Uso
6.  Detención del Sistema
7.  Estructura del Proyecto

---

## 1. Descripción del Sistema

El software actúa como un intermediario inteligente entre el usuario y una base de datos de noticias. Sus funciones principales incluyen:

*   **Búsqueda Híbrida:** Combinación de búsqueda vectorial (semántica) y búsqueda de texto completo en Elasticsearch.
*   **Procesamiento de Lenguaje Natural (NLP):** Módulo intermedio que corrige errores ortográficos, detecta la intención del usuario y calcula filtros temporales antes de realizar la búsqueda.
*   **Persistencia de Datos:** Almacenamiento local del historial de conversaciones y registros de depuración (logs).
*   **Seguridad:** Gestión de credenciales mediante variables de entorno, autenticación por API Key y aislamiento de ejecución mediante contenedores.

---

## 2. Requisitos Previos

Para ejecutar este proyecto, es necesario disponer de los siguientes elementos.

### 2.1. Entorno de Ejecución (Docker)
El proyecto se ejecuta dentro de un contenedor para garantizar la compatibilidad. Debe tener Docker y Docker Compose instalados en su sistema.

**Instrucciones de instalación para Ubuntu/Linux:**
Si no tiene Docker instalado, ejecute los siguientes comandos en su terminal:

```bash
# 1. Actualizar el índice de paquetes
sudo apt-get update

# 2. Instalar paquetes necesarios
sudo apt-get install ca-certificates curl gnupg

# 3. Instalar Docker
sudo apt-get install docker.io docker-compose-v2

# 4. Verificar la instalación
sudo docker compose version
```

### 2.2. Acceso a Elasticsearch
El sistema requiere conexión a una instancia de Elasticsearch activa. Necesitará:
*   URL de conexión (IP y Puerto, habitualmente 9200).
*   **API Key** válida de Elasticsearch (codificada en Base64).
*   Certificado de seguridad SSL (`http_ca.crt`) del servidor.

### 2.3. Microservicio de Embeddings
Es necesario disponer de acceso a la API de vectorización interna (habitualmente en el puerto 8000) para la generación de embeddings.

### 2.4. Clave de API (LLM)
Es necesaria una clave de API válida de OpenRouter o OpenAI para el funcionamiento del modelo de lenguaje.

---

## 3. Instalación y Configuración

Siga estos pasos estrictamente para preparar el entorno antes de la ejecución.

### Paso 1: Ubicación de Archivos
Asegúrese de estar ubicado en la carpeta raíz del proyecto. Debería ver los archivos `docker-compose.yml`, `requirements.txt` y la carpeta `src`.

### Paso 2: Configuración del Certificado de Seguridad
Para que la conexión con la base de datos sea segura, debe copiar el archivo de certificado `http_ca.crt` proporcionado por su administrador de sistemas a la raíz de este proyecto.

*   **Acción:** Copie el archivo `http_ca.crt` en la misma carpeta donde se encuentra este archivo README.md.

### Paso 3: Configuración de Variables de Entorno
El sistema no almacena contraseñas en el código. Debe crear un archivo de configuración local.

1.  Cree un archivo llamado `.env` en la raíz del proyecto.
2.  Abra el archivo con un editor de texto y pegue el siguiente contenido, sustituyendo los valores de ejemplo por sus datos reales:

```ini
# Configuración del Proveedor de IA (LLM)
OPENAI_API_KEY=pegue_aqui_su_clave_api_completa

# Configuración de la Base de Datos (Elasticsearch)
ELASTIC_URL=https://192.199.1.XX:9200
# Usar el comodín (*) permite buscar en los índices de todos los días
ELASTIC_INDEX=noticias-*
ELASTIC_API_KEY=pegue_aqui_su_api_key_de_elastic

# Configuración de Seguridad SSL
ELASTIC_CERT_PATH=./http_ca.crt
ELASTIC_VERIFY_SSL=True

# Configuración del Servicio de Embeddings
EMBEDDING_API_URL=http://192.199.1.XX:8000/api/embed
```

3.  Guarde y cierre el archivo.

### Paso 4: Preparación del Almacenamiento
El sistema guarda el historial de los chats y los registros de depuración en su disco local. Debe crear las carpetas donde se almacenarán estos datos para evitar errores de permisos.

Ejecute en la terminal:
```bash
mkdir -p chats_data
mkdir -p debug_logs
```

---

## 4. Despliegue con Docker Compose

Una vez configurado el entorno, proceda a construir y ejecutar la aplicación utilizando Docker Compose, que gestionará la red y los volúmenes automáticamente.

### Ejecución del Servicio
Ejecute el siguiente comando en la terminal:

```bash
sudo docker compose up -d --build
```

**Explicación del comando:**
*   `up`: Crea e inicia los contenedores.
*   `-d`: Ejecuta el contenedor en segundo plano (modo "detached").
*   `--build`: Fuerza la reconstrucción de la imagen para asegurar que se utiliza la última versión del código fuente.

---

## 5. Manual de Uso

Una vez el contenedor esté en ejecución:

1.  Abra su navegador web.
2.  Acceda a la dirección: `http://localhost:8501` (o la IP de su máquina virtual si accede remotamente).

**Interfaz de Usuario:**
*   **Barra Lateral (Izquierda):**
    *   **Nuevo Chat:** Inicia una sesión limpia.
    *   **Historial:** Permite cargar conversaciones anteriores.
    *   **Configuración:** Selección de modelo y temperatura.
    *   **Ver Logs de Debug:** Abre un panel técnico para inspeccionar la lógica interna del sistema.
*   **Chat (Centro):** Área de interacción. Escriba sus preguntas en lenguaje natural.

**Ejemplos de interacción:**
*   *"Dime las noticias más actuales sobre el medioambiente."* (Búsqueda temporal)
*   *"¿Qué ha pasado con el FC Barcelona?"* (Búsqueda semántica)

---

## 6. Detención del Sistema

Para detener la aplicación y eliminar los recursos asociados (contenedores y redes) de manera limpia, ejecute:

```bash
sudo docker compose down -v
```

**Nota:** El parámetro `-v` asegura que se eliminen los volúmenes temporales si los hubiera, aunque los datos persistentes en `chats_data` y `debug_logs` se mantendrán en su disco local.

---

## 7. Estructura del Proyecto

A continuación se detalla la organización de los archivos para referencia técnica:

*   **src/**: Contiene el código fuente de la aplicación.
    *   `app.py`: Controla la interfaz gráfica (Frontend).
    *   `logic.py`: Contiene la lógica de negocio, conexión a Elastic, NLP y gestión de logs (Backend).
*   **docs/**: Documentación técnica y legal del proyecto.
*   **chats_data/**: Directorio persistente para el historial de conversaciones.
*   **debug_logs/**: Directorio persistente para los registros técnicos de depuración.
*   **docker-compose.yml**: Definición del servicio, redes y volúmenes.
*   **Dockerfile**: Archivo de configuración para la creación de la imagen.
*   **requirements.txt**: Lista de dependencias y librerías Python necesarias.
*   **.env**: Archivo de configuración de variables de entorno (Credenciales).
*   **.gitignore**: Configuración para excluir archivos sensibles del control de versiones.
*   **http_ca.crt**: Certificado de seguridad para la conexión SSL.
