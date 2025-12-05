import streamlit as st
import logic

# --- CONFIGURACIÓN UI ---
st.set_page_config(page_title="AI Noticias Studio", page_icon="⚡", layout="wide")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stChatMessage { background-color: #000; color: #fff; border: 1px solid #333; border-radius: 15px; }
    [data-testid="stSidebar"] { background-color: #000; color: #fff; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #fff !important; }
    .main-header { background-color: #383838; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #7d3c98; margin-bottom: 2rem;}
    .chat-btn { width: 100%; text-align: left; margin-bottom: 5px; }
    .source-card { background-color: #2d2d2d; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #4ecdc4; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADO ---
if "current_chat" not in st.session_state:
    existing = logic.get_all_chats()
    if existing:
        st.session_state.current_chat = existing[0]
    else:
        st.session_state.current_chat = logic.create_new_chat_data()
        logic.save_chat_to_disk(st.session_state.current_chat)

# --- SIDEBAR ---
with st.sidebar:
    st.title("AI Studio")
    
    st.markdown("---")
    # Botón para mostrar/ocultar panel de debug
    if st.button("Ver Logs de Debug", use_container_width=True):
        st.session_state.show_debug_panel = not st.session_state.get("show_debug_panel", False)    

    if st.button("Nuevo Chat", use_container_width=True):
        st.session_state.current_chat = logic.create_new_chat_data()
        logic.save_chat_to_disk(st.session_state.current_chat)
        st.rerun()

    # --- PANEL DE DEBUG ---
    if st.session_state.get("show_debug_panel", False):
        st.markdown("---")
        st.subheader("Historial de Debug")
        
        if st.button("Limpiar logs >7 días"):
            deleted = logic.clear_old_debug_logs(days=7)
            st.success(f"{deleted} logs eliminados")
    
        all_logs = logic.get_all_debug_logs()
        
        if not all_logs:
            st.info("No hay logs de debug disponibles")
        else:
            for log in all_logs[:10]:
                with st.expander(f"{log['timestamp']} | {log['intent'].get('user_query', 'N/A')[:20]}..."):
                    st.caption(f"ID: {log['log_id']}")
                    col1, col2 = st.columns(2)
                    with col1: st.metric("Docs", log['results'].get('docs_returned', 0))
                    with col2: st.metric("Score", f"{log['results'].get('avg_score', 0):.2f}")
                    
                    tab1, tab2, tab3 = st.tabs(["Logs", "Intent", "Resultados"])
                    with tab1: st.json(log.get('logs', []))
                    with tab2: st.json(log.get('intent', {}))
                    with tab3: st.json(log.get('results', {}))
                    
                    if st.button("Borrar", key=f"del_{log['log_id']}"):
                        logic.delete_debug_log(log['log_id'])
                        st.rerun()
    # ----------------------

    st.markdown("---")
    st.caption("Historial de Chats")
    
    for chat in logic.get_all_chats():
        label = f"{chat.get('title','Chat')}" if chat["id"] == st.session_state.current_chat["id"] else chat.get("title","Chat")
        if st.button(label, key=chat["id"], use_container_width=True):
            loaded = logic.load_chat_from_disk(chat["id"])
            if loaded:
                st.session_state.current_chat = loaded
                st.rerun()
            
    st.markdown("---")
    st.subheader("Configuración")
    
    selected_model = st.selectbox(
        "Modelo:",
        ["openai/gpt-4o-mini", "openai/gpt-4o"],
        index=0
    )
    
    temperature = st.slider("Temperatura", 0.0, 1.0, 0.0, 0.1)
    k_val = st.slider("Contexto (Docs)", 1, 20, 10)
    debug_mode = st.checkbox("Modo Debug (En chat)", value=True)
    show_search_type = st.checkbox("Mostrar métricas", value=True)
    
    st.markdown("---")
    if st.button("Eliminar Chat", type="primary", use_container_width=True):
        logic.delete_chat_from_disk(st.session_state.current_chat["id"])
        existing = logic.get_all_chats()
        st.session_state.current_chat = existing[0] if existing else logic.create_new_chat_data()
        st.rerun()

    with st.expander("ℹInformación del Sistema"):
        st.caption("""
        **Tipos de búsqueda:**
        - **Vectorial**: Similitud semántica
        - **Texto**: Coincidencia exacta
        - **Temporal**: Ordenado por fecha
        """)
    
    with st.expander("Aviso Legal"):
        st.caption("Sistema académico. Respuestas generadas por IA. No se almacenan datos personales.")

# --- CARGA DE RECURSOS ---
llm = logic.load_llm(selected_model, temperature)

# --- UI PRINCIPAL ---
current_title = st.session_state.current_chat.get("title", "Nuevo Chat")
st.markdown(f'<div class="main-header"><h1>⚡ {current_title}</h1><p>Modelo: <strong>{selected_model}</strong> | Docs: {k_val}</p></div>', unsafe_allow_html=True)

# Mostrar mensajes previos
for msg in st.session_state.current_chat["messages"]:
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])

# --- LÓGICA DE CHAT ---
if q := st.chat_input("Escribe tu consulta..."):
    # 1. Guardar mensaje usuario
    st.session_state.current_chat["messages"].append({"role": "user", "content": q})
    if len(st.session_state.current_chat["messages"]) == 1:
        st.session_state.current_chat["title"] = " ".join(q.split()[:5]) + "..."
    logic.save_chat_to_disk(st.session_state.current_chat)
    
    with st.chat_message("user"): 
        st.markdown(q)

    # 2. Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner(f"Buscando en base de datos..."):
            
            # --- BÚSQUEDA (Devuelve resultados y log) ---
            results, debug_log = logic.search_elastic(q, llm, k=k_val)
            
            # Obtenemos resumen del log
            log_summary = debug_log.get_summary()
            
            # --- ANÁLISIS DE RESULTADOS ---
            search_type = "UNKNOWN"
            avg_score = 0.0
            
            if results:
                scores = [doc['score'] for doc in results if doc['score'] is not None]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    if avg_score == 0: search_type = "TEMPORAL"
                    elif avg_score > 1.0: search_type = "TEXT_BM25"
                    else: search_type = "VECTOR_KNN"
            else:
                search_type = "NO_RESULTS"
            
            # --- VISUALIZACIÓN DE MÉTRICAS ---
            if show_search_type and results:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if search_type == "VECTOR_KNN": st.metric("Búsqueda", "Vectorial", f"{avg_score:.1%}")
                    elif search_type == "TEXT_BM25": st.metric("Búsqueda", "Texto", f"Score: {avg_score:.2f}")
                    else: st.metric("Búsqueda", "Temporal", "Reciente")
                with col2: st.metric("Docs", len(results))
                with col3:
                    latest = max([doc.get('date', 'N/A') for doc in results]) if results else 'N/A'
                    st.metric("Fecha", latest[:10])

            # --- DEBUG INFO EN CHAT ---
            if debug_mode and results:
                with st.expander("Información Técnica Inmediata"):
                    st.markdown(f"**Log ID:** `{log_summary['log_id']}`")
                    st.markdown("**Scores individuales:**")
                    for i, doc in enumerate(results[:5], 1):
                        score_type = "Vector" if 0 < doc['score'] < 1 else "Texto" if doc['score'] > 1 else "Fecha"
                        st.text(f"{i}. [{doc['score']:.4f}] ({score_type}) - {doc['title'][:50]}...")

            # --- CONSTRUCCIÓN DEL CONTEXTO ---
            ctx = ""
            html_sources = ""
            
            if results:
                for i, doc in enumerate(results, 1):
                    ctx += f"NOTICIA {i}: (Fecha: {doc['date']}) {doc['content'][:4000]}\nFUENTE: {doc['url']}\n\n"
                    
                    if doc['score'] == 0: score_str = "📅 Fecha"
                    elif doc['score'] > 1: score_str = f"🔤 {doc['score']:.2f}"
                    else: score_str = f"{doc['score']:.1%}"
                    
                    html_sources += f"""
                    <div class="source-card">
                        <strong>{doc['title']}</strong><br>
                        <small style="color: #95a5a6;">{doc['date']}</small> | <span style="color: #4ecdc4;">{score_str}</span><br>
                        <a href='{doc['url']}' target="_blank" style="color: #fff;">🔗 Ver noticia</a>
                    </div>
                    """
            else:
                ctx = "No se encontraron noticias coincidentes en la base de datos."
                st.warning("No se encontraron resultados para tu consulta.")

            # --- GENERACIÓN DE RESPUESTA ---
            rag_chain = logic.get_rag_chain(llm)
            raw_resp = rag_chain.invoke({"context": ctx, "question": q})
            resp = logic.clean_response(raw_resp)
            
            # Pie de página
            metric_label = "Semántica" if search_type == "VECTOR_KNN" else "📅 Temporal" if search_type == "TEMPORAL" else "🔤 Texto"
            resp += f"\n\n---\n* {metric_label} | Modelo: {selected_model} | Log ID: `{log_summary['log_id']}`*"
            
            st.markdown(resp)
            
            if results and "No se encontraron noticias" not in ctx:
                with st.expander(f"Ver {len(results)} fuentes utilizadas"): 
                    st.markdown(html_sources, unsafe_allow_html=True)
    
    # 3. Guardar respuesta
    st.session_state.current_chat["messages"].append({"role": "assistant", "content": resp})
    logic.save_chat_to_disk(st.session_state.current_chat)
    st.rerun()