# Memoria Técnica del Proyecto NewsAI

## 1. Selección del Modelo de Lenguaje (LLM)
Para el núcleo de inferencia del sistema, se ha implementado una arquitectura flexible que permite alternar entre modelos de alto rendimiento. La configuración principal utiliza **GPT-4o-mini** a través de la pasarela OpenRouter.

**Justificación de la elección:**
*   **Eficiencia en RAG:** El modelo presenta una latencia mínima en la generación de tokens, lo cual es crítico para mantener la fluidez en una interfaz de chat en tiempo real.
*   **Capacidad de Contexto:** Su ventana de contexto permite inyectar múltiples noticias completas recuperadas de la base de datos sin truncamiento severo.
*   **Adherencia a Instrucciones:** En las pruebas realizadas, GPT-4o-mini demostró una obediencia superior a las "Prohibiciones Estrictas" definidas en el *System Prompt* (no generar código, no realizar cálculos), superando a modelos locales más pequeños.
*   **Pruebas de varios modelos** Despues de probar varios modelos, como puede ser Llama, en varias versiones, Gemini 1.5, Gemini 2.5 pro, y diferentes modelos mas. Esos modelos no seguian correctamente las solicitudes que se le daban, ni hacian caso a las prohibiciones. Por lo cual finalmente se ha decidido ir por los modelos mas fiables.

## 2. Arquitectura del Sistema
El proyecto sigue un patrón de diseño modular (MVC simplificado) para garantizar la escalabilidad y el mantenimiento:

1.  **Frontend (`app.py`):** Interfaz desarrollada en Streamlit. Gestiona el estado de la sesión, la visualización de métricas (scores de relevancia), el panel de depuración y la interacción con el usuario.
2.  **Backend Lógico (`logic.py`):** Módulo que encapsula la lógica de negocio. Contiene:
    *   Gestión de conexión con Elasticsearch.
    *   Clases personalizadas para servicios externos (`RemoteEmbeddings`).
    *   Lógica de enrutamiento semántico (`analyze_intent`).
    *   Sistema de registro de depuración (`DebugLogger`).
3.  **Microservicio de Embeddings:** Se utiliza una clase personalizada `RemoteEmbeddings` que conecta con una API interna (`/api/embed`), desacoplando la carga computacional de la vectorización del contenedor principal.

## 3. Estrategia de Procesamiento de Lenguaje Natural (PLN)
El sistema implementa un flujo de PLN avanzado antes de realizar cualquier búsqueda, estructurado en la función `analyze_intent`:

*   **Detección de Intención:** Un LLM analiza la entrada del usuario para clasificarla en:
    *   *Saludo:* Interacción social que no requiere búsqueda.
    *   *Intento Prohibido:* Detección de palabras clave (código, script, matemáticas) para bloquear la solicitud inmediatamente.
    *   *Consulta de Información:* Extracción del tema principal y el marco temporal.
*   **Normalización de Entidades:** El sistema limpia la consulta eliminando verbos de acción ("resúmela", "explícame") para centrar la búsqueda vectorial exclusivamente en las entidades nombradas (ej: "FC Barcelona").
*   **Cálculo Temporal Dinámico:** El sistema inyecta la fecha actual en el prompt para que el modelo pueda interpretar expresiones relativas como "ayer" o "esta semana" y convertirlas en filtros numéricos (`days`).

## 4. Búsqueda Híbrida y Recuperación
La función `search_elastic` implementa una estrategia de recuperación robusta:

1.  **Filtrado Temporal:** Se aplican filtros de rango (`range: {date: ...}`) basados en la interpretación del NLP.
2.  **Estrategia Dual:**
    *   *Búsqueda Genérica:* Si no se detecta un tema específico, se ejecuta un `match_all` ordenado cronológicamente.
    *   *Búsqueda Vectorial:* Si hay un tema, se utiliza el modelo de embeddings remoto para generar el vector y realizar una búsqueda k-NN (k-Nearest Neighbors) en Elasticsearch.
    *   *Fallback:* Se incluye un mecanismo de recuperación ante fallos que cambia a búsqueda de texto (`multi_match`) si la vectorización falla.

## 5. Diseño del System Prompt
El prompt del sistema (`get_rag_chain`) se ha diseñado con técnicas de "Chain of Thought" y delimitación de contexto:

*   **Definición de Rol:** Asistente de noticias profesional y analítico.
*   **Capacidades Explícitas:** Se autoriza al modelo a sintetizar, listar, explicar y contextualizar, siempre que la base factual provenga del contexto.
*   **Guardrails (Seguridad):** Instrucciones negativas estrictas para evitar la invención de datos, la generación de código o contenido creativo literario.
*   **Gestión de Vacíos:** Instrucción precisa para comunicar la ausencia de información en la base de datos en lugar de alucinar una respuesta.

## 6. Pruebas, Depuración y Métricas
El sistema incluye un módulo dedicado `DebugLogger` y un panel visual en la interfaz para la trazabilidad:

*   **Registro de Trazas:** Se almacenan logs JSON con la consulta original, la interpretación del intent, los parámetros de búsqueda y los resultados crudos.
*   **Métricas de Relevancia:** Se calcula y muestra al usuario el "Score" promedio de los documentos recuperados, proporcionando transparencia sobre la calidad de la coincidencia (semántica o textual).
*   **Persistencia de Logs:** Los logs de depuración se almacenan en disco (`debug_logs/`) para auditoría posterior.

## 7. Implementación y Despliegue
*   **Docker:** Entorno contenerizado para asegurar la consistencia de las dependencias.
*   **Persistencia:** Uso de volúmenes para mantener el historial de chats (`chats/`) y logs entre reinicios.
*   **Seguridad:** Inyección de credenciales (API Keys, Certificados SSL) mediante variables de entorno, sin exposición en el código fuente.

## ANEXO: Fundamentación Teórica y Rol Lingüístico 

### 1. Relación con el Procesamiento del Lenguaje Natural (PLN)
Este proyecto no se limita a la ejecución de comandos, sino que integra las dos ramas fundamentales del PLN para superar las limitaciones de los sistemas tradicionales:

*   **Comprensión (NLU):** A través de la vectorización (Embeddings), el sistema "entiende" que una búsqueda sobre "catástrofe en Valencia" está semánticamente relacionada con "DANA", aunque no compartan palabras clave. Además, el Router Semántico desambigua la intención temporal del usuario (interpretando deícticos como "ayer" o "esta semana").
*   **Generación (NLG):** El modelo GPT-4o-mini no recupera texto estático, sino que genera nuevo discurso coherente y cohesionado en español, adaptándose al formato solicitado (lista, resumen, explicación).
*   **Gestión de Limitaciones:** Se ha abordado la principal limitación de los LLM generativos (la alucinación o invención de datos) mediante la arquitectura RAG, que restringe la generación exclusivamente a los hechos verificados en la base de datos Elasticsearch.

### 2. El Papel del Lingüista en la IA y la Colaboración Interdisciplinar
El desarrollo de este chatbot ha requerido una simbiosis entre la ingeniería de software y la lingüística computacional. El rol del lingüista se ha materializado en:

*   **Ingeniería de Prompts (Prompt Engineering):** Diseño de las instrucciones en lenguaje natural que guían al modelo. Esto implica definir el registro (periodístico/neutro), la pragmática (cómo reaccionar ante saludos vs. órdenes) y la gestión del discurso.
*   **Análisis de Intenciones:** Definición de las categorías semánticas que el sistema debe reconocer ("Saludo", "Búsqueda Temática", "Búsqueda Temporal", "Intento Prohibido") para dirigir el flujo lógico.
*   **Colaboración con Informática:** La arquitectura MVC del proyecto refleja esta colaboración. Mientras el ingeniero gestiona la conexión a la base de datos y el despliegue en Docker (`logic.py` backend), el lingüista define las reglas de comportamiento y respuesta dentro de las plantillas de texto (`templates`), permitiendo ajustar la "personalidad" del bot sin alterar el código fuente funcional.