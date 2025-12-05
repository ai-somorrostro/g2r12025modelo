import os
import json
import glob
import uuid
import re
import requests
from datetime import datetime, timedelta
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

# --- CONSTANTES ---
CHATS_DIR = "chats"
DEBUG_LOGS_DIR = "debug_logs"  
if not os.path.exists(CHATS_DIR): os.makedirs(CHATS_DIR)
if not os.path.exists(DEBUG_LOGS_DIR): os.makedirs(DEBUG_LOGS_DIR)

# --- CLASE DEBUG LOGGER ---
class DebugLogger:
    """Almacena información de debug de cada búsqueda"""
    
    def __init__(self):
        self.log_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs = []
        self.intent_data = {}
        self.search_data = {}
        self.results_data = {}
        
    def add_log(self, message, level="INFO"):
        """Añade un mensaje de log"""
        self.logs.append({
            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level": level,
            "message": message
        })
    
    def set_intent(self, user_query, llm_response, parsed_intent):
        """Guarda datos del análisis de intención"""
        self.intent_data = {
            "user_query": user_query,
            "llm_raw_response": llm_response,
            "parsed": parsed_intent
        }
    
    def set_search_params(self, topic, days, k, date_filter, search_type):
        """Guarda parámetros de búsqueda"""
        self.search_data = {
            "topic": topic,
            "days": days,
            "k": k,
            "date_filter": date_filter,
            "search_type": search_type
        }
    
    def set_results(self, hits, docs_returned, avg_score):
        """Guarda resultados de búsqueda"""
        self.results_data = {
            "total_hits": len(hits),
            "docs_returned": docs_returned,
            "avg_score": avg_score,
            "results": [
                {
                    "title": hit['_source'].get('title', 'Sin título')[:100],
                    "date": hit['_source'].get('date', 'N/A'),
                    "score": hit.get('_score', 0.0),
                    "url": hit['_source'].get('url', '#')
                }
                for hit in hits[:10]  # Guardar solo primeros 10
            ]
        }
    
    def save(self):
        """Guarda el log a disco"""
        log_data = {
            "log_id": self.log_id,
            "timestamp": self.timestamp,
            "intent": self.intent_data,
            "search": self.search_data,
            "results": self.results_data,
            "logs": self.logs
        }
        
        filepath = os.path.join(DEBUG_LOGS_DIR, f"{self.log_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return self.log_id
    
    def get_summary(self):
        """Retorna un resumen del debug para mostrar en UI"""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp,
            "query": self.intent_data.get("user_query", "N/A"),
            "topic": self.search_data.get("topic", "N/A"),
            "search_type": self.search_data.get("search_type", "N/A"),
            "results_count": self.results_data.get("docs_returned", 0),
            "avg_score": self.results_data.get("avg_score", 0.0)
        }

# --- FUNCIONES PARA GESTIONAR LOGS ---
def get_all_debug_logs():
    """Obtiene todos los logs de debug ordenados por fecha"""
    files = glob.glob(f"{DEBUG_LOGS_DIR}/*.json")
    files.sort(key=os.path.getmtime, reverse=True)
    logs = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                logs.append(json.load(file))
        except:
            pass
    return logs

def load_debug_log(log_id):
    """Carga un log específico por su ID"""
    files = glob.glob(f"{DEBUG_LOGS_DIR}/{log_id}_*.json")
    if files:
        with open(files[0], "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def delete_debug_log(log_id):
    """Elimina un log específico"""
    files = glob.glob(f"{DEBUG_LOGS_DIR}/{log_id}_*.json")
    for f in files:
        if os.path.exists(f):
            os.remove(f)

def clear_old_debug_logs(days=7):
    """Elimina logs más antiguos de X días"""
    cutoff = datetime.now() - timedelta(days=days)
    files = glob.glob(f"{DEBUG_LOGS_DIR}/*.json")
    deleted = 0
    for f in files:
        if datetime.fromtimestamp(os.path.getmtime(f)) < cutoff:
            os.remove(f)
            deleted += 1
    return deleted

# --- CLASE PARA API DE EMBEDDINGS REMOTA ---
class RemoteEmbeddings(Embeddings):
    def __init__(self, api_url):
        self.api_url = api_url

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        try:
            payload = {"text": text}
            response = requests.post(self.api_url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list): return data
            if "embedding" in data: return data["embedding"]
            if "vector" in data: return data["vector"]
            return list(data.values())[0]
        except Exception as e:
            print(f"Error en API Embeddings: {e}")
            return []

# --- CONFIGURACIÓN ELASTICSEARCH ---
@st.cache_resource
def get_elastic_client():
    try:
        es_url = os.getenv("ELASTIC_URL")
        es_api_key = os.getenv("ELASTIC_API_KEY")
        es_cert = os.getenv("ELASTIC_CERT_PATH")
        verify_ssl = os.getenv("ELASTIC_VERIFY_SSL") == "True"

        if not es_api_key:
            st.error("Falta ELASTIC_API_KEY en .env")
            return None

        if verify_ssl and os.path.exists(es_cert):
            return Elasticsearch(es_url, api_key=es_api_key, ca_certs=es_cert)
        else:
            return Elasticsearch(es_url, api_key=es_api_key, verify_certs=False, ssl_show_warn=False)
    except Exception as e:
        st.error(f"Error Elastic: {e}")
        return None

# --- CARGA DEL MODELO DE EMBEDDINGS (REMOTO) ---
@st.cache_resource
def load_embedding_model():
    api_url = os.getenv("EMBEDDING_API_URL")
    if not api_url:
        st.error("Falta EMBEDDING_API_URL en .env")
        return None
    return RemoteEmbeddings(api_url)

# --- MODELO LLM ---
def load_llm(model_name, temp):
    return ChatOpenAI(
        model_name=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temp,
        default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "NewsAI Lab"}
    )

# --- ROUTER SEMÁNTICO ---
def analyze_intent(user_query, llm_instance, debug_logger=None):
    """
    Analiza la intención del usuario y extrae tema + filtro temporal.
    
    Args:
        user_query: Consulta del usuario
        llm_instance: Instancia del modelo LLM
        debug_logger: Logger opcional para debug
    
    Returns:
        dict: {"topic": str, "days": int}
    """
    greetings = ["hola", "buenos dias", "buenas", "que tal", "hi", "hello", "saludos"]
    clean_q = user_query.lower().strip().replace("¿", "").replace("?", "").replace("!", "").replace("¡", "")
    
    # Detectar saludo
    if clean_q in greetings:
        result = {"topic": "SALUDO", "days": -1}
        if debug_logger:
            debug_logger.add_log(f"Detectado saludo: '{clean_q}'", "INFO")
        print(f"Intent parseado → Topic: 'SALUDO' | Days: -1")
        return result

    # Detectar intentos prohibidos
    forbidden_keywords = ["codigo", "code", "script", "python", "css", "html", "java", "calcula", "suma", "resta", "multiplica", "poema", "cuento", "chiste"]
    if any(w in clean_q for w in forbidden_keywords):
        result = {"topic": "INTENTO_PROHIBIDO", "days": -1}
        if debug_logger:
            debug_logger.add_log(f"Detectado intento prohibido - palabra clave encontrada", "WARNING")
        print(f"Intent parseado → Topic: 'INTENTO_PROHIBIDO' | Days: -1")
        return result

    today_str = datetime.now().strftime("%Y-%m-%d")
    
    system_prompt = f"""
    Eres un clasificador de intenciones para un buscador de noticias.
    HOY ES: {today_str}
    
    Analiza la consulta del usuario y devuelve SOLO un JSON con:
    {{
      "topic": "tema principal (ej: 'política', 'deportes', 'tecnología'). Si no hay tema específico, pon 'general'",
      "days": "número de días hacia atrás (0=hoy, 1=ayer, 7=última semana, 30=último mes, -1=sin filtro temporal)"
    }}
    
    REGLAS:
    - Si dice "ayer", days=1
    - Si dice "última semana", days=7
    - Si dice "hoy" o "últimas noticias", days=0
    - Si no menciona tiempo, days=-1
    - Para "noticias de tecnología de ayer", topic="tecnología", days=1
    
    Responde SOLO el JSON, sin texto adicional.
    """
    
    try:
        # Log inicio de análisis
        if debug_logger:
            debug_logger.add_log(f"Iniciando análisis de intención para: '{user_query}'", "INFO")
        
        print(f"Analizando intención de: '{user_query}'")
        
        # Invocar LLM
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "{query}")])
        chain = prompt | llm_instance | StrOutputParser()
        response = chain.invoke({"query": user_query}).strip().replace("```json", "").replace("```", "")
        
        # Log respuesta cruda
        print(f"Respuesta LLM Router (raw): {response}")
        if debug_logger:
            debug_logger.add_log(f"Respuesta LLM Router (raw): {response}", "DEBUG")
        
        # Parsear JSON
        result = json.loads(response)
        
        # Log resultado parseado
        topic = result.get('topic', 'N/A')
        days = result.get('days', -1)
        print(f"Intent parseado → Topic: '{topic}' | Days: {days}")
        
        if debug_logger:
            debug_logger.add_log(f"Intent parseado correctamente → Topic: '{topic}' | Days: {days}", "SUCCESS")
            debug_logger.set_intent(user_query, response, result)
        
        return result
        
    except json.JSONDecodeError as e:
        error_msg = f"Error al parsear JSON del LLM: {e}. Respuesta recibida: {response}"
        print(f"{error_msg}")
        if debug_logger:
            debug_logger.add_log(error_msg, "ERROR")
        
        # Fallback: usar query completa como topic
        return {"topic": user_query, "days": -1}
        
    except Exception as e:
        error_msg = f"Error general en analyze_intent: {e}"
        print(f"{error_msg}")
        if debug_logger:
            debug_logger.add_log(error_msg, "ERROR")
        
        return {"topic": user_query, "days": -1}


def clean_response(text):
    """Limpia caracteres no deseados de la respuesta del LLM"""
    patterns = [r"^}\]\);", r"^HTMLElement\s*\(.*?\)", r"^```json", r"^```"]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE).strip()
    return text

# --- BÚSQUEDA HÍBRIDA ---
def search_elastic(user_query, llm_instance, k=5, debug_logger=None):
    # Crear logger si no se proporciona
    if debug_logger is None:
        debug_logger = DebugLogger()
    
    debug_logger.add_log("=== INICIO DE BÚSQUEDA ===", "INFO")
    
    es_client = get_elastic_client()
    if not es_client:
        debug_logger.add_log("Cliente Elasticsearch no disponible", "ERROR")
        return []

    intent = analyze_intent(user_query, llm_instance, debug_logger)
    topic = intent.get("topic", "general")
    days = intent.get("days", -1)
    
    debug_logger.add_log(f"Query Usuario: '{user_query}'", "INFO")
    debug_logger.add_log(f"Topic extraído: '{topic}' | Days: {days}", "INFO")
    
    if topic in ["SALUDO", "INTENTO_PROHIBIDO"]:
        debug_logger.add_log("Búsqueda bloqueada por tipo de intent", "WARNING")
        debug_logger.save()
        return []

    search_kwargs = {
        "index": os.getenv("ELASTIC_INDEX"),
        "size": k,
        "_source": ["title", "body", "url", "date"],
        "ignore_unavailable": True,
        "allow_no_indices": True
    }

    # Construir filtro de fecha
    date_filter = None
    if days >= 0:
        cutoff = f"now-{days}d/d"
        date_filter = {"range": {"date": {"gte": cutoff}}}
        debug_logger.add_log(f"Filtro temporal aplicado: {cutoff} (últimos {days} días)", "INFO")
    else:
        debug_logger.add_log("Sin filtro temporal (búsqueda en todo el histórico)", "INFO")

    hits = []
    search_type = "UNKNOWN"
    
    # Solo usar match_all si NO hay tema específico
    if topic == "general" or not topic:
        search_type = "MATCH_ALL"
        debug_logger.add_log("Ejecutando búsqueda MATCH_ALL (sin tema específico)", "INFO")
        
        query_body = {"match_all": {}}
        if date_filter:
            query_body = {"bool": {"filter": date_filter}}
        
        try:
            response = es_client.search(
                query=query_body,
                sort=[{"date": {"order": "desc"}}],
                **search_kwargs
            )
            hits = response['hits']['hits']
            debug_logger.add_log(f"Match_all devolvió {len(hits)} resultados", "SUCCESS")
            
            if hits:
                for i, hit in enumerate(hits[:3], 1):
                    title = hit['_source'].get('title', 'Sin título')[:60]
                    debug_logger.add_log(f"  {i}. {title}", "DEBUG")
            
        except Exception as e:
            debug_logger.add_log(f"Error en match_all: {e}", "ERROR")
            debug_logger.save()
            return []
            
    else:
        # Búsqueda vectorial con tema específico
        try:
            search_type = "VECTOR_KNN"
            debug_logger.add_log(f"Generando embedding para: '{topic}'", "INFO")
            
            embedding_model = load_embedding_model()
            vector = embedding_model.embed_query(topic)
            
            if not vector:
                raise ValueError("Vector vacío")
            
            debug_logger.add_log(f"Vector generado correctamente (dimensión: {len(vector)})", "SUCCESS")

            num_candidates = max(1000, k * 20)
            knn_query = {
                "field": "embedding",
                "query_vector": vector,
                "k": k,
                "num_candidates": num_candidates
            }
            if date_filter:
                knn_query["filter"] = date_filter
            
            debug_logger.add_log(f"Ejecutando búsqueda KNN: k={k}, candidates={num_candidates}, filtro_fecha={'Sí' if date_filter else 'No'}", "INFO")
            
            response = es_client.search(knn=knn_query, **search_kwargs)
            hits = response['hits']['hits']
            
            debug_logger.add_log(f"KNN devolvió {len(hits)} resultados", "SUCCESS")
            
            if hits:
                debug_logger.add_log("Resultados vectoriales (con scores):", "DEBUG")
                for i, hit in enumerate(hits[:3], 1):
                    score = hit.get('_score', 0.0)
                    title = hit['_source'].get('title', 'Sin título')[:60]
                    debug_logger.add_log(f"  {i}. [Score: {score:.4f}] {title}", "DEBUG")
            
            if not hits:
                debug_logger.add_log(f"Sin resultados vectoriales para '{topic}'. Forzando fallback a texto...", "WARNING")
                raise ValueError("Forzar fallback")
                
        except Exception as e:
            search_type = "TEXT_BM25"
            debug_logger.add_log(f"Fallback a búsqueda por TEXTO: {e}", "WARNING")
            
            q_body = {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": topic,
                            "fields": ["title", "body"],
                            "type": "best_fields"
                        }
                    }
                }
            }
            if date_filter:
                q_body["bool"]["filter"] = date_filter
            
            debug_logger.add_log(f"Ejecutando multi_match en campos: title^3, body", "INFO")
            
            try:
                response = es_client.search(query=q_body, **search_kwargs)
                hits = response['hits']['hits']
                debug_logger.add_log(f"Búsqueda por texto devolvió {len(hits)} resultados", "SUCCESS")
                
                if hits:
                    debug_logger.add_log("Resultados de texto:", "DEBUG")
                    for i, hit in enumerate(hits[:3], 1):
                        title = hit['_source'].get('title', 'Sin título')[:60]
                        debug_logger.add_log(f"  {i}. {title}", "DEBUG")
                        
            except Exception as text_error:
                debug_logger.add_log(f"Error en búsqueda por texto: {text_error}", "ERROR")
                debug_logger.save()
                return []

    # Procesar resultados
    docs = []
    for hit in hits:
        s = hit['_source']
        docs.append({
            "content": s.get('body',''),
            "title": s.get('title',''),
            "url": s.get('url','#'),
            "date": s.get('date','Sin fecha'),
            "score": hit.get('_score', 0.0)
        })
    
    # Calcular score promedio
    avg_score = 0.0
    if docs:
        scores = [doc['score'] for doc in docs if doc['score'] > 0]
        if scores:
            avg_score = sum(scores) / len(scores)
    
    debug_logger.add_log(f"TOTAL DOCUMENTOS DEVUELTOS: {len(docs)}", "SUCCESS")
    debug_logger.add_log(f"Score promedio: {avg_score:.6f}", "INFO")
    debug_logger.add_log("=== FIN DE BÚSQUEDA ===", "INFO")
    
    # Guardar datos finales y persistir
    debug_logger.set_search_params(topic, days, k, date_filter, search_type)
    debug_logger.set_results(hits, len(docs), avg_score)
    debug_logger.save()
    
    return docs, debug_logger  # IMPORTANTE: Ahora retorna también el logger

# --- GESTIÓN DE CHATS ---
def get_all_chats():
    files = glob.glob(f"{CHATS_DIR}/*.json")
    files.sort(key=os.path.getmtime, reverse=True)
    chats = []
    for f in files:
        with open(f, "r") as file:
            try: chats.append(json.load(file))
            except: pass
    return chats

def create_new_chat_data(): return {"id": str(uuid.uuid4()), "title": "Nuevo Chat", "created_at": str(datetime.now()), "messages": []}
def save_chat_to_disk(chat_data):
    path = os.path.join(CHATS_DIR, f"{chat_data['id']}.json")
    with open(path, "w") as f: json.dump(chat_data, f, indent=4)
def delete_chat_from_disk(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(path): os.remove(path)
def load_chat_from_disk(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f: return json.load(f)
    return None

# --- SYSTEM PROMPT (PERMISO PARA PENSAR) ---
def get_rag_chain(llm_instance):
    template = """
    ERES: Un asistente de noticias profesional y analítico.
    FECHA ACTUAL: Diciembre 2025.

    OBJETIVO: Informar al usuario utilizando los datos proporcionados como base factual, pero aplicando tu capacidad de análisis y síntesis para generar respuestas útiles y bien estructuradas.

    TUS CAPACIDADES PERMITIDAS:
    1. **Sintetizar:** Puedes unir información de varias noticias para crear un resumen coherente.
    2. **Estructurar:** Usa listas, negritas y párrafos para hacer la información legible.
    3. **Contextualizar:** Si una noticia requiere explicación para ser entendida, usa tu capacidad lógica para explicarla basándote en los hechos del texto.
    4. **Conversar:** Mantén un tono natural, fluido y educado.

    PROHIBICIONES ESTRICTAS:
    1. **Invenciones (Alucinaciones):** NO inventes nombres, fechas o eventos que no aparezcan en el <context>. Si el dato no está, no existe.
    2. **Temas Ajenos:** NO generes código, NO hagas cálculos matemáticos complejos, NO escribas literatura creativa.
    3. **Idioma:** Responde SIEMPRE en ESPAÑOL.

    INSTRUCCIONES DE RESPUESTA:
    - Usa la información de <context> como tu FUENTE DE DATOS.
    - Si la información solicitada NO está en el contexto, di claramente: "No dispongo de información sobre ese tema en mi base de datos actual."
    - Si es un saludo, responde amablemente sin buscar noticias.

    <context>
    {context}
    </context>

    PREGUNTA DEL USUARIO:
    {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    return prompt | llm_instance | StrOutputParser()