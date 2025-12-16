import requests
from elasticsearch import Elasticsearch
import json
from statistics import mean
from itertools import islice
import time

# ====================== CONFIGURACIÓN ======================

ES_HOSTS = [
    "https://192.199.1.59:9200",
    "https://192.199.1.60:9200",
    "https://192.199.1.61:9200",
]

ES_USER = "elastic"
ES_PASSWORD = "elastic"

API_ENDPOINTS = {
    "all-mpnet-base-v2": "http://192.199.1.61:8000/api/embed",
    "jhgan/ko-sroberta-multitask": "http://192.199.1.61:8000/api/embed2",
    "paraphrase-multilingual-mpnet-base-v2": "http://192.199.1.61:8000/api/embed3",
    "multilingual-e5-base": "http://192.199.1.61:8000/api/embed4",
}

TIMEOUT = 30
TOP_K = 5

QUERIES = [
    "Noticias sobre política",
    "Fútbol hoy",
    "Clima en Madrid",
    "Tecnología e innovación",
    "Salud y medicina",
    "Que ha pasado con la peste porcina",
    "Quien es Pedro Sanchez",
    "Últimas noticias de economía",
    "Resultados del FC Barcelona",
    "En que posiciones juega Eric Garcia",
    "Noticias sobre el cambio climático",
    "Últimas noticias internacionales",
    "Eventos deportivos esta semana",
    "Consejos de salud mental",
    "Vacunas COVID-19 últimas noticias",
    "Noticias sobre inteligencia artificial",
    "Últimas tendencias en criptomonedas",
    "Resultados de la lotería nacional",
    "Noticias sobre educación en España",
    "Pronóstico del tiempo para Barcelona",
    "Noticias de cine y estrenos",
    "Actualidad sobre la UEFA Champions League",
    "Noticias sobre contaminación del aire",
    "Últimos descubrimientos científicos",
    "Noticias sobre energías renovables",
    "Actualidad sobre elecciones locales",
    "Últimas noticias sobre transporte público",
    "Consejos de alimentación saludable",
    "Noticias sobre inflación en Europa",
    "Eventos culturales en Madrid",
    "Últimas noticias sobre economía digital",
    "Resultados deportivos del fin de semana",
    "Noticias sobre tecnología móvil",
    "Actualidad sobre el Parlamento Europeo",
    "Noticias sobre seguridad cibernética",
    "Últimas novedades en medicina",
    "Noticias sobre fauna y medio ambiente",
    "Resultados de partidos de fútbol recientes",
    "Noticias sobre exploración espacial",
    "Últimas noticias sobre conflictos internacionales",
    "Noticias sobre música y conciertos"
]

# ====================== CONEXIÓN ELASTIC ======================

es = Elasticsearch(
    ES_HOSTS,
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=True,
    ca_certs="/home/g2/ELK/elasticsearch-9.2.1/config/certs/http_ca.crt"
)

# ====================== FUNCIONES ======================

def get_embedding(text: str, url: str):
    resp = requests.post(url, json={"text": text}, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    embedding = data["embedding"]
    ram_used = data.get("ram_used_mb")
    return embedding, ram_used

def measure_api_metrics(url: str, queries, model_name: str):
    metrics = {}
    print(f"\n📌 Iniciando medición de API para modelo '{model_name}'")

    # Tiempo de carga (primera llamada)
    print(f"⏱️  Cargando modelo (primera query): '{queries[0]}'")
    start_load = time.time()
    _, ram_used = get_embedding(queries[0], url)
    metrics["load_time_sec"] = time.time() - start_load
    metrics["ram_used_mb"] = ram_used
    print(f"✅ Modelo cargado en {metrics['load_time_sec']:.2f} seg, RAM usada: {ram_used:.2f} MB")

    # Batch encoding 100 queries
    batch = list(islice(queries * 5, 100))
    print(f"⏱️  Iniciando batch encoding de las queries para modelo '{model_name}'")
    start_batch = time.time()
    for i, q in enumerate(batch, 1):
        if i % 10 == 0:
            print(f"    Procesadas {i} queries del batch")
        get_embedding(q, url)
    metrics["batch_encoding_100_sec"] = time.time() - start_batch
    print(f"✅ Batch encoding completado en {metrics['batch_encoding_100_sec']:.2f} seg")

    return metrics

def vector_search(query_vec, top_k=TOP_K):
    body = {
        "size": top_k,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vec}
                }
            }
        }
    }
    resp = es.search(index="noticias-*", body=body)
    return resp["hits"]["hits"]

def format_search_results(hits):
    return [
        {"_id": h["_id"], "_score": h["_score"], "title": h["_source"].get("title")}
        for h in hits
    ]

def process_query(query, url, all_scores, model_name):
    try:
        print(f"🔹 Procesando query '{query}' en modelo '{model_name}'")
        embedding, _ = get_embedding(query, url)
        hits = vector_search(embedding, top_k=TOP_K)
        results = format_search_results(hits)
        scores = [h["_score"] for h in hits]
        all_scores.extend(scores)
        return results, all_scores
    except Exception as e:
        print(f"❌ Error en query '{query}' en {model_name}: {e}")
        return None, all_scores

def evaluate_model(url, queries, model_name):
    model_results = {}
    all_scores = []
    for query in queries:
        results, all_scores = process_query(query, url, all_scores, model_name)
        if results is not None:
            model_results[query] = results
    return model_results, all_scores

def calculate_model_summary(all_scores):
    if all_scores:
        return {"mean_score": mean(all_scores)}
    return {"mean_score": None}

# ====================== EJECUCIÓN ======================

if __name__ == "__main__":
    benchmark_results = {}
    model_metrics = {}

    for model_name, url in API_ENDPOINTS.items():
        # Métricas API + RAM
        metrics = measure_api_metrics(url, QUERIES, model_name)

        # Búsqueda vectorial y scores
        results, all_scores = evaluate_model(url, QUERIES, model_name)
        benchmark_results[model_name] = results

        # Scores promedio
        summary_scores = calculate_model_summary(all_scores)

        # Fusionar todo en un solo dict por modelo
        model_metrics[model_name] = {**summary_scores, **metrics}

    # Guardar resultados completos
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, ensure_ascii=False, indent=2)

    # Guardar métricas fusionadas
    with open("model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(model_metrics, f, ensure_ascii=False, indent=2)

    print("\n✅ Benchmark completado. Resultados guardados en:")
    print("- 'benchmark_results.json' (detalles de búsqueda)")
    print("- 'model_metrics.json' (scores promedio + tiempos + RAM)")