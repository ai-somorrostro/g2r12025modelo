# NewsAI Studio - Sistema de Análisis de Noticias mediante Inteligencia Artificial

NewsAI Studio es una aplicación de software diseñada para la consulta y análisis de noticias en tiempo real utilizando una arquitectura RAG (Retrieval-Augmented Generation).

El sistema permite a los usuarios interactuar mediante lenguaje natural con una base de datos corporativa (Elasticsearch), garantizando respuestas veraces, actualizadas y libres de alucinaciones gracias a un estricto filtrado ético y de seguridad.

## Tabla de Contenidos
1.  Descripción del Sistema
2.  Requisitos Previos
3.  Instalación y Configuración
4.  Despliegue con Docker
5.  Manual de Uso
6.  Detención del Sistema
7.  Estructura del Proyecto

---

## 1. Descripción del Sistema

El software actúa como un intermediario inteligente entre el usuario y una base de datos de noticias. Sus funciones principales incluyen:

*   **Búsqueda Semántica y de Texto:** Conexión directa con índices de Elasticsearch.
*   **Procesamiento de Lenguaje Natural (NLP):** Módulo intermedio que corrige errores ortográficos y detecta la intención del usuario antes de realizar la búsqueda.
*   **Persistencia de Datos:** Almacenamiento local del historial de conversaciones.
*   **Seguridad:** Gestión de credenciales mediante variables de entorno y aislamiento de ejecución mediante contenedores.

---

## 2. Requisitos Previos

Para ejecutar este proyecto, es necesario disponer de los siguientes elementos. Si no dispone de ellos, siga las instrucciones adjuntas.

### 2.1. Entorno de Ejecución (Docker)
El proyecto se ejecuta dentro de un contenedor para garantizar la compatibilidad. Debe tener Docker instalado en su sistema.

**Instrucciones de instalación para Ubuntu/Linux:**
Si no tiene Docker instalado, ejecute los siguientes comandos en su terminal:

```bash
# 1. Actualizar el índice de paquetes
sudo apt-get update

# 2. Instalar paquetes necesarios
sudo apt-get install ca-certificates curl gnupg

# 3. Instalar Docker
sudo apt-get install docker.io

# 4. Verificar la instalación
sudo docker --version
```

### 2.2. Acceso a Elasticsearch
El sistema requiere conexión a una instancia de Elasticsearch activa. Necesitará:
*   URL de conexión (IP y Puerto, habitualmente 9200).
*   Nombre del índice de noticias.
*   Credenciales de acceso (Usuario y Contraseña).
*   Certificado de seguridad SSL (`http_ca.crt`) del servidor.

### 2.3. Clave de API (LLM)
Es necesaria una clave de API válida de OpenRouter o OpenAI para el funcionamiento del modelo de lenguaje.

---

## 3. Instalación y Configuración

Siga estos pasos estrictamente para preparar el entorno antes de la ejecución.

### Paso 1: Ubicación de Archivos
Asegúrese de estar ubicado en la carpeta raíz del proyecto. Debería ver los archivos `Dockerfile`, `requirements.txt` y la carpeta `src`.

### Paso 2: Configuración del Certificado de Seguridad
Para que la conexión con la base de datos sea segura, debe copiar el archivo de certificado `http_ca.crt` proporcionado por su administrador de sistemas a la raíz de este proyecto.

*   **Acción:** Copie el archivo `http_ca.crt` en la misma carpeta donde se encuentra este archivo README.md.

### Paso 3: Configuración de Variables de Entorno
El sistema no almacena contraseñas en el código. Debe crear un archivo de configuración local.

1.  Cree un archivo llamado `.env` en la raíz del proyecto.
2.  Abra el archivo con un editor de texto y pegue el siguiente contenido, sustituyendo los valores de ejemplo por sus datos reales:

```ini
# Configuración del Proveedor de IA
OPENAI_API_KEY=pegue_aqui_su_clave_api_completa

# Configuración de la Base de Datos (Elasticsearch)
ELASTIC_URL=https://XXX.XXX.X.XX:9200
ELASTIC_INDEX=nombre_del_indice_de_noticias
ELASTIC_USER=nombre_de_usuario
ELASTIC_PASSWORD=contraseña_del_usuario

# Configuración de Seguridad SSL
ELASTIC_CERT_PATH=./http_ca.crt
ELASTIC_VERIFY_SSL=True
```

3.  Guarde y cierre el archivo.

### Paso 4: Preparación del Almacenamiento
El sistema guarda el historial de los chats en su disco local. Debe crear la carpeta donde se almacenarán estos datos para evitar errores de permisos.

Ejecute en la terminal:
```bash
mkdir -p chats_data
```

---

## 4. Despliegue con Docker

Una vez configurado el entorno, proceda a construir y ejecutar la aplicación.

### Paso 1: Construcción de la Imagen
Este proceso empaqueta el código y descarga las librerías necesarias. Solo es necesario hacerlo la primera vez o cuando se modifique el código.

Ejecute:
```bash
sudo docker build -t news-ai-bot .
```

### Paso 2: Ejecución del Contenedor
Este comando inicia el servidor de la aplicación.

Ejecute:
```bash
docker compose up -d --build
```

**Explicación del comando:**
*   `-p 8501:8501`: Hace accesible la aplicación web en el puerto 8501.
*   `--env-file .env`: Carga las contraseñas configuradas en el paso anterior.
*   `-v ...`: Conecta la carpeta local `chats_data` con el contenedor para que no se pierdan las conversaciones al apagar el sistema.

---

## 5. Manual de Uso

Una vez el contenedor esté en ejecución:

1.  Abra su navegador web.
2.  Acceda a la dirección: `http://localhost:8501` (o la IP de su máquina virtual si accede remotamente).

**Interfaz de Usuario:**
*   **Barra Lateral (Izquierda):** Permite crear nuevos chats, ver el historial de conversaciones anteriores, cambiar el modelo de inteligencia artificial y ajustar la temperatura (creatividad).
*   **Chat (Centro):** Área de interacción. Escriba sus preguntas en lenguaje natural.

**Ejemplos de interacción:**
*   *"Dime las noticias más actuales sobre el medioambiente."*
*   *"¿Qué ha pasado con el FC Barcelona?"*

---

## 6. Detención del Sistema

Para detener la aplicación de manera segura:

1.  Vaya a la terminal donde se está ejecutando el contenedor.
2.  Presione la combinación de teclas `Ctrl + C`.

Si el contenedor se está ejecutando en segundo plano o no responde, puede forzar su detención:

```bash
# 1. Listar contenedores activos para obtener el ID
sudo docker ps

# 2. Detener el contenedor (sustituya ID_CONTENEDOR por el código alfanumérico)
sudo docker stop ID_CONTENEDOR
```

---

## 7. Estructura del Proyecto

A continuación se detalla la organización de los archivos para referencia técnica:

*   **src/**: Contiene el código fuente de la aplicación.
    *   `app.py`: Controla la interfaz gráfica y la interacción con el usuario.
    *   `logic.py`: Contiene la lógica de negocio, conexión a bases de datos y procesamiento de lenguaje natural.
*   **docs/**: Documentación técnica y legal del proyecto.
*   **chats_data/**: Directorio donde se almacena el historial de conversaciones (formato JSON).
*   **Dockerfile**: Archivo de configuración para la creación del contenedor Docker.
*   **requirements.txt**: Lista de dependencias y librerías Python necesarias.
*   **.env**: Archivo de configuración de variables de entorno (Credenciales).
*   **.gitignore**: Configuración para excluir archivos sensibles del control de versiones.
*   **http_ca.crt**: Certificado de seguridad para la conexión SSL.