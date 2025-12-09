# 📘 Memoria Técnica del Proyecto NewsAI

## 1. Selección del Modelo de Lenguaje (LLM)
Para este proyecto se ha seleccionado el modelo **GPT-4o-mini** a través de OpenRouter.

**Justificación y Comparativa:**
| Característica | GPT-4o-mini (Seleccionado) | Llama 3 (Local) | GPT-4 Turbo |
| :--- | :--- | :--- | :--- |
| **Coste** | Muy bajo ($0.15/1M tokens) | Gratuito (Hardware) | Alto |
| **Latencia** | Muy baja (<1s) | Depende de GPU | Media |
| **Ventana de Contexto** | 128k tokens | 8k - 128k | 128k |
| **Capacidad RAG** | Alta (Instrucciones complejas) | Media | Muy Alta |

**Decisión:** Se elige GPT-4o-mini por ofrecer el mejor equilibrio entre **capacidad de razonamiento** para tareas RAG y **eficiencia de costes** para un entorno de producción, superando a modelos locales que requerirían hardware dedicado costoso en la infraestructura del instituto.

## 2. Arquitectura y Flujo de la Conversación
El sistema sigue una arquitectura **RAG (Retrieval-Augmented Generation)** desacoplada:

1.  **Input del Usuario:** El usuario realiza una pregunta en lenguaje natural.
2.  **Recuperación (Retrieval):**
    *   El sistema conecta con **Elasticsearch** (Puerto 9200).
    *   Se ejecuta una búsqueda de texto completo (`multi_match`) sobre los campos `title`, `body` y `author`.
    *   Se recuperan los 5 documentos más relevantes (Top-K).
3.  **Aumento (Augmentation):**
    *   Se construye un contexto único concatenando los fragmentos recuperados.
    *   Se inyectan instrucciones de seguridad (System Prompt).
4.  **Generación:** El LLM genera la respuesta basándose *exclusivamente* en el contexto inyectado.

## 3. Diseño del System Prompt
Se ha implementado una estrategia de **"Prompt de Amnesia"** para mitigar alucinaciones.

*   **Iteración 1 (Básica):** "Responde a la pregunta con el texto". *Resultado:* El modelo usaba conocimientos externos (ej. datos de 2023).
*   **Iteración 2 (Final - Optimizada):** Se fuerza al modelo a ignorar conocimientos previos y se simula una fecha actual (Diciembre 2025). Se añaden cláusulas negativas ("Si no lo sabes, di que no hay información").

## 4. Optimización y Ajuste
*   **Temperatura 0.0:** Se ha configurado la temperatura a 0 para eliminar la creatividad y garantizar la **facticidad** (necesario en noticias).
*   **Búsqueda Híbrida:** Ante la incompatibilidad de dimensiones vectoriales (384 vs 768), se optó por una búsqueda `multi_match` (BM25) que ha demostrado ser más robusta para encontrar términos específicos ("DANA", "Mazón") que la búsqueda vectorial pura en este escenario.

## 5. Pre-procesamiento de Consultas con NLP (Novedad Técnica)
Para mejorar la precisión de la recuperación (Retrieval), se ha implementado un módulo de **Optimización de Consultas** basado en LLM antes de realizar la búsqueda en Elasticsearch.

**Problema detectado:**
Las búsquedas vectoriales o de texto fallaban ante:
1.  Errores ortográficos del usuario (ej: "Karlos Mazon").
2.  "Ruido" en la frase (ej: "Dime por favor las noticias más actuales sobre la DANA").

**Solución Implementada:**
Se utiliza una cadena de procesamiento (LangChain) que recibe el input crudo del usuario y lo transforma en una **query canónica** optimizada para el motor de búsqueda.
*   *Input:* "Dime cosas de Karlos"
*   *Proceso NLP:* Corrección ortográfica + Eliminación de Stopwords.
*   *Output:* "Carlos" -> Esto es lo que se envía a Elasticsearch.

Esto demuestra una aplicación avanzada de NLP para mejorar la interacción humano-máquina.