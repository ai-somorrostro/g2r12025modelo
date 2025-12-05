# Memoria Técnica del Proyecto NewsAI

## 1. Selección del Modelo de Lenguaje (LLM)
Se ha seleccionado **GPT-4o-mini** como motor principal de inferencia tras un análisis comparativo de rendimiento y coste.

*   **Eficiencia:** Ofrece la latencia más baja (<1s) para tareas de RAG, crucial para la experiencia de usuario en tiempo real.
*   **Coste:** Su ratio coste/rendimiento es superior a modelos mayores para tareas de síntesis y clasificación de texto.
*   **Ventana de Contexto:** Sus 128k tokens permiten inyectar múltiples noticias completas sin perder información.

## 2. Arquitectura del Sistema (Patrón MVC)
El sistema se ha refactorizado siguiendo un patrón de diseño desacoplado para garantizar la mantenibilidad y la separación de responsabilidades:

1.  **Frontend (`src/app.py`):** Capa de presentación desarrollada en Streamlit. Se encarga exclusivamente de la visualización de datos, gestión del estado de la sesión y renderizado de métricas de relevancia.
2.  **Backend Lógico (`src/logic.py`):** Núcleo del sistema. Centraliza la conexión con Elasticsearch, la gestión de modelos, el enrutamiento semántico y el sistema de registro (logging).
3.  **Microservicio de Embeddings:** Se utiliza una API externa dedicada (`/api/embed`) para la vectorización de consultas, optimizando el consumo de memoria RAM del contenedor principal al no cargar modelos pesados localmente.

## 3. Estrategia de Búsqueda Híbrida e Inteligente
Se ha implementado un sistema de recuperación de información avanzado que combina técnicas léxicas y semánticas:

*   **Router Semántico (NLP):** Un módulo previo analiza la consulta del usuario para extraer la intención.
    *   *Intención Temporal:* Detecta expresiones como "ayer" o "esta semana", calcula la fecha relativa y aplica filtros de rango en la base de datos.
    *   *Intención Temática:* Extrae las entidades clave (ej: "FC Barcelona") eliminando ruido lingüístico.
*   **Búsqueda Vectorial (k-NN):** Utiliza vectores densos (768 dimensiones) generados por el modelo `paraphrase-multilingual-mpnet-base-v2` para encontrar similitud semántica.
*   **Métricas de Relevancia:** El sistema calcula y muestra al usuario un "Score de Confianza" basado en la similitud del coseno de los documentos recuperados, aumentando la explicabilidad del sistema.

## 4. Sistema de Depuración y Trazabilidad
Para cumplir con los criterios de "Pruebas y Depuración", se ha desarrollado un módulo de **Debug Logger**.
*   Cada interacción genera un archivo de log JSON detallado en el servidor.
*   El panel de control permite inspeccionar en tiempo real: la consulta original, la interpretación del Router, los parámetros de búsqueda enviados a Elasticsearch y los scores individuales de cada documento recuperado.

## 5. Diseño del System Prompt
El prompt del sistema ha sido diseñado con instrucciones de "Cadena de Pensamiento" y restricciones de seguridad:
*   **Rigor Factual:** Instrucción estricta de basar las respuestas únicamente en el contexto proporcionado.
*   **Capacidades Permitidas:** Se habilita explícitamente la capacidad de resumir y sintetizar información, siempre que los datos provengan de la base de datos.
*   **Bloqueo de Alucinaciones:** Si el contexto está vacío, el modelo debe responder que no dispone de información.

## 6. Implementación y Despliegue
*   **Docker:** El entorno está contenerizado (`python:3.9-slim`) para garantizar la reproducibilidad.
*   **Persistencia:** Se utilizan volúmenes de Docker para almacenar el historial de chats (`/chats_data`) y los logs de depuración (`/debug_logs`), asegurando la persistencia de datos tras reinicios.
*   **Seguridad:** La conexión con Elasticsearch se realiza mediante autenticación por API Key y cifrado SSL.