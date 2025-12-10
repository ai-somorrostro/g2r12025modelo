# Informe de Cumplimiento Ético, Legal y Normativo

Este documento justifica la alineación del proyecto **NewsAI Studio** con los marcos regulatorios vigentes, demostrando un enfoque integral de privacidad, seguridad y ética desde la fase de diseño hasta la implementación.

## 1. Análisis de Riesgos y Seguridad (Security by Design)
Se ha implementado un plan de seguridad basado en la defensa en profundidad para mitigar riesgos técnicos y operativos:

*   **Protección contra Inyecciones (Prompt Injection):** Se utiliza un **Cortafuegos Semántico** en el *System Prompt*. Las instrucciones de seguridad ("PROHIBICIONES STRICTAS") tienen prioridad jerárquica sobre el input del usuario. Además, el módulo de NLP (`analyze_intent`) sanea la entrada antes de procesarla.
*   **Gestión de Secretos:** Política de "Cero Confianza". Ninguna credencial se almacena en el código. Se utilizan variables de entorno (`.env`) inyectadas en tiempo de ejecución.
*   **Cifrado en Tránsito:** La comunicación con la base de datos Elasticsearch fuerza el uso de **TLS/SSL** (`verify_ssl=True`) mediante certificados CA, protegiendo los datos frente a ataques *Man-in-the-Middle*.

## 2. Privacidad desde el Diseño (Privacy by Design)
Se demuestra un enfoque integral de privacidad que abarca todas las etapas del desarrollo, cumpliendo con el RGPD:

### 2.1. Arquitectura Privada (Diseño)
*   **Soberanía del Dato:** A diferencia de soluciones SaaS, la base de datos de noticias (Elasticsearch) y el historial de chats residen en infraestructura local controlada (volúmenes Docker), garantizando que la información no sale del perímetro de la organización.
*   **Vectorización Interna:** Se utiliza una API de embeddings propia (`/api/embed`), evitando enviar los textos de búsqueda a proveedores públicos de terceros.

### 2.2. Minimización y Transparencia (Implementación)
*   **Minimización:** El sistema no recolecta datos personales (PII) de los usuarios. Solo se procesa la consulta necesaria para la búsqueda.
*   **Transparencia:** El usuario es informado mediante un aviso legal visible de que interactúa con una IA y de que las respuestas se basan en noticias indexadas.

### 2.3. Derechos del Usuario (Operación)
*   **Derecho de Supresión (Art. 17 RGPD):** Se han programado funcionalidades específicas ("Eliminar Chat", "Limpiar Logs") que permiten la eliminación física y permanente de los datos de sesión, garantizando el derecho al olvido.

## 3. Identificación y Corrección de Sesgos
Se han identificado riesgos de sesgo inherentes a los LLM y se han aplicado correcciones activas:

*   **Identificación del Riesgo:** Los modelos de lenguaje tienden a asumir géneros basados en estereotipos profesionales (ej: asumir que "el médico" es hombre o "la enfermera" es mujer) debido a sus datos de entrenamiento.
*   **Estrategia de Corrección:** Se ha implementado una instrucción de **Neutralidad de Género** en el *System Prompt*. El modelo está obligado a utilizar lenguaje inclusivo o neutro cuando la noticia original no especifique el género de los protagonistas.
*   **Neutralidad Informativa:** Se fuerza al modelo a mantener un tono "periodístico y analítico", eliminando adjetivos valorativos o emocionales que puedan introducir sesgos de opinión no presentes en la fuente.

## 4. Licencias de Uso y Propiedad Intelectual
Se describen y justifican detalladamente las licencias de todos los componentes para asegurar la compatibilidad legal del proyecto.

### 4.1. Licencias de Componentes de Terceros
| Componente | Licencia | Justificación de Compatibilidad |
| :--- | :--- | :--- |
| **Streamlit** | Apache 2.0 | Licencia permisiva que permite el uso comercial, modificación y distribución del software sin obligar a liberar el código derivado. Ideal para interfaces empresariales. |
| **LangChain** | MIT | Licencia altamente permisiva compatible con cualquier tipo de proyecto (propietario o libre). Permite la integración sin restricciones virales. |
| **Elasticsearch** | Elastic License 2.0 | Permite el uso gratuito y modificación del software para uso interno. Restringe únicamente ofrecerlo como un servicio gestionado (SaaS) a terceros, lo cual cumple con el uso de este proyecto. |
| **GPT-4o-mini** | Propietaria (OpenAI) | El uso se rige por los Términos de Servicio de la API. El proyecto cumple con las políticas de uso aceptable (no generación de contenido ilegal o dañino). |

### 4.2. Licencia del Proyecto
*   **Código Fuente Propio:** Los scripts desarrollados (`src/app.py`, `src/logic.py`) se liberan bajo licencia **MIT**.
    *   *Motivo:* Fomentar la colaboración académica y permitir que otros estudiantes o desarrolladores reutilicen la arquitectura RAG sin restricciones legales complejas.
*   **Derechos de Contenido:** El sistema actúa como un índice de búsqueda. Se reconoce el derecho de autor de las noticias originales mediante la cita obligatoria de la **Fuente/URL** en cada respuesta, amparándose en el derecho de cita para fines informativos.