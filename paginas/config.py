# config.py
import streamlit as st

CATEGORIAS_PADRAO = [
    "Iniciação Científica", "Mestrado", "Doutorado", 
    "Pós-Doutorado", "Orientador", "Técnico / Pesquisador"
]

CORES_GOOGLE_AGENDA = {
    "🔵 Azul (Reunião / Geral)": "#0284C7",
    "🟢 Verde (Ensaio / Experimento)": "#059669",
    "🔴 Vermelho (Urgente / Importante)": "#DC2626",
    "🟣 Roxo (Apresentação / Defesa)": "#7C3AED",
    "🟠 Laranja (Manutenção / Limpeza)": "#EA580C"
}

def aplicar_estilos_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp { background-color: #F8FAFC; }
        </style>
    """, unsafe_allow_html=True)