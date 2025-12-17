# Benchmark de Modelos de LLM

Hemos decidido evaluar distintos modelos de LLM para escoger la opción más adecuada a nuestras necesidades. Por ello conectandose a Elasticsearch directamente, cogiendo nuestros propios datos y mandando 50 queries sobre esos datos, hemos evaluado de manera correcta cual modelo seria mas efectivo. 

Hemos evaluado 7 modelos diferentes. 

---

## Modelos Probados

- **gpt-4o**
- **gpt-4o-mini**
- **paraphrase-multilingual-mpnet-base-v2**
- **llama-3-70b-instruct**
- **llama-3-8b-instruct**
- **mistral-large**
- **gemini**

---

## Contenido

- `benchmark_llm.py` – Script principal que se utiliza para ejecutar el benchmark..
- `csv_benchmark` – Carpeta donde se guarda el csv de los resultados, cada vez que se ejecute se añadira un nuevo csv, se puede cambiar el modelo o parametro y será de utilidad para probar distintos modelos.


---

## Requisitos

- Python 3.8+
- Elasticsearch 7.x o 8.x
- Módulos Python:
  ```bash
  pip install requests elasticsearch
