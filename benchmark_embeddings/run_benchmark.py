import requests
from elasticsearch import Elasticsearch
import json
from statistics import mean

# ------------------------------
# CONFIGURACIÓN
# ------------------------------
ES_HOSTS = [
    "https://192.199.1.59:9200",
    "https://192.199.1.60:9200",
    "https://192.199.1.61:9200"
]

ES_USER = "elastic"
ES_PASSWORD = "elastic"

API_ENDPOINTS = {
    "all-mpnet-base-v2": "http://192.199.1.61:8000/api/embed",
    "jhgan/ko-sroberta-multitask": "http://192.199.1.61:8000/api/embed2",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": "http://192.199.1.61:8000/api/embed3"
}

TIMEOUT = 30

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

TOP_K = 5

# ------------------------------
# Conexión a Elasticsearch
# ------------------------------
es = Elasticsearch(
    ES_HOSTS,
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=True,
    ca_certs="/home/g2/ELK/elasticsearch-9.2.1/config/certs/http_ca.crt"
)

# ------------------------------
# Funciones
# ------------------------------
def get_embedding(text, model_name):
    if model_name not in API_ENDPOINTS:
        raise ValueError(f"Modelo desconocido: {model_name}")
    
    url = API_ENDPOINTS[model_name]
    resp = requests.post(url, json={"text": text}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["embedding"]

def vector_search(query_vec, top_k=5):
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

# ------------------------------
# Benchmark
# ------------------------------
def run_benchmark():
    resultados = {}
    model_scores_summary = {}

    for model_name in API_ENDPOINTS.keys():
        print(f"\n--- Evaluando modelo: {model_name} ---")
        resultados[model_name] = {}
        all_scores = []  # <-- Guardamos todos los scores de este modelo

        for query in QUERIES:
            print(f"Query: {query}")
            try:
                query_vec = get_embedding(query, model_name)
                hits = vector_search(query_vec, top_k=TOP_K)
                resultados[model_name][query] = [
                    {"_id": h["_id"], "_score": h["_score"], "title": h["_source"].get("title")}
                    for h in hits
                ]
                # Agregar scores al resumen
                all_scores.extend([h["_score"] for h in hits])

            except Exception as e:
                print(f"Error en query '{query}' con modelo '{model_name}': {e}")

        # Calcular media del modelo
        if all_scores:
            model_scores_summary[model_name] = {
                "mean_score": mean(all_scores),
                "total_scores": len(all_scores)
            }
        else:
            model_scores_summary[model_name] = {
                "mean_score": None,
                "total_scores": 0
            }

    return resultados, model_scores_summary

# ------------------------------
# Ejecutar benchmark
# ------------------------------
if __name__ == "__main__":
    benchmark_results, model_scores_summary = run_benchmark()

    # Guardar resultados completos
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, ensure_ascii=False, indent=2)

    # Guardar medias de scores por modelo
    with open("model_scores_average.json", "w", encoding="utf-8") as f:
        json.dump(model_scores_summary, f, ensure_ascii=False, indent=2)

    print("\n✅ Benchmark completado. Resultados guardados en 'benchmark_results.json' y 'model_scores_average.json'")