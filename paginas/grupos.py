# paginas/grupos.py
import streamlit as st
from utils import salvar_dados, ARQUIVO_GRUPOS

def render_pagina_grupos(usuario_atual, is_admin):
    st.title("🔬 Área de Grupos de Pesquisa")
    st.caption("Acesso restrito por senha individual por grupo.")

    # Coloque aqui todo o código correspondente à tela de Grupos de Pesquisa