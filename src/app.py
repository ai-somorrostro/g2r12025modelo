import streamlit as st
import logic  # Importamos nuestro módulo de lógica

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
    st.title("⚡ AI Studio")
    
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.current_chat = logic.create_new_chat_data()
        logic.save_chat_to_disk(st.session_state.current_chat)
        st.rerun()
    
    st.markdown("---")
    st.caption("📜 Historial")
    
    for chat in logic.get_all_chats():
        label = f"📂 {chat.get('title','Chat')}" if chat["id"] == st.session_state.current_chat["id"] else chat.get("title","Chat")
        if st.button(label, key=chat["id"], use_container_width=True):
            loaded = logic.load_chat_from_disk(chat["id"])
            if loaded:
                st.session_state.current_chat = loaded
                st.rerun()
            
    st.markdown("---")
    st.subheader("⚙️ Configuración")
    
    # LISTA DE MODELOS ACTUALIZADA (Solo los fiables)
    selected_model = st.selectbox(
        "Modelo:",
        [
            "openai/gpt-4o-mini",              # El mejor calidad/precio
            "meta-llama/llama-3.1-8b-instruct",# Buena alternativa Open Source
            "openai/gpt-4o"                    # El más inteligente
        ],
        index=0
    )
    
    temperature = st.slider("Temperatura", 0.0, 1.0, 0.0, 0.1)
    k_val = st.slider("Contexto (Docs)", 1, 10, 5)
    debug_mode = st.checkbox("Modo Debug", value=True)
    
    st.markdown("---")
    if st.button("🗑️ Eliminar Chat", type="primary", use_container_width=True):
        logic.delete_chat_from_disk(st.session_state.current_chat["id"])
        existing = logic.get_all_chats()
        st.session_state.current_chat = existing[0] if existing else logic.create_new_chat_data()
        st.rerun()

    with st.expander("Aviso Legal"):
        st.caption("Sistema académico. Respuestas generadas por IA. No se almacenan datos personales.")

# --- CARGA DE RECURSOS ---
llm = logic.load_llm(selected_model, temperature)

# --- UI PRINCIPAL ---
current_title = st.session_state.current_chat.get("title", "Nuevo Chat")
st.markdown(f'<div class="main-header"><h1>⚡ {current_title}</h1><p>Modelo: <strong>{selected_model}</strong></p></div>', unsafe_allow_html=True)

for msg in st.session_state.current_chat["messages"]:
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])

if q := st.chat_input("Escribe tu consulta..."):
    st.session_state.current_chat["messages"].append({"role": "user", "content": q})
    if len(st.session_state.current_chat["messages"]) == 1:
        st.session_state.current_chat["title"] = " ".join(q.split()[:5]) + "..."
    logic.save_chat_to_disk(st.session_state.current_chat)
    
    with st.chat_message("user"): st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner(f"Consultando con {selected_model}..."):
            
            optimized_q = q if len(q.split()) < 3 else logic.optimize_query(q, llm)
            results = logic.search_elastic(optimized_q, k=k_val)
            
            if debug_mode:
                with st.expander("Datos de la Prueba"):
                    st.write(f"**Query usada:** {optimized_q}")
                    st.write(f"**Docs Recuperados:** {len(results)}")

            ctx = ""
            html_sources = ""
            for i, doc in enumerate(results):
                ctx += f"NOTICIA {i+1}: (Fecha: {doc['date']}) {doc['content'][:4000]}\nFUENTE: {doc['url']}\n\n"
                html_sources += f"<div><strong>{doc['title']}</strong><br><a href='{doc['url']}'>Link</a></div><hr>"
            
            if not ctx:
                ctx = "No se encontraron noticias coincidentes en la base de datos."

            rag_chain = logic.get_rag_chain(llm)
            raw_resp = rag_chain.invoke({"context": ctx, "question": q})
            resp = logic.clean_response(raw_resp)
            
            resp += f"\n\n---\n* Respuesta generada por: **{selected_model}** | Temp: {temperature}*"
            
            st.markdown(resp)
            if ctx and "No se encontraron noticias" not in ctx:
                with st.expander("Fuentes"): st.markdown(html_sources, unsafe_allow_html=True)
    
    st.session_state.current_chat["messages"].append({"role": "assistant", "content": resp})
    logic.save_chat_to_disk(st.session_state.current_chat)
    st.rerun()