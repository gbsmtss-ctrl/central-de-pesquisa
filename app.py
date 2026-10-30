import calendar
from datetime import datetime, time
from io import BytesIO
import json
import os
import pandas as pd
import qrcode
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Central de Pesquisa",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILIZAÇÃO VISUAL (AZUL CLARO E BRANCO) ---
st.markdown(
    """
    <style>
    /* Fundo principal da aplicação em azul super claro */
    .stApp {
        background-color: #F4F8FB;
    }
    /* Estilo da barra lateral (Sidebar) em azul claro */
    [data-testid="stSidebar"] {
        background-color: #E3F2FD;
    }
    /* Cor dos títulos principais */
    h1, h2, h3 {
        color: #0D47A1 !important;
    }
    /* Botões primários em azul vibrante */
    div.stButton > button:first-child {
        background-color: #1E88E5;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #1565C0;
        color: white;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SISTEMA DE PERSISTÊNCIA DE DADOS ---
ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"


def carregar_dados(arquivo, padrao):
  """Carrega os dados salvos em arquivo JSON."""
  if os.path.exists(arquivo):
    with open(arquivo, "r", encoding="utf-8") as f:
      return json.load(f)
  return padrao


def salvar_dados(arquivo, dados):
  """Salva a lista atualizada no arquivo JSON."""
  with open(arquivo, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)


# Inicializa os dados salvos
if "integrantes" not in st.session_state:
  st.session_state.integrantes = carregar_dados(
      ARQUIVO_INTEGRANTES,
      [{
          "Nome": "Eliane Pereira Cipolatti",
          "Categoria": "Orientador",
          "Vínculo": "UFRRJ - Engenharia de Alimentos",
          "Situação": "Ativo",
      }],
  )

if "agenda" not in st.session_state:
  st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, [])

usuario_admin_padrao = [{
    "nome": "Administrador",
    "usuario": "admin",
    "senha": "123",
    "status": "Aprovado",
    "is_admin": True,
}]

if "usuarios" not in st.session_state:
  st.session_state.usuarios = carregar_dados(
      ARQUIVO_USUARIOS, usuario_admin_padrao
  )

if "usuario_logado" not in st.session_state:
  st.session_state.usuario_logado = None


# --- TELA DE LOGIN E SOLICITAÇÃO DE ACESSO ---
if st.session_state.usuario_logado is None:
  st.title("🧪 Central de Pesquisa - Controle de Acesso ⚗️")

  aba_login, aba_cadastro = st.tabs(["Entrar no Sistema", "Solicitar Acesso"])

  # Aba de Login
  with aba_login:
    st.subheader("Login")
    with st.form("form_login"):
      user_input = st.text_input("Usuário / E-mail")
      senha_input = st.text_input("Senha", type="password")
      btn_login = st.form_submit_button("Entrar", type="primary")

      if btn_login:
        usuario_encontrado = None
        for u in st.session_state.usuarios:
          if u["usuario"].lower() == user_input.strip().lower():
            usuario_encontrado = u
            break

        if usuario_encontrado:
          if usuario_encontrado["senha"] == senha_input:
            if usuario_encontrado["status"] == "Aprovado":
              st.session_state.usuario_logado = usuario_encontrado
              st.success(f"Bem-vindo(a), {usuario_encontrado['nome']}!")
              st.rerun()
            elif usuario_encontrado["status"] == "Pendente":
              st.warning(
                  "Sua solicitação de acesso ainda está pendente de aprovação"
                  " pelo administrador."
              )
            else:
              st.error("Sua solicitação de acesso foi recusada ou removida.")
          else:
            st.error("Senha incorreta.")
        else:
          st.error("Usuário não encontrado.")

  # Aba de Solicitação de Acesso
  with aba_cadastro:
    st.subheader("Pedir Permissão de Acesso")
    with st.form("form_solicitar_acesso"):
      novo_nome = st.text_input("Nome Completo")
      novo_usuario = st.text_input("Usuário Desejado (ex: gabriela)")
      nova_senha = st.text_input("Criar Senha", type="password")
      btn_solicitar = st.form_submit_button("Enviar Solicitação")

      if btn_solicitar and novo_nome and novo_usuario and nova_senha:
        usr_clean = novo_usuario.strip().lower()

        # Verifica existência considerando apenas contas ativas ou pendentes
        existe = any(
            u["usuario"].lower() == usr_clean
            and u.get("status") in ["Aprovado", "Pendente"]
            for u in st.session_state.usuarios
        )

        if existe:
          st.error(
              "Este nome de usuário já está em uso por uma conta ativa ou"
              " pendente. Escolha outro nome de usuário."
          )
        else:
          # Remove qualquer registro antigo/inativo desse nome de usuário para liberar o login
          st.session_state.usuarios = [
              u
              for u in st.session_state.usuarios
              if u["usuario"].lower() != usr_clean
          ]

          # Cria o novo registro de solicitação
          novo_user_dict = {
              "nome": novo_nome.strip(),
              "usuario": novo_usuario.strip(),
              "senha": nova_senha,
              "status": "Pendente",
              "is_admin": False,
          }
          st.session_state.usuarios.append(novo_user_dict)
          salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

          # Atualiza ou adiciona na lista de integrantes como Pendente
          integrante_existente = next(
              (
                  p
                  for p in st.session_state.integrantes
                  if p["Nome"].lower() == novo_nome.strip().lower()
              ),
              None,
          )
          if integrante_existente:
            integrante_existente["Situação"] = "Pendente"
          else:
            st.session_state.integrantes.append({
                "Nome": novo_nome.strip(),
                "Categoria": "Aluno / Pesquisador",
                "Vínculo": "Solicitante de Acesso",
                "Situação": "Pendente",
            })
          salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

          st.success(
              "Solicitação enviada com sucesso! Seu nome consta na tabela de"
              " integrantes como 'Pendente'. Aguarde a aprovação do"
              " administrador."
          )

# --- ÁREA LOGADA (SISTEMA PRINCIPAL) ---
else:
  usuario_atual = st.session_state.usuario_logado

  # Barra Lateral
  st.sidebar.title("🧪 Central de Pesquisa ⚗️")
  st.sidebar.caption(f"Usuário: **{usuario_atual['nome']}**")

  if usuario_atual.get("is_admin"):
    opcoes_menu = [
        "Visão Geral",
        "Cadastrar Integrantes",
        "Calendário / Agenda",
        "Gerar QR Code de Amostras",
        "Aprovar Acessos",
    ]
  else:
    opcoes_menu = [
        "Visão Geral",
        "Calendário / Agenda",
        "Gerar QR Code de Amostras",
    ]

  menu = st.sidebar.radio("Navegação", opcoes_menu)

  st.sidebar.markdown("---")
  if st.sidebar.button("🚪 Sair / Logout"):
    st.session_state.usuario_logado = None
    st.rerun()

  # --- 1. VISÃO GERAL ---
  if menu == "Visão Geral":
    st.title("🧪 Visão Geral do Laboratório")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Integrantes Ativos",
        sum(
            1
            for p in st.session_state.integrantes
            if p.get("Situação") == "Ativo"
        ),
    )
    col2.metric(
        "Alunos Ativos",
        sum(
            1
            for p in st.session_state.integrantes
            if p.get("Categoria") != "Orientador"
            and p.get("Situação") == "Ativo"
        ),
    )
    col3.metric("Agendamentos Ativos", len(st.session_state.agenda))

    st.markdown("---")
    st.subheader("Integrantes do Laboratório")

    if st.session_state.integrantes:
      df = pd.DataFrame(st.session_state.integrantes)
      st.dataframe(df, use_container_width=True)
    else:
      st.info("Nenhum integrante cadastrado no momento.")

  # --- 2. CADASTRO E REMOÇÃO DE INTEGRANTES (EXCLUSIVO ADMIN) ---
  elif menu == "Cadastrar Integrantes":
    st.title("Gestão de Integrantes")

    st.subheader("Cadastrar Novo Integrante")
    with st.form("form_cadastro"):
      nome = st.text_input("Nome Completo")
      categoria = st.selectbox(
          "Categoria",
          [
              "Iniciação Científica",
              "Mestrado",
              "Doutorado",
              "Orientador",
              "Técnico",
          ],
      )
      vinculo = st.text_input(
          "Vínculo / Curso", "UFRRJ - Engenharia de Alimentos"
      )
      situacao = st.selectbox("Situação", ["Ativo", "Pendente", "Inativo"])

      btn_salvar = st.form_submit_button("Cadastrar Integrante")

      if btn_salvar and nome:
        existente = next(
            (
                p
                for p in st.session_state.integrantes
                if p["Nome"].lower() == nome.strip().lower()
            ),
            None,
        )
        if existente:
          existente["Categoria"] = categoria
          existente["Vínculo"] = vinculo
          existente["Situação"] = situacao
        else:
          st.session_state.integrantes.append({
              "Nome": nome.strip(),
              "Categoria": categoria,
              "Vínculo": vinculo,
              "Situação": situacao,
          })

        salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
        st.success(f"Integrante '{nome}' salvo com sucesso!")
        st.rerun()

    st.markdown("---")
    st.subheader("Remover Integrante")

    lista_nomes = [p["Nome"] for p in st.session_state.integrantes]

    if lista_nomes:
      pessoa_para_remover = st.selectbox(
          "Selecione quem deseja remover:", lista_nomes
      )

      if st.button("Apagar Integrante", type="primary"):
        # Remove da lista de integrantes
        st.session_state.integrantes = [
            p
            for p in st.session_state.integrantes
            if p["Nome"] != pessoa_para_remover
        ]
        salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

        # Remove o usuário correspondente para LIBERAR O NOME DE USUÁRIO
        st.session_state.usuarios = [
            u
            for u in st.session_state.usuarios
            if u["nome"].lower() != pessoa_para_remover.lower()
        ]
        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

        st.success(
            f"Integrante '{pessoa_para_remover}' removido(a) com sucesso! O"
            " nome de usuário foi liberado para novos cadastros."
        )
        st.rerun()

  # --- 3. CALENDÁRIO / AGENDA ---
  elif menu == "Calendário / Agenda":
    st.title("📅 Agenda e Calendário do Laboratório")

    col_esq, col_dir = st.columns([1, 1.2])

    with col_esq:
      st.subheader("➕ Agendar Compromisso")
      with st.form("form_agenda"):
        titulo = st.text_input(
            "Título do Compromisso", "Uso do Espectrofotômetro"
        )
        data_evento = st.date_input("Data do Evento", datetime.now().date())

        c1, c2 = st.columns(2)
        with c1:
          hora_inicio = st.time_input("Horário Inicial", time(9, 0))
        with c2:
          hora_fim = st.time_input("Horário Final", time(11, 0))

        equipamento = st.selectbox(
            "Equipamento / Local",
            [
                "Bancada A",
                "Bancada B",
                "Espectrofotômetro",
                "Autoclave",
                "Centrífuga",
                "Reunião de Grupo",
            ],
        )

        lista_resp = [
            p["Nome"]
            for p in st.session_state.integrantes
            if p.get("Situação") == "Ativo"
        ]
        responsavel = (
            st.selectbox("Pesquisador Responsável", lista_resp)
            if lista_resp
            else st.text_input("Pesquisador Responsável")
        )

        obs = st.text_input("Observações / Detalhes", "Análise de amostras")

        btn_agendar = st.form_submit_button("Confirmar Agendamento")

        if btn_agendar and titulo:
          novo_evento = {
              "ID": len(st.session_state.agenda) + 1,
              "Título": titulo,
              "Data": data_evento.strftime("%Y-%m-%d"),
              "Início": hora_inicio.strftime("%H:%M"),
              "Término": hora_fim.strftime("%H:%M"),
              "Equipamento": equipamento,
              "Responsável": responsavel,
              "Observações": obs,
          }
          st.session_state.agenda.append(novo_evento)
          salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
          st.success("Evento agendado com sucesso!")
          st.rerun()

    with col_dir:
      st.subheader("🔍 Consultar Dia Específico")
      data_consulta = st.date_input(
          "Selecione uma data para ver os eventos", datetime.now().date()
      )
      data_str = data_consulta.strftime("%Y-%m-%d")

      eventos_dia = [
          e for e in st.session_state.agenda if e["Data"] == data_str
      ]

      if eventos_dia:
        st.write(
            f"**Compromissos em {data_consulta.strftime('%d/%m/%Y')}:**"
        )
        for ev in eventos_dia:
          with st.expander(
              f"⏰ {ev['Início']} - {ev['Término']} | {ev['Título']}"
          ):
            st.write(f"**Local:** {ev['Equipamento']}")
            st.write(f"**Responsável:** {ev['Responsável']}")
            st.write(f"**Observações:** {ev['Observações']}")
      else:
        st.info(
            f"Nenhum compromisso agendado para"
            f" {data_consulta.strftime('%d/%m/%Y')}."
        )

    st.markdown("---")
    st.subheader("🗓️ Visão Geral do Mês (Calendário)")

    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    col_m1, col_m2 = st.columns(2)
    with col_m1:
      mes_sel = st.selectbox(
          "Selecione o Mês:", list(range(1, 13)), index=mes_atual - 1
      )
    with col_m2:
      ano_sel = st.number_input(
          "Ano:", min_value=2024, max_value=2035, value=ano_atual
      )

    cal = calendar.monthcalendar(ano_sel, mes_sel)
    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    eventos_mes = {}
    for ev in st.session_state.agenda:
      try:
        d_ev = datetime.strptime(ev["Data"], "%Y-%m-%d")
        if d_ev.year == ano_sel and d_ev.month == mes_sel:
          dia = d_ev.day
          if dia not in eventos_mes:
            eventos_mes[dia] = []
          eventos_mes[dia].append(ev)
      except ValueError:
        pass

    cols_header = st.columns(7)
    for idx, d_nome in enumerate(dias_semana):
      cols_header[idx].markdown(f"**{d_nome}**")

    for semana in cal:
      cols_dia = st.columns(7)
      for idx, dia in enumerate(semana):
        if dia == 0:
          cols_dia[idx].write(" ")
        else:
          num_ev = len(eventos_mes.get(dia, []))
          if num_ev > 0:
            cols_dia[idx].markdown(f"**{dia}** 🔴 *({num_ev})*")
          else:
            cols_dia[idx].write(f"{dia}")

    st.markdown("---")
    st.subheader("📋 Lista Completa de Agendamentos")

    if st.session_state.agenda:
      df_agenda = pd.DataFrame(st.session_state.agenda)
      colunas = [
          "Data",
          "Início",
          "Término",
          "Título",
          "Equipamento",
          "Responsável",
          "Observações",
      ]
      st.dataframe(
          df_agenda[colunas].sort_values(by=["Data", "Início"]),
          use_container_width=True,
      )

      st.markdown("### ❌ Cancelar Agendamento")
      opcoes = [
          f"ID {e['ID']} - {e['Data']} [{e['Início']}] {e['Título']}"
          f" ({e['Responsável']})"
          for e in st.session_state.agenda
      ]
      sel_cancelar = st.selectbox(
          "Selecione o compromisso para cancelar:", opcoes
      )

      if st.button("Remover Compromisso", type="primary"):
        id_sel = int(sel_cancelar.split(" ")[1])
        st.session_state.agenda = [
            e for e in st.session_state.agenda if e["ID"] != id_sel
        ]
        salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
        st.success("Agendamento removido!")
        st.rerun()

  # --- 4. GERADOR DE QR CODE PARA AMOSTRAS ---
  elif menu == "Gerar QR Code de Amostras":
    st.title("🧪 Gerador de QR Code de Amostras")

    col_form, col_qr = st.columns([1, 1])

    with col_form:
      id_amostra = st.text_input("Código / ID da Amostra", "AMS-2026-001")
      nome_amostra = st.text_input(
          "Nome da Amostra / Reagente", "Extrato Enzimático de Lipase"
      )

      data_obtencao = st.date_input(
          "Data de Obtenção / Produção", datetime.now().date()
      )

      lista_cadastrados = [
          p["Nome"]
          for p in st.session_state.integrantes
          if p.get("Situação") == "Ativo"
      ]
      opcoes_resp = lista_cadastrados + ["Outro / Digitar manualmente..."]

      sel_resp = st.selectbox("Pesquisador Responsável", opcoes_resp)

      if sel_resp == "Outro / Digitar manualmente...":
        responsavel = st.text_input(
            "Digite o Nome do Pesquisador", "Gabriela Mendes Farias Matos"
        )
      else:
        responsavel = sel_resp

      localizacao = st.text_input(
          "Local de Armazenamento", "Freezer -20°C / Caixa 3 / Posição B4"
      )

      descricao = st.text_area(
          "Descrição Detalhada / Protocolo de Preparo",
          value=(
              "Extrato obtido via fermentação estado sólido. Tampão fosfato"
              " 0.1M pH 7.0. Concentração de proteína: 2.5 mg/mL. Manter"
              " estritamente sob refrigeração."
          ),
          height=120,
      )

      gerar = st.button("Gerar QR Code")

    with col_qr:
      if gerar or id_amostra:
        conteudo_qr = (
            "=== FICHA DA AMOSTRA ===\n"
            f"ID: {id_amostra}\n"
            f"NOME: {nome_amostra}\n"
            f"RESPONSÁVEL: {responsavel}\n"
            f"DATA OBTENÇÃO: {data_obtencao.strftime('%d/%m/%Y')}\n"
            f"LOCAL: {localizacao}\n"
            "------------------------\n"
            f"DESCRIÇÃO:\n{descricao}\n"
            "========================"
        )

        img = qrcode.make(conteudo_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        st.image(img_bytes, caption=f"QR Code: {id_amostra}", width=260)

        st.download_button(
            label="Baixar QR Code (PNG)",
            data=img_bytes,
            file_name=f"QR_{id_amostra}.png",
            mime="image/png",
        )

  # --- 5. APROVAÇÃO E GESTÃO DE ACESSOS (EXCLUSIVO ADMIN) ---
  elif menu == "Aprovar Acessos":
    st.title("🔑 Gerenciamento e Aprovação de Acessos")

    pendentes = [
        u for u in st.session_state.usuarios if u.get("status") == "Pendente"
    ]
    aprovados = [
        u for u in st.session_state.usuarios if u.get("status") == "Aprovado"
    ]

    st.subheader("Solicitações Pendentes de Aprovação")

    if pendentes:
      for idx, u in enumerate(pendentes):
        col_u, col_b1, col_b2 = st.columns([3, 1, 1])
        with col_u:
          st.write(f"👤 **{u['nome']}** (Usuário: `{u['usuario']}`)")
        with col_b1:
          if st.button("✅ Aprovar", key=f"ap_{idx}", type="primary"):
            u["status"] = "Aprovado"
            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

            for p in st.session_state.integrantes:
              if p["Nome"].lower() == u["nome"].lower():
                p["Situação"] = "Ativo"
            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

            st.success(f"Acesso aprovado para {u['nome']}!")
            st.rerun()
        with col_b2:
          if st.button("❌ Recusar e Excluir", key=f"rec_{idx}"):
            # Exclui totalmente o usuário para liberar o login
            st.session_state.usuarios = [
                usr
                for usr in st.session_state.usuarios
                if usr["usuario"] != u["usuario"]
            ]
            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

            st.session_state.integrantes = [
                p
                for p in st.session_state.integrantes
                if p["Nome"].lower() != u["nome"].lower()
            ]
            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

            st.warning(
                f"Solicitação de {u['nome']} recusada. Nome de usuário liberado"
                " com sucesso!"
            )
            st.rerun()
    else:
      st.info("Nenhuma solicitação de acesso pendente no momento.")

    st.markdown("---")
    st.subheader("Usuários com Acesso Aprovado")

    if aprovados:
      df_u = pd.DataFrame(aprovados)[["nome", "usuario", "status", "is_admin"]]
      st.dataframe(df_u, use_container_width=True)

      st.markdown("### 🗑️ Excluir Conta de Usuário Aprovado")
      usuarios_normais = [u for u in aprovados if not u.get("is_admin")]
      if usuarios_normais:
        opcoes_excluir = [
            f"{u['nome']} (Usuário: {u['usuario']})" for u in usuarios_normais
        ]
        sel_usr_del = st.selectbox(
            "Selecione a conta para excluir permanentemente:", opcoes_excluir
        )

        if st.button("Excluir Conta do Usuário", type="primary"):
          usr_alvo = sel_usr_del.split("(Usuário: ")[1].replace(")", "")

          st.session_state.usuarios = [
              u for u in st.session_state.usuarios if u["usuario"] != usr_alvo
          ]
          salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

          st.session_state.integrantes = [
              p
              for p in st.session_state.integrantes
              if p["Nome"].lower() != sel_usr_del.split(" (Usuário:")[0].lower()
          ]
          salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

          st.success(
              f"Usuário `{usr_alvo}` excluído com sucesso! O nome de usuário"
              " está novamente disponível."
          )
          st.rerun()
      else:
        st.caption("Apenas a conta administradora principal está cadastrada.")
