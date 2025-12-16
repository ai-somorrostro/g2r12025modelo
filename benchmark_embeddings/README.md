# Benchmark de Modelos de Embeddings en Elasticsearch

Este proyecto permite evaluar múltiples modelos de embeddings para búsquedas semánticas en documentos indexados en Elasticsearch. Genera resultados detallados de los documentos más relevantes y calcula estadísticas de los 4 modelos probados.

---

## Modelos Probados

- **all-mpnet-base-v2**
- **jhgan/ko-sroberta-multitask**
- **paraphrase-multilingual-mpnet-base-v2**
- **multilingual-e5-base**

---

## Contenido

- `run_benchmark.py` – Script principal para ejecutar el benchmark.
- `benchmark_results.json` – Resultados de las búsquedas para cada modelo y query.
- `model_metric.json` – Resultados generales de cada modelo.

---

## Requisitos

- Python 3.8+
- Elasticsearch 7.x o 8.x
- Módulos Python:
  ```bash
  pip install requests elasticsearch
