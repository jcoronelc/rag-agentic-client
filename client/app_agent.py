from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime

import streamlit as st
import uuid  
import json
import os
import time
import requests

os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
 
SESSION_ID = "1234"
B_INST, E_INST = "<s>[INST]", "[/INST]</s>"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

API_BASE_URL = "https://fd8d-200-55-228-82.ngrok-free.app/api"


def save_history():
    chat_data = {
        chat_id: {
        "title": st.session_state.history[chat_id]["title"],
        "messages": [
                {
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content
                } for msg in st.session_state.chat_store[chat_id].messages
                ],
        "created_at": datetime.now().isoformat()
        } for chat_id in st.session_state.history
    }

    response = requests.post(
        f"{API_BASE_URL}/agentic/history/save_all", 
        json=chat_data
    )
    return response.ok
   
    # with open("./data/output/chat/agent_chat_history.json", "w") as f:
    #     json.dump(chat_data, f, indent=4)
        
def load_history():
    try:
        response = requests.get(f"{API_BASE_URL}/agentic/history/load_all")
        if response.status_code == 200:
            chat_data = response.json()
            for chat_id, chat_info in chat_data.items():
                st.session_state.history[chat_id] = {"title": chat_info["title"]}
                chat_history = ChatMessageHistory()
                
                for msg in chat_info["messages"]:
                    role = msg["role"]
                    content = msg["content"]
                    
                    # Según el rol, creamos el mensaje correspondiente
                    if role == "user":
                        chat_history.add_message(HumanMessage(content=content))
                    elif role == "assistant":
                        chat_history.add_message(AIMessage(content=content))
                    else:
                        print(f"Formato desconocido en mensaje: {msg}")    
                    
                
                st.session_state.chat_store[chat_id] = chat_history
            return chat_data
        else:
            return {}
    except FileNotFoundError:
        return {}

def select_chat():
    chat_ids_sorted = sorted(
        st.session_state.history.keys(),
        key=lambda chat_id: st.session_state.history[chat_id]["created_at"],
        reverse=True
    )
    # chat_ids = list(st.session_state.history.keys())
    # chat_ids.sort(reverse=True)
    
    for chat_id in chat_ids_sorted:
        first_message = st.session_state.chat_store[chat_id].messages[0].content if st.session_state.chat_store[chat_id].messages else "No hay mensajes"
        #limitar titulo de chat con la primera query
        summary = " ".join(first_message.split()[:6]) + "..." if len(first_message.split()) >= 6 else first_message
        
        with st.sidebar.container():
            col1, col2 = st.sidebar.columns([4, 1], gap="small")
            with col1:
                # st.markdown(f"<div style='text-align: left; font-size: 15px; padding: 5px;'>{summary}</div>", unsafe_allow_html=True)
                if st.button(f"{summary}", key=chat_id, type='tertiary',  use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    save_history()
                    st.rerun()
                    
            with col2:
                with st.expander("", expanded=False, ):
                    if st.button("❌", key=f"delete_{chat_id}", help="Eliminar chat",  use_container_width=True):
                        del st.session_state.history[chat_id]
                        del st.session_state.chat_store[chat_id]
                        
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                        
                        save_history()
                        st.rerun()
                

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in st.session_state.chat_store:
        st.session_state.chat_store[session_id] = ChatMessageHistory()
    return st.session_state.chat_store[session_id]

def get_response(chat_id, question):
    """ Obtiene la respuesta de la bd vectorial basada en la consulta. """
    
    collection_name_active = "bdv2"
    collection_name_active_summary = "bdvs3"
    use_memory = True
    
    payload = {
        "model_llm_responses": selected_llm_model,
        "collection_name_active": collection_name_active, 
        "collection_name_active_summary": collection_name_active_summary, 
        "question": question,
        "top_k": 4,
        "use_external_data": True,
        "use_memory": use_memory,
        "chat_id": chat_id,
        "crew_name": "crew_4"
    }

    try:
        res = requests.post(f"{API_BASE_URL}/agentic/ask", json=payload)
        return res.json().get("response", "Sin respuesta")
    except Exception as e:
        return f"Error al consultar /agentic/ask: {str(e)}"
    
 
def get_response_finetuning(chat_id, question):
    """ Obtiene la respuesta de la bd vectorial basada en la consulta. """
    
    print("Flujo con Fine-Tuning")
    
    collection_name_active = "bdv2"
    collection_name_active_summary = "bdvs3"
    use_memory = False
    
    payload = {
        "model_llm_responses": selected_llm_model,
        "collection_name_active": collection_name_active, 
        "collection_name_active_summary": collection_name_active_summary, 
        "question": question,
        "top_k": 4,
        "use_external_data": True,
        "use_memory": use_memory,
        "chat_id": chat_id,
        "crew": "crew_finetuning"
    }

    try:
        res = requests.post(f"{API_BASE_URL}/agentic/ask", json=payload)
        return res.json().get("response", "Sin respuesta")
    except Exception as e:
        return f"Error al consultar /agentic/ask: {str(e)}"

    
### ------- GUI ----------
st.set_page_config(page_title="Chatbot MultiAgente", page_icon="🦜")
st.title("Chatea con :blue[tus datos] 🤖")

# ---- Inicializacion de claves para la session
if "chat_store" not in st.session_state:
    st.session_state.chat_store = {}

if "history" not in st.session_state:
    st.session_state.history = {}

# Cargar historial desde JSON
loaded_history = load_history()
if loaded_history:
    st.session_state.history.update(loaded_history)

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- Sidebar: Historial de conversaciones ---
st.sidebar.title("💬  Chats")

# --- Crear nuevo chat ---
if st.sidebar.button("➕ Nuevo Chat"):
    new_chat_id = str(uuid.uuid4())[:8]  
    st.session_state.history[new_chat_id] = {"title": f"Chat {len(st.session_state.history) + 1}"}
    st.session_state.chat_store[new_chat_id] = ChatMessageHistory()
    st.session_state.current_chat_id = new_chat_id
    save_history() 
    st.rerun()
    
select_chat()


# Mostrar el historial de la conversacion
chat_id = st.session_state.current_chat_id if st.session_state.current_chat_id else None

# para crear un chat si no se crea un nuevo chat con el btn
# if not chat_id:
#     new_chat_id = str(uuid.uuid4())[:8]  
#     st.session_state.history[new_chat_id] = {"title": f"Chat {len(st.session_state.history) + 1}"}
#     st.session_state.chat_store[new_chat_id] = ChatMessageHistory()
#     st.session_state.current_chat_id = new_chat_id  
#     save_history()


if chat_id:
    
    # rag_crew = Crew(
    # agents=[retriever_agent, evaluator_agent, router_agent, answer_agent],
    # tasks=[retriever_task, evaluator_task, router_task, answer_task],
    # verbose=True,
    # process=Process.sequential,
    # # memory=True, # memory capabilities
    # # memory_config={
    # #     "provider": "mem0",
    # #     "config": {"user_id": chat_id,
    # #                "api_key": "m0-bnTCjYzJePVtZDrRmibHDe2zvkiByzrMSTde30OM"},
    # #     "user_memory" : {}
        
    # # }
    # )
    # rag_crew = Crew(
    # agents=[travel_agent],
    # tasks=[planning_task],
    # verbose=True,
    # memory=True, # memory capabilities
    # memory_config={
    #     "provider": "mem0",
    #     "config": {"user_id": chat_id,
    #                "api_key": "m0-bnTCjYzJePVtZDrRmibHDe2zvkiByzrMSTde30OM"}
    #     # "user_memory" : {}
    # }
    # )

    st.write(f"**Conversación activa:** `{chat_id}`")

    for message in st.session_state.chat_store[chat_id].messages:
        if isinstance(message, AIMessage):
           MESSAGE_TYPE = "assistant"
        elif isinstance(message, HumanMessage):
            MESSAGE_TYPE = "user"
        else:
            MESSAGE_TYPE = "unknown"

        if MESSAGE_TYPE != "unknown":
            with st.chat_message(MESSAGE_TYPE):
                st.markdown(f"{message.content}")

# Entrar mensaje de usuario y seleccionar modelo LLM
with st.container():
    col1, col2, col3 = st.columns([1, 4, 1])

    response = requests.get(f"{API_BASE_URL}/models/llm")
    if response.status_code == 200:
        models_llm = response.json()

    with col1:
        selected_llm_model = st.selectbox(
            label="Modelo LLM", 
            options=list(models_llm.values()), 
            index=0,
            placeholder="Selecciona el modelo LLM",
            label_visibility="collapsed",
        )
        
    with col2:
        user_query = st.chat_input("Escribe tu mensaje ✍")
        
    with col3: 
        if st.button("🗑 Limpiar"):
            st.session_state.chat_store[chat_id] = ChatMessageHistory()
            save_history() 
            st.rerun()

if user_query:
    with st.spinner("Generando respuesta..."):

        start = time.time()

        if selected_llm_model != 'mistralfinetuning':
            response = get_response(chat_id, user_query)
        else:
            response = get_response_finetuning(chat_id, user_query)
        
        end = time.time()
        elapsed = end - start
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f"Tiempo total de ejecución: {int(hours)}h {int(minutes)}m {int(seconds)}s")

        st.session_state.chat_store[chat_id].add_message(HumanMessage(content=user_query))
        st.session_state.chat_store[chat_id].add_message(AIMessage(content=response))

        save_history() 
        st.rerun()

