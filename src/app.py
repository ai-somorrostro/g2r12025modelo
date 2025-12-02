import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN UI ---
st.set_page_config(page_title="NewsAI Elastic", page_icon="⚖️", layout="wide")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stChatMessage { background-color: #000; color: #fff; border: 1px solid #333; border-radius: 15px; }
    [data-testid="stSidebar"] { background-color: #000; color: #fff; }
    /* Ajuste para que los textos del sidebar sean legibles */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #fff !important; }
    .main-header { background-color: #383838; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #2e86de; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

# --- CLIENTE ELASTIC ---
@st.cache_resource
def get_elastic_client():
    try:
        es_url = os.getenv("ELASTIC_URL")
        es_user = os.getenv("ELASTIC_USER")
        es_pass = os.getenv("ELASTIC_PASSWORD")
        es_cert = os.getenv("ELASTIC_CERT_PATH")
        verify_ssl = os.getenv("ELASTIC_VERIFY_SSL") == "True"

        if verify_ssl and os.path.exists(es_cert):
            return Elasticsearch(es_url, basic_auth=(es_user, es_pass), ca_certs=es_cert)
        else:
            return Elasticsearch(es_url, basic_auth=(es_user, es_pass), verify_certs=False, ssl_show_warn=False)
    except Exception as e:
        st.error(f"Error Elastic: {e}")
        return None

es_client = get_elastic_client()

# --- MODELO LLM ---
@st.cache_resource
def load_llm():
    return ChatOpenAI(
        model_name="openai/gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.0
    )

llm = load_llm()

# --- OPTIMIZADOR DE BÚSQUEDA (NLP) ---
def optimize_query(user_query):
    """Limpieza de consulta usando IA"""
    system_prompt = """
    Eres un experto en motores de búsqueda. Tu tarea es optimizar la consulta del usuario.
    1. Elimina palabras irrelevantes (dime, búscame, noticias, sobre).
    2. CORRIGE errores ortográficos (ej: "Karlos" -> "Carlos").
    3. Devuelve SOLO las palabras clave corregidas.
    """
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "{query}")])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"query": user_query}).strip()

# --- FUNCIÓN DE BÚSQUEDA ---
def search_elastic(query_text, k=5):
    if not es_client: return []
    
    response = es_client.search(
        index=os.getenv("ELASTIC_INDEX"),
        query={
            "multi_match": {
                "query": query_text,
                "fields": ["title^3", "body", "author"],
                "fuzziness": "AUTO",
                "operator": "OR",
                "minimum_should_match": "75%"
            }
        },
        size=k,
        _source=["title", "body", "url", "date"]
    )
    
    docs = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        docs.append({
            "content": source.get('body', ''),
            "title": source.get('title', 'Sin título'),
            "url": source.get('url', '#'),
            "date": source.get('date', 'N/A'),
            "score": hit.get('_score', 0)
        })
    return docs

# --- SIDEBAR (CON AVISO LEGAL RA6) ---
with st.sidebar:
    st.title("⚡ Panel de Control")
    if es_client:
        st.success("🟢 Sistema Online")
    
    k_val = st.slider("Noticias a leer", 3, 10, 5)
    debug_mode = st.checkbox("Modo Debug", value=True)
    
    if st.button("Limpiar Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    # --- AQUÍ ESTÁ EL BLOQUE LEGAL (RA6) ---
    with st.expander("Aviso Legal y Privacidad", expanded=False):
        st.markdown("""
        **1. Privacidad de Datos:**
        Este sistema procesa sus consultas de forma anónima. No se almacenan datos personales ni historiales de conversación en servidores persistentes.
        
        **2. Limitación de Responsabilidad:**
        Las respuestas son generadas por Inteligencia Artificial (GPT-4o) basada en noticias. Pueden contener errores o alucinaciones. Verifique siempre la fuente original.
        
        **3. Licencia de Uso:**
        Software desarrollado con fines académicos. Código liberado bajo licencia MIT.
        """)
    # ---------------------------------------

# --- LÓGICA RAG ---
template = """
SITUACIÓN: Eres un periodista de investigación.
FECHA: Diciembre 2025.
FUENTE: Únicamente las noticias proporcionadas abajo.

INSTRUCCIONES:
1. Responde a la pregunta del usuario basándote SOLO en el CONTEXTO.
2. Si la respuesta no está en las noticias, di: "No dispongo de información sobre ese tema en mi base de datos actual."
3. Cita siempre la fuente (URL) al final.

CONTEXTO:
{context}

PREGUNTA:
{question}
"""
prompt = ChatPromptTemplate.from_template(template)

# --- UI CHAT ---
st.markdown('<div class="main-header"><h1>📰 NewsAI Elastic</h1><p>Búsqueda Inteligente con NLP</p></div>', unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if q := st.chat_input("Busca las noticias que mas te interesen..."):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"): st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("Procesando consulta..."):
            
            optimized_q = optimize_query(q)
            results = search_elastic(optimized_q, k=k_val)
            
            if debug_mode:
                with st.expander("Debug Info"):
                    st.markdown(f"**Query NLP:** `{optimized_q}`")
                    st.markdown(f"**Hits:** {len(results)}")

            ctx = ""
            html_sources = ""
            
            for i, doc in enumerate(results):
                ctx += f"NOTICIA {i+1}: {doc['content'][:4000]}\nFUENTE: {doc['url']}\n\n"
                html_sources += f"<div><strong>{doc['title']}</strong><br><span style='color:grey'>{doc['date']}</span> | <a href='{doc['url']}'>Link</a></div><hr>"
            
            if not ctx:
                resp = f"No he encontrado noticias sobre '{optimized_q}' en la base de datos."
            else:
                chain = prompt | llm | StrOutputParser()
                resp = chain.invoke({"context": ctx, "question": q})
            
            st.markdown(resp)
            if ctx:
                with st.expander("Fuentes Consultadas"): st.markdown(html_sources, unsafe_allow_html=True)
                
    st.session_state.messages.append({"role": "assistant", "content": resp})