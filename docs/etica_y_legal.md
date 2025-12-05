# Informe de Cumplimiento Ético y Legal (RA6)

## 1. Seguridad desde el Diseño (Security by Design)
*   **Gestión de Secretos:** Se aplica una política de "Cero Confianza". Ninguna credencial (API Keys, contraseñas) se almacena en el código fuente. Se utilizan variables de entorno (`.env`) inyectadas en tiempo de ejecución.
*   **Autenticación Robusta:** La conexión con la base de datos Elasticsearch utiliza **API Keys** específicas con permisos limitados, evitando el uso de credenciales de superusuario básicas.
*   **Cifrado:** Todas las comunicaciones con la base de datos están cifradas mediante SSL/TLS (`http_ca.crt`).

## 2. Privacidad y Soberanía del Dato
*   **Procesamiento Local de Vectores:** La vectorización de las consultas se realiza mediante una API interna controlada, evitando enviar los textos de búsqueda a proveedores de embeddings públicos.
*   **Almacenamiento Controlado:** El historial de conversaciones y los logs de depuración se almacenan localmente en volúmenes Docker bajo el control del administrador, sin realizar copias en nubes de terceros no autorizadas.
*   **Minimización:** Solo se envían al LLM los fragmentos de texto estrictamente necesarios para responder a la consulta en curso.

## 3. Ética y Transparencia (XAI)
*   **Explicabilidad:** La interfaz muestra claramente las fuentes (URLs) y la puntuación de relevancia (`_score`) de cada noticia utilizada. Esto permite al usuario verificar la veracidad de la información y entender por qué el sistema seleccionó esos datos.
*   **Control de Contenidos:** El System Prompt incluye directrices estrictas para evitar la generación de contenido no relacionado con noticias (poemas, código, ficción) y bloquea intentos de uso para fines no informativos.
*   **Neutralidad:** El modelo está instruido para mantener un tono objetivo y periodístico.

## 4. Propiedad Intelectual
*   **Licencia del Software:** El código fuente desarrollado para este proyecto se distribuye bajo licencia **MIT**.
*   **Componentes de Terceros:** Se respetan las licencias de las librerías utilizadas (Apache 2.0 para Streamlit, MIT para LangChain, Elastic License para el driver).
*   **Contenidos:** El sistema actúa como un motor de indexación y búsqueda. Los derechos de propiedad intelectual sobre el contenido de las noticias pertenecen a sus respectivos autores y medios de comunicación.