# 🧠 RAG Agentic Cliente

Este proyecto implementa un **frontend** para un sistema **RAG (Retrieval-Augmented Generation)** utilizando **agentes inteligentes**, un **LLM local con LM Studio**, y exposición pública opcional mediante **Ngrok**.  
La interfaz gráfica se construye con **Streamlit**.

---

## 📦 Requisitos

Asegúrate de tener instalados los siguientes componentes:

- ✅ Python **3.10+** o **3.12+**
- ✅ `pip`, `venv`, `uvicorn`

---

## ⚙️ Instalación de dependencias

Desde la carpeta raíz del proyecto (`rag_agentic_client`):

```bash
# Crear y activar entorno virtual
python -m venv env
source env/bin/activate   # En Windows: env\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Ejecutar el frontend

Dirígete a la carpeta client.

Elige el tipo de frontend que deseas correr:

### Agentic RAG
```bash
streamlit run app_agent.py
```

### Vanilla RAG
```bash
streamlit run app_rag.py
```

## ✅ ¡Listo!

Tu frontend estará disponible en el navegador en:

http://localhost:8501
