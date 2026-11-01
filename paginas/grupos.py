# paginas/grupos.py
import streamlit as st
from utils import salvar_dados, ARQUIVO_GRUPOS

def render_pagina_grupos(usuario_atual, is_admin):
    st.title("🔬 Área de Grupos de Pesquisa")
    st.caption("Acesso restrito por senha individual por grupo.")

    # Coloque aqui todo o código correspondente à tela de Grupos de Pesquisa
    import streamlit as st
from utils import salvar_dados, ARQUIVO_GRUPOS

def render_pagina_grupos(usuario_atual, is_admin):
    st.title("🔬 Área de Grupos de Pesquisa")
    st.caption("Acesso restrito por senha individual por grupo.")

    meus_grupos = [g for g in st.session_state.grupos_db if g.get("status") == "Aprovado" and (usuario_atual["nome"] in g.get("membros", []) or is_admin)]
    if meus_grupos:
        grp_sel_nome = st.selectbox("Selecione o Grupo de Pesquisa", [g["nome"] for g in meus_grupos])
        grupo_ativo = next((g for g in meus_grupos if g["nome"] == grp_sel_nome), meus_grupos[0])

        autenticado = (grupo_ativo["id"] in st.session_state.grupos_autenticados) or is_admin

        if not autenticado:
            with st.container(border=True):
                st.warning(f"🔒 O Grupo **{grupo_ativo['nome']}** é protegido por senha.")
                with st.form(f"form_auth_grp_{grupo_ativo['id']}"):
                    senha_grp_input = st.text_input("Senha do Grupo", type="password")
                    if st.form_submit_button("🔓 Acessar Área do Grupo", type="primary"):
                        if senha_grp_input == grupo_ativo.get("senha", ""):
                            st.session_state.grupos_autenticados.append(grupo_ativo["id"])
                            st.rerun()
                        else:
                            st.error("Senha incorreta.")
        else:
            st.success(f"🔓 Você está autenticado no grupo: **{grupo_ativo['nome']}**")
            st.markdown(f"<div class='css-card'>{grupo_ativo.get('descricao')}</div>", unsafe_allow_html=True)
