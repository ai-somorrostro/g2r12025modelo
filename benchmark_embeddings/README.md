# Benchmark de Modelos de Embeddings en Elasticsearch

Este proyecto permite evaluar múltiples modelos de embeddings para búsquedas semánticas en documentos indexados en Elasticsearch. Genera resultados detallados de los documentos más relevantes y calcula estadísticas de los scores de los modelos.

---

## Contenido

- `run_benchmark.py` – Script principal para ejecutar el benchmark.
- `benchmark_results.json` – Resultados de las búsquedas para cada modelo y query.
- `model_scores_average.json` – Media de scores por modelo para todas las queries.

---

## Requisitos

- Python 3.8+
- Elasticsearch 7.x o 8.x
- Módulos Python:
  ```bash
  pip install requests elasticsearch
