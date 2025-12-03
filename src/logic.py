import os
import json
import glob
import uuid
import re
from datetime import datetime
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Cargar entorno al importar este módulo
load_dotenv()

# --- CONSTANTES ---
CHATS_DIR = "chats"
if not os.path.exists(CHATS_DIR):
    os.makedirs(CHATS_DIR)

# --- GESTIÓN DE ELASTICSEARCH ---
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

# --- GESTIÓN DE MODELOS LLM ---
def load_llm(model_name, temp):
    return ChatOpenAI(
        model_name=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temp,
        default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "NewsAI Lab"}
    )

# --- PROCESAMIENTO NLP ---
def optimize_query(user_query, llm_instance):
    if len(user_query.split()) < 4: return user_query
    
    system_prompt = """Eres un experto en búsqueda. 
    1. Elimina palabras vacías (dime, sobre, la, información).
    2. CORRIGE ortografía (Karlos -> Carlos).
    3. Devuelve SOLO las palabras clave."""
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "{query}")])
    chain = prompt | llm_instance | StrOutputParser()
    return chain.invoke({"query": user_query}).strip()

def clean_response(text):
    patterns = [r"^}\]\);", r"^HTMLElement\s*\(.*?\)", r"^```json", r"^```"]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE).strip()
    return text

# --- BÚSQUEDA EN ELASTIC ---
def search_elastic(query_text, k=5):
    es_client = get_elastic_client()
    if not es_client: return []
    
    generic_keywords = ["actuales", "actualidad", "hoy", "últimas", "noticias", "tienes", "pasa", "resumen", "dime algo", "novedades"]
    is_generic = any(word in query_text.lower() for word in generic_keywords)
    
    if is_generic:
        query_body = {"match_all": {}}
        sort_body = [{"@timestamp": {"order": "desc"}}]
    else:
        query_body = {
            "multi_match": {
                "query": query_text,
                "fields": ["title^3", "body", "author"],
                "fuzziness": "AUTO",
                "operator": "OR",
                "minimum_should_match": "60%"
            }
        }
        sort_body = []

    response = es_client.search(
        index=os.getenv("ELASTIC_INDEX"),
        query=query_body,
        sort=sort_body,
        size=k,
        _source=["title", "body", "url", "date"]
    )
    
    docs = []
    for hit in response['hits']['hits']:
        s = hit['_source']
        docs.append({
            "content": s.get('body',''), 
            "title": s.get('title',''), 
            "url": s.get('url','#'), 
            "date": s.get('date','')
        })
    return docs

# --- GESTIÓN DE CHATS (PERSISTENCIA) ---
def get_all_chats():
    files = glob.glob(f"{CHATS_DIR}/*.json")
    files.sort(key=os.path.getmtime, reverse=True)
    chats = []
    for f in files:
        with open(f, "r") as file:
            try: chats.append(json.load(file))
            except: pass
    return chats

def create_new_chat():
    return {
        "id": str(uuid.uuid4()),
        "title": "Nuevo Chat",
        "created_at": str(datetime.now()),
        "messages": []
    }

def save_chat_to_disk(chat_data):
    path = os.path.join(CHATS_DIR, f"{chat_data['id']}.json")
    with open(path, "w") as f:
        json.dump(chat_data, f, indent=4)

def delete_chat_from_disk(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        os.remove(path)

def load_chat_from_disk(chat_id):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

# --- SYSTEM PROMPT ---
def get_rag_chain(llm_instance):
    template = """
    SITUACIÓN: Eres un periodista de investigación y asistente de noticias.
    FECHA ACTUAL: Diciembre 2025.

    INSTRUCCIONES DE COMPORTAMIENTO:
    1. IDIOMA: Si el usuario te habla en español, RESPONDE EN ESPAÑOL. Solo rechaza si te hablan explícitamente en otro idioma.
    2. FUENTE DE VERDAD: Considera las noticias proporcionadas en <context> como la verdad absoluta.
    3. PROACTIVIDAD: Si la respuesta exacta no está, di "No tengo ese dato exacto, pero tengo noticias sobre..." y lista lo que haya en el contexto.
    4. PROHIBIDO CÓDIGO: No generes código informático.

    <context>
    {context}
    </context>

    PREGUNTA DEL USUARIO:
    {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    return prompt | llm_instance | StrOutputParser()