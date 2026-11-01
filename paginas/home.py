import streamlit as st
from datetime import datetime
from utils import salvar_dados, ARQUIVO_AVISOS
from config import CORES_GOOGLE_AGENDA

def render_pagina_home(usuario_atual, is_admin):
    st.title("🏠 Painel Geral de Pesquisa")
    st.caption(f"Bem-vindo(a) de volta, **{usuario_atual['nome']}**! Acompanhe abaixo o resumo das atividades.")

    st.markdown("<br>", unsafe_allow_html=True)
    hoje_str = datetime.now().strftime("%Y-%m-%d")

    # METRICAS EM GRID (2x2 / 4 COLUNAS)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(f'<div class="kpi-card kpi-card-blue"><div><div class="kpi-val">{len(st.session_state.integrantes)}</div><div class="kpi-label">Integrantes</div></div><div class="kpi-icon">👥</div></div>', unsafe_allow_html=True)

    with kpi2:
        eventos_futuros = [e for e in st.session_state.agenda if e.get("data", "") >= hoje_str]
        st.markdown(f'<div class="kpi-card kpi-card-green"><div><div class="kpi-val">{len(eventos_futuros)}</div><div class="kpi-label">Próximos Eventos</div></div><div class="kpi-icon">📅</div></div>', unsafe_allow_html=True)

    with kpi3:
        st.markdown(f'<div class="kpi-card kpi-card-amber"><div><div class="kpi-val">{len(st.session_state.avisos_db)}</div><div class="kpi-label">Avisos Ativos</div></div><div class="kpi-icon">📢</div></div>', unsafe_allow_html=True)

    with kpi4:
        pops_aprov = len([p for p in st.session_state.pops_db if p.get("status") == "Aprovado"])
        st.markdown(f'<div class="kpi-card kpi-card-purple"><div><div class="kpi-val">{pops_aprov}</div><div class="kpi-label">POPs Vigentes</div></div><div class="kpi-icon">📝</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        with st.container(border=True):
            st.subheader("📢 Mural de Avisos do Laboratório")
            if is_admin:
                with st.expander("➕ Publicar Novo Aviso"):
                    with st.form("form_novo_aviso"):
                        tit_aviso = st.text_input("Título do Aviso *")
                        cat_aviso = st.selectbox("Categoria", ["Informativo", "Manutenção", "Urgente", "Segurança"])
                        cor_aviso = st.selectbox("Cor de Destaque", list(CORES_GOOGLE_AGENDA.keys()))
                        txt_aviso = st.text_area("Conteúdo do Aviso *")
                        if st.form_submit_button("📌 Publicar Aviso", type="primary"):
                            novo_id = max([a.get("id", 0) for a in st.session_state.avisos_db], default=0) + 1
                            st.session_state.avisos_db.insert(0, {
                                "id": novo_id, "titulo": tit_aviso, "conteudo": txt_aviso,
                                "categoria": cat_aviso, "cor": CORES_GOOGLE_AGENDA[cor_aviso],
                                "autor": usuario_atual["nome"], "data": datetime.now().strftime("%d/%m/%Y")
                            })
                            salvar_dados(ARQUIVO_AVISOS, st.session_state.avisos_db)
                            st.rerun()

            for av in st.session_state.avisos_db:
                c_hex = av.get("cor", "#0E7490")
                st.markdown(f'<div class="aviso-card" style="border-left-color: {c_hex};"><h4>{av["titulo"]}</h4><p>{av["conteudo"]}</p></div>', unsafe_allow_html=True)

    with col_right:
        with st.container(border=True):
            st.subheader("📅 Próximas Reuniões & Compromissos")
            eventos_validos = [e for e in st.session_state.agenda if e.get("data", "") >= hoje_str]
            for ev in eventos_validos[:5]:
                st.markdown(f'<div class="event-card"><strong>{ev["titulo"]}</strong><div>🕒 {ev.get("data")} das {ev.get("hora_inicio")} às {ev.get("hora_fim")}</div></div>', unsafe_allow_html=True)
