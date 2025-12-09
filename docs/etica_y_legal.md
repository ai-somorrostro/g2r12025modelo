# ⚖️ Informe de Cumplimiento Ético y Legal (RA6)

## 1. Security by Design (Seguridad desde el Diseño)
Para cumplir con el criterio de protección frente a ataques y errores, se han implementado las siguientes medidas:
*   **Gestión de Secretos:** Ninguna credencial (API Keys, contraseñas de Elastic) está hardcodeada en el código. Se utilizan variables de entorno (`.env`) que no se suben al repositorio.
*   **Aislamiento de Red:** El chatbot se conecta a Elasticsearch mediante HTTPS (o HTTP interno controlado), asegurando que los datos no viajan por redes públicas innecesarias.
*   **Cortafuegos Semántico:** El System Prompt actúa como barrera de seguridad, impidiendo que el chatbot responda a preguntas fuera de ámbito (ej. matemáticas o temas sensibles no indexados).

## 2. Privacy by Design (Privacidad)
*   **Minimización de Datos:** Solo se envían al LLM los fragmentos de texto estrictamente necesarios para responder a la pregunta del usuario. La base de datos completa permanece en la infraestructura local (Elasticsearch), cumpliendo con la soberanía del dato.
*   **Anonimización:** El sistema no almacena datos personales de los usuarios que realizan las consultas en ninguna base de datos persistente del chatbot.

## 3. Sesgos y Equidad
Se ha instruido al modelo mediante el System Prompt para mantener un **tono neutral y periodístico**.
*   **Mitigación de Sesgos:** En caso de noticias donde el género no sea relevante o especificado, el modelo está instruido para usar lenguaje inclusivo o neutro, evitando asunciones estereotipadas.

## 4. Licencias de Uso
| Componente | Licencia | Uso en el Proyecto |
| :--- | :--- | :--- |
| **Streamlit** | Apache 2.0 | Interfaz de Usuario (Open Source) |
| **LangChain** | MIT | Orquestación lógica (Open Source) |
| **Elasticsearch** | Elastic License 2.0 | Motor de Búsqueda |
| **GPT-4o-mini** | Propietaria (OpenAI) | Generación de texto (Uso comercial permitido vía API) |
| **Código Propio** | MIT | Se libera el código del chatbot bajo licencia MIT. |