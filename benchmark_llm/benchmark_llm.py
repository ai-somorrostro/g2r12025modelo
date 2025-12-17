import os
import time
import json
import pandas as pd
from openai import OpenAI
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from tqdm import tqdm
from colorama import Fore, Style, init

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()
init(autoreset=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
REFERER = "http://localhost:8501"

# Modelos a evaluar
MODELS_TO_TEST = [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-sonnet",
    "meta-llama/llama-3-70b-instruct",
    "meta-llama/llama-3-8b-instruct",
    "mistralai/mistral-large"
]

# Precios estimados ($ por 1M tokens) - Input / Output
PRICING = {
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "meta-llama/llama-3-70b-instruct": (0.70, 0.90),
    "meta-llama/llama-3-8b-instruct": (0.05, 0.10),
    "google/gemini-flash-1.5": (0.35, 1.05),
    "mistralai/mistral-large": (2.00, 6.00)
}

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={"HTTP-Referer": REFERER}
)

# --- FASE 1: OBTENCIÓN DE DATOS REALES (50 NOTICIAS) ---
def get_real_context():
    print(f"{Fore.CYAN}--- Conectando a Elasticsearch para obtener 50 noticias reales ---{Style.RESET_ALL}")
    
    mock_context = "[DATOS SIMULADOS POR FALLO DE CONEXIÓN]..." 
    
    try:
        es_url = os.getenv("ELASTIC_URL")
        es_key = os.getenv("ELASTIC_API_KEY")
        index_name = "noticias-2025.12.15" # el índice especifico que usaremos para el benchmark
        
        if not es_url or not es_key:
            return mock_context

        es = Elasticsearch(es_url, api_key=es_key, verify_certs=False, ssl_show_warn=False)
        
        # SOLICITAMOS 50 NOTICIAS
        resp = es.search(
            index=index_name,
            size=50, 
            query={"match_all": {}},
            _source=["title", "body", "date"]
        )
        
        hits = resp['hits']['hits']
        if not hits:
            print(f"{Fore.RED}No se encontraron hits en {index_name}.{Style.RESET_ALL}")
            return mock_context
            
        context_str = ""
        print(f"{Fore.GREEN}ÉXITO: Se descargaron {len(hits)} noticias reales.{Style.RESET_ALL}")
        
        for i, hit in enumerate(hits, 1):
            source = hit['_source']
            title = source.get('title', 'Sin título')
            # Recortamos a 250 caracteres para optimizar tokens pero mantener contexto
            body = source.get('body', '')[:250].replace("\n", " ") 
            date = source.get('date', '2025-12-15')
            context_str += f"[{i}] {date} | {title} | {body}...\n"
            
        return context_str

    except Exception as e:
        print(f"{Fore.RED}Error conectando: {e}{Style.RESET_ALL}")
        return mock_context

# Cargar contexto una sola vez
REAL_CONTEXT = get_real_context()

# --- FASE 2: DEFINICIÓN DE PRUEBAS ---
TEST_CASES = [
    {
        "name": "ROUTER (Intent JSON)",
        "prompt_template": """
        Eres un sistema de clasificación. HOY ES: 2025-12-16.
        Analiza: "{query}"
        Devuelve SOLO JSON: {{"topic": "string", "days": int}}.
        Reglas: "ayer"=1, "hoy"=0.
        """,
        "user_input": "Busca noticias sobre economía de ayer",
        "expected_type": "json"
    },
    {
        "name": "RAG (Summarization)",
        "prompt_template": f"""
        Eres un analista de noticias. Usa el siguiente contexto real:
        <context>
        {REAL_CONTEXT}
        </context>
        
        TAREA: Genera un resumen ejecutivo agrupando las noticias principales.
        NO inventes información.
        """,
        "user_input": "Hazme un resumen de las noticias más importantes de ayer.",
        "expected_type": "text"
    }
]

# --- FASE 3: FUNCIONES DE EJECUCIÓN ---
def run_benchmark_iteration(model, test_case):
    messages = [
        {"role": "system", "content": test_case["prompt_template"]},
        {"role": "user", "content": test_case["user_input"]}
    ]
    
    start_time = time.time()
    ttft = 0
    full_response = ""
    
    # Estimación de tokens de entrada
    tokens_in = len(test_case["prompt_template"]) // 4 + len(test_case["user_input"]) // 4 
    if "REAL_CONTEXT" in test_case["prompt_template"]:
        tokens_in += len(REAL_CONTEXT) // 4

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            stream=True
        )
        
        first_chunk = True
        for chunk in stream:
            if chunk.choices[0].delta.content:
                if first_chunk:
                    ttft = time.time() - start_time
                    first_chunk = False
                full_response += chunk.choices[0].delta.content
        
        total_time = time.time() - start_time
        tokens_out = len(full_response) // 4
        
        success = True
        if test_case["expected_type"] == "json":
            try:
                json.loads(full_response.replace("```json", "").replace("```", ""))
            except:
                success = False

        return {
            "ttft": ttft,
            "total_time": total_time,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "response": full_response,
            "success": success
        }
    except Exception as e:
        return {"error": str(e)}

def evaluate_quality(question, context, answer):
    try:
        judge_resp = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[{
                "role": "system", 
                "content": "Eres un juez estricto. Puntúa del 0 al 10 la calidad del resumen basándote en la fidelidad al contexto."
            }, {
                "role": "user",
                "content": f"CONTEXTO (Extracto): {context[:2000]}...\n\nRESUMEN GENERADO: {answer}\n\nPuntuación (solo número):"
            }]
        )
        score = judge_resp.choices[0].message.content.strip()
        return int(''.join(filter(str.isdigit, score)))
    except:
        return 5

# --- EJECUCIÓN PRINCIPAL ---
def main():
    print(f"\n{Fore.CYAN}=== INICIANDO BENCHMARK (50 Docs) ==={Style.RESET_ALL}")
    
    all_results = []
    
    for model in tqdm(MODELS_TO_TEST, desc="Evaluando Modelos"):
        model_results = {"Model": model}
        
        for test in TEST_CASES:
            res = run_benchmark_iteration(model, test)
            
            if "error" in res:
                print(f"\nError en {model}: {res['error']}")
                continue
                
            prefix = "Router" if test["expected_type"] == "json" else "RAG"
            
            # Métricas
            model_results[f"{prefix}_TTFT"] = round(res["ttft"], 3)
            p_in, p_out = PRICING.get(model, (0, 0))
            cost = (res["tokens_in"]/1e6 * p_in) + (res["tokens_out"]/1e6 * p_out)
            model_results[f"{prefix}_Cost"] = cost
            
            if test["expected_type"] == "json":
                model_results[f"{prefix}_Quality"] = 10 if res["success"] else 0
            else:
                score = evaluate_quality(test["user_input"], REAL_CONTEXT, res["response"])
                model_results[f"{prefix}_Quality"] = score
        
        total_cost = model_results.get("Router_Cost", 0) + model_results.get("RAG_Cost", 0)
        model_results["Total_Cost_1k_Runs"] = round(total_cost * 1000, 4)
        
        all_results.append(model_results)
        time.sleep(1) 

    # --- GUARDADO EN CARPETA ---
    df = pd.DataFrame(all_results)
    
    # Definir columnas finales
    final_cols = ["Model", "Router_TTFT", "Router_Quality", "RAG_TTFT", "RAG_Quality", "Total_Cost_1k_Runs"]
    for col in final_cols:
        if col not in df.columns: df[col] = 0
    
    df_final = df[final_cols].sort_values("RAG_Quality", ascending=False)
    
    print(f"\n{Fore.GREEN}=== RESULTADOS DEL BENCHMARK ==={Style.RESET_ALL}")
    print(df_final.to_string(index=False))
    
    # 1. Definir nombre de la carpeta
    output_folder = "csv_benchmark"
    
    # 2. Crear la carpeta si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"\nCarpeta creada: {output_folder}")
    
    # 3. Generar nombre de archivo con HORA (para no sobrescribir)
    timestamp = time.strftime('%Y%m%d_%H%M%S') # Ej: 20251216_143005
    csv_filename = f"benchmark_results_{timestamp}.csv"
    
    # 4. Ruta completa
    full_path = os.path.join(output_folder, csv_filename)
    
    # 5. Guardar
    df_final.to_csv(full_path, index=False)
    print(f"\nResultados guardados en: {Fore.YELLOW}{full_path}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()