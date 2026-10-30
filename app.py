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
    page_title="Central de Pesquisa - Gestão do Laboratório",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILIZAÇÃO VISUAL (AZUL CLARO, BRANCO E CARDS) ---
st.markdown(
    """
    <style>
    /* Fundo principal da aplicação em azul super claro */
    .stApp {
        background-color: #F4F8FB;
    }
    /* Estilo da barra lateral (Sidebar) em azul claro */
    [data-testid="stSidebar"] {
        background-color: #EBF3FA;
        border-right: 1px solid #D6E4F0;
    }
    /* Cor dos títulos principais */
    h1, h2, h3 {
        color: #0D47A1 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Subtítulos de seções na barra lateral */
    .sidebar-section {
        font-size: 0.75rem;
        font-weight: 700;
        color: #5C768D;
        text-transform: uppercase;
        margin-top: 1.2rem;
        margin-bottom: 0.3rem;
        letter-spacing: 0.05em;
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
    /* Cards brancos elegantes */
    .css-card {
        background-color: white;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SISTEMA DE PERSISTÊNCIA DE DADOS ---
ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_ARQUIVOS = "arquivos.json"
PASTA_UPLOADS = "uploads"

os.makedirs(PASTA_UPLOADS, exist_ok=True)

CATEGORIAS_PADRAO = [
    "Iniciação Científica",
    "Mestrado",
    "Doutorado",
    "Pós-Doutorado",
    "Orientador",
    "Técnico / Pesquisador",
]

CATEGORIAS_ARQUIVOS = [
    "Protocolo / POP",
    "Artigo Científico",
    "Relatório de Pesquisa",
    "Manual de Equipamento",
    "Ficha de Segurança (FISPQ)",
    "Outro Documento",
]


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


# Inicializa os dados no session_state
if "integrantes" not in st.session_state:
  st.session_state.integrantes = carregar_dados(
      ARQUIVO_INTEGRANTES,
      [{
          "Nome": "Eliane Pereira Cipolatti",
          "Categoria": "Orientador",
          "Vínculo": "UFRRJ - Engenharia de Alimentos",
          "Telefone": "(21) 99999-9999",
          "Email": "eliane@ufrrj.br",
          "Situação": "Ativo",
      }],
  )

if "agenda" not in st.session_state:
  st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, [])

if "arquivos_db" not in st.session_state:
  st.session_state.arquivos_db = carregar_dados(ARQUIVO_ARQUIVOS, [])

usuario_admin_padrao = [{
    "nome": "Administrador",
    "usuario": "admin",
    "senha": "123",
    "categoria": "Orientador",
    "vinculo": "UFRRJ",
    "telefone": "(21) 99999-9999",
    "email": "admin@ufrrj.br",
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

  with aba_cadastro:
    st.subheader("Pedir Permissão de Acesso")
    with st.form("form_solicitar_acesso"):
      novo_nome = st.text_input("Nome Completo *")
      nova_categoria = st.selectbox("Categoria *", CATEGORIAS_PADRAO)
      novo_vinculo = st.text_input(
          "Vínculo / Curso *", "UFRRJ - Engenharia de Alimentos"
      )
      novo_telefone = st.text_input("Telefone para Contato *")
      novo_email = st.text_input("E-mail para Contato *")
      novo_usuario = st.text_input("Usuário Desejado (ex: gabriela) *")
      nova_senha = st.text_input("Criar Senha *", type="password")
      btn_solicitar = st.form_submit_button("Enviar Solicitação")

      if btn_solicitar:
        if not (
            novo_nome
            and novo_usuario
            and nova_senha
            and novo_vinculo
            and novo_telefone
            and novo_email
        ):
          st.error("Por favor, preencha todos os campos obrigatórios (*).")
        else:
          usr_clean = novo_usuario.strip().lower()

          existe = any(
              u["usuario"].lower() == usr_clean
              and u.get("status") in ["Aprovado", "Pendente"]
              for u in st.session_state.usuarios
          )

          if existe:
            st.error(
                "Este nome de usuário já está em uso. Escolha outro nome de"
                " usuário."
            )
          else:
            st.session_state.usuarios = [
                u
                for u in st.session_state.usuarios
                if u["usuario"].lower() != usr_clean
            ]

            novo_user_dict = {
                "nome": novo_nome.strip(),
                "usuario": novo_usuario.strip(),
                "senha": nova_senha,
                "categoria": nova_categoria,
                "vinculo": novo_vinculo.strip(),
                "telefone": novo_telefone.strip(),
                "email": novo_email.strip(),
                "status": "Pendente",
                "is_admin": False,
            }
            st.session_state.usuarios.append(novo_user_dict)
            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

            integrante_existente = next(
                (
                    p
                    for p in st.session_state.integrantes
                    if p["Nome"].lower() == novo_nome.strip().lower()
                ),
                None,
            )
            if integrante_existente:
              integrante_existente["Categoria"] = nova_categoria
              integrante_existente["Vínculo"] = novo_vinculo.strip()
              integrante_existente["Telefone"] = novo_telefone.strip()
              integrante_existente["Email"] = novo_email.strip()
              integrante_existente["Situação"] = "Pendente"
            else:
              st.session_state.integrantes.append({
                  "Nome": novo_nome.strip(),
                  "Categoria": nova_categoria,
                  "Vínculo": novo_vinculo.strip(),
                  "Telefone": novo_telefone.strip(),
                  "Email": novo_email.strip(),
                  "Situação": "Pendente",
              })
            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

            st.success(
                "Solicitação enviada com sucesso! Seu nome consta na tabela de"
                " integrantes como 'Pendente'. Aguarde a aprovação do"
                " administrador."
            )

# --- ÁREA LOGADA (SISTEMA PRINCIPAL COM ESTRUTURA IGUAL À IMAGEM) ---
else:
  usuario_atual = st.session_state.usuario_logado
  is_admin = usuario_atual.get("is_admin", False)

  # Barra Lateral Estilizada com Seções Identicas à Imagem
  st.sidebar.title("🧪 Central LTAB")
  st.sidebar.caption("Laboratório de Pesquisa & Desenvolvimento")

  st.sidebar.markdown(
      '<div class="sidebar-section">VISÃO GERAL</div>', unsafe_allow_html=True
  )
  opcoes_menu = ["🏠 Início / Visão Geral", "📅 Agenda & Compromissos"]

  st.sidebar.markdown(
      '<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>',
      unsafe_allow_html=True,
  )
  if is_admin:
    opcoes_menu.append("👥 Gestão de Integrantes")
    opcoes_menu.append("🔑 Central de Aprovações")
  else:
    opcoes_menu.append("👥 Equipe do Laboratório")

  st.sidebar.markdown(
      '<div class="sidebar-section">FERRAMENTAS & DOCUMENTOS</div>',
      unsafe_allow_html=True,
  )
  opcoes_menu.append("🏷️ Gerar QR Code de Amostras")
  opcoes_menu.append("📁 Repositório de Arquivos")

  st.sidebar.markdown(
      '<div class="sidebar-section">MINHA CONTA</div>', unsafe_allow_html=True
  )
  opcoes_menu.append("👤 Meu Perfil")

  menu_selecionado = st.sidebar.radio("Navegação:", opcoes_menu)

  st.sidebar.markdown("---")
  st.sidebar.write(f"Usuário: **{usuario_atual['nome']}**")
  if is_admin:
    st.sidebar.caption("🟢 **Administrador**")
  else:
    st.sidebar.caption("🔵 Pesquisador")

  if st.sidebar.button("🚪 Sair da conta"):
    st.session_state.usuario_logado = None
    st.rerun()

  # --- 1. VISÃO GERAL (DESIGN DE PAINEL COM CARDS) ---
  if menu_selecionado == "🏠 Início / Visão Geral":
    st.title("Visão geral")
    st.caption("Informações e recursos do Laboratório de Pesquisa.")

    # Bloco de Avisos Importantes
    with st.container():
      st.markdown(
          """
            <div style="background-color: #FFF9E6; border-left: 5px solid #FFC107; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #856404;">📣 AVISOS IMPORTANTES</h4>
                <p style="margin:5px 0 0 0; color: #856404;">
                    Mantenham o Lattes atualizado e lembrem-se de registrar o uso das bancadas e equipamentos na agenda.
                </p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    col_m1, col_m2, col_m3 = st.columns(3)
    ativos_cnt = sum(
        1
        for p in st.session_state.integrantes
        if p.get("Situação") == "Ativo"
    )
    alunos_cnt = sum(
        1
        for p in st.session_state.integrantes
        if p.get("Categoria") != "Orientador" and p.get("Situação") == "Ativo"
    )
    agenda_cnt = len(st.session_state.agenda)

    col_m1.metric("Integrantes Ativos", ativos_cnt)
    col_m2.metric("Pesquisadores / Alunos", alunos_cnt)
    col_m3.metric("Agendamentos Ativos", agenda_cnt)

    st.markdown("---")

    col_esq, col_dir = st.columns([1.2, 1])

    with col_esq:
      st.subheader("📋 Tabela de Integrantes do Laboratório")
      if st.session_state.integrantes:
        df_int = pd.DataFrame(st.session_state.integrantes)
        cols_viz = [
            "Nome",
            "Categoria",
            "Vínculo",
            "Telefone",
            "Email",
            "Situação",
        ]
        for col in cols_viz:
          if col not in df_int.columns:
            df_int[col] = "-"
        st.dataframe(df_int[cols_viz], use_container_width=True)
      else:
        st.info("Nenhum integrante cadastrado.")

    with col_dir:
      st.subheader("📅 Próximos Compromissos")
      if st.session_state.agenda:
        df_ag = pd.DataFrame(st.session_state.agenda)
        st.dataframe(
            df_ag[["Data", "Início", "Título", "Responsável"]].tail(5),
            use_container_width=True,
        )
      else:
        st.info("Nenhum compromisso agendado recentemente.")

  # --- 2. AGENDA & COMPROMISSOS ---
  elif menu_selecionado == "📅 Agenda & Compromissos":
    st.title("📅 Agenda do Laboratório")

    col_esq, col_dir = st.columns([1, 1.2])

    with col_esq:
      st.subheader("➕ Agendar Horário / Equipamento")
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
            "Equipamento / Bancada",
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
      st.subheader("🗓️ Consultar Compromissos por Data")
      data_consulta = st.date_input(
          "Selecione o dia:", datetime.now().date(), key="dt_cons"
      )
      data_str = data_consulta.strftime("%Y-%m-%d")

      eventos_dia = [
          e for e in st.session_state.agenda if e["Data"] == data_str
      ]

      if eventos_dia:
        for ev in eventos_dia:
          with st.expander(
              f"⏰ {ev['Início']} - {ev['Término']} | {ev['Título']}"
          ):
            st.write(f"**Local:** {ev['Equipamento']}")
            st.write(f"**Responsável:** {ev['Responsável']}")
            st.write(f"**Observações:** {ev['Observações']}")
      else:
        st.info("Nenhum agendamento para este dia.")

    st.markdown("---")
    st.subheader("📋 Lista Completa de Agendamentos")

    if st.session_state.agenda:
      df_ag_full = pd.DataFrame(st.session_state.agenda)
      st.dataframe(
          df_ag_full[
              [
                  "Data",
                  "Início",
                  "Término",
                  "Título",
                  "Equipamento",
                  "Responsável",
                  "Observações",
              ]
          ].sort_values(by=["Data", "Início"]),
          use_container_width=True,
      )

      if is_admin:
        st.markdown("### ❌ Cancelar Compromisso")
        opcoes_c = [
            f"ID {e['ID']} - {e['Data']} [{e['Início']}] {e['Título']}"
            for e in st.session_state.agenda
        ]
        sel_c = st.selectbox("Selecione o agendamento:", opcoes_c)
        if st.button("Remover Agendamento", type="primary"):
          id_del = int(sel_c.split(" ")[1])
          st.session_state.agenda = [
              e for e in st.session_state.agenda if e["ID"] != id_del
          ]
          salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
          st.success("Agendamento cancelado!")
          st.rerun()

  # --- 3. GESTÃO DE INTEGRANTES / EQUIPE ---
  elif menu_selecionado in [
      "👥 Gestão de Integrantes",
      "👥 Equipe do Laboratório",
  ]:
    st.title("👥 Integrantes do Laboratório")

    if is_admin:
      st.subheader("➕ Cadastrar ou Editar Integrante Manualmente")
      with st.form("form_cad_int"):
        nome = st.text_input("Nome Completo")
        categoria = st.selectbox("Categoria", CATEGORIAS_PADRAO)
        vinculo = st.text_input(
            "Vínculo / Curso", "UFRRJ - Engenharia de Alimentos"
        )
        telefone = st.text_input("Telefone de Contato")
        email = st.text_input("E-mail de Contato")
        situacao = st.selectbox("Situação", ["Ativo", "Pendente", "Inativo"])
        btn_salv = st.form_submit_button("Salvar Integrante")

        if btn_salv and nome:
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
            existente["Telefone"] = telefone
            existente["Email"] = email
            existente["Situação"] = situacao
          else:
            st.session_state.integrantes.append({
                "Nome": nome.strip(),
                "Categoria": categoria,
                "Vínculo": vinculo,
                "Telefone": telefone,
                "Email": email,
                "Situação": situacao,
            })

          salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
          st.success(f"Integrante {nome} salvo com sucesso!")
          st.rerun()

      st.markdown("---")
      st.subheader("🗑️ Remover Integrante")
      lista_nomes = [p["Nome"] for p in st.session_state.integrantes]
      if lista_nomes:
        sel_rem = st.selectbox("Selecione quem deseja remover:", lista_nomes)
        if st.button("Excluir das Listas", type="primary"):
          st.session_state.integrantes = [
              p for p in st.session_state.integrantes if p["Nome"] != sel_rem
          ]
          salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

          st.session_state.usuarios = [
              u
              for u in st.session_state.usuarios
              if u["nome"].lower() != sel_rem.lower()
          ]
          salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

          st.success(f"Integrante '{sel_rem}' removido!")
          st.rerun()

    else:
      df_eq = pd.DataFrame(st.session_state.integrantes)
      st.dataframe(df_eq, use_container_width=True)

  # --- 4. FERRAMENTA: GERAR QR CODE DE AMOSTRAS ---
  elif menu_selecionado == "🏷️ Gerar QR Code de Amostras":
    st.title("🧪 Gerador de QR Code de Amostras")

    col_f, col_q = st.columns([1, 1])

    with col_f:
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

      tel_resp = "-"
      email_resp = "-"

      if sel_resp == "Outro / Digitar manualmente...":
        responsavel = st.text_input(
            "Nome do Pesquisador", "Gabriela Mendes Farias Matos"
        )
        tel_resp = st.text_input("Telefone do Responsável")
        email_resp = st.text_input("E-mail do Responsável")
      else:
        responsavel = sel_resp
        integrante_sel = next(
            (
                p
                for p in st.session_state.integrantes
                if p["Nome"] == sel_resp
            ),
            None,
        )
        if integrante_sel:
          tel_resp = integrante_sel.get("Telefone", "-")
          email_resp = integrante_sel.get("Email", "-")
          st.info(
              f"📞 **Contatos do Responsável:**\n- **Telefone:**"
              f" {tel_resp}\n- **E-mail:** {email_resp}"
          )

      localizacao = st.text_input(
          "Local de Armazenamento", "Freezer -20°C / Caixa 3 / Posição B4"
      )
      descricao = st.text_area(
          "Descrição Detalhada / Protocolo",
          value=(
              "Extrato obtido via fermentação estado sólido. Tampão fosfato"
              " 0.1M pH 7.0."
          ),
          height=100,
      )
      gerar = st.button("Gerar Etiqueta QR Code")

    with col_q:
      if gerar or id_amostra:
        conteudo_qr = (
            "=== FICHA DA AMOSTRA ===\n"
            f"ID: {id_amostra}\n"
            f"NOME: {nome_amostra}\n"
            f"RESPONSÁVEL: {responsavel}\n"
            f"CONTATO: Tel {tel_resp} | Email {email_resp}\n"
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

        st.image(img_bytes, caption=f"QR Code: {id_amostra}", width=250)
        st.download_button(
            label="Baixar QR Code (PNG)",
            data=img_bytes,
            file_name=f"QR_{id_amostra}.png",
            mime="image/png",
        )

  # --- 5. NOVA ÁREA: REPOSITÓRIO DE ARQUIVOS E DOCUMENTOS ---
  elif menu_selecionado == "📁 Repositório de Arquivos":
    st.title("📁 Central de Arquivos & Documentos do Laboratório")

    aba_docs, aba_upload = st.tabs(
        ["📚 Documentos Aprovados", "📥 Enviar Novo Arquivo"]
    )

    # Aba de Consulta e Download
    with aba_docs:
      st.subheader("Documentos e POPs Disponíveis")
      aprovados_arq = [
          a
          for a in st.session_state.arquivos_db
          if a.get("status") == "Aprovado"
      ]

      if aprovados_arq:
        for doc in aprovados_arq:
          with st.container():
            st.markdown(
                f"""
                        <div class="css-card">
                            <h4 style="margin:0; color:#0D47A1;">📄 {doc['titulo']}</h4>
                            <p style="margin:4px 0; color:#555;"><b>Categoria:</b> {doc['categoria']} | <b>Enviado por:</b> {doc['autor']} em {doc['data']}</p>
                            <p style="margin:4px 0; color:#666;"><i>{doc['descricao']}</i></p>
                        </div>
                        """,
                unsafe_allow_html=True,
            )

            # Botão para baixar o arquivo
            caminho_arq = doc.get("caminho")
            if caminho_arq and os.path.exists(caminho_arq):
              with open(caminho_arq, "rb") as f:
                bytes_f = f.read()
              st.download_button(
                  label=f"⬇️ Baixar {doc['nome_original']}",
                  data=bytes_f,
                  file_name=doc["nome_original"],
                  key=f"dl_{doc['id']}",
              )
            else:
              st.caption("Ficheiro não encontrado no servidor.")
            st.markdown("---")
      else:
        st.info(
            "Nenhum documento aprovado no momento. Envie um arquivo na aba ao"
            " lado!"
        )

    # Aba de Envio de Arquivo pelo Usuário
    with aba_upload:
      st.subheader("Enviar Arquivo para Avaliação do Administrador")
      with st.form("form_upload_arq"):
        tit_doc = st.text_input("Título do Documento *")
        cat_doc = st.selectbox("Categoria do Documento *", CATEGORIAS_ARQUIVOS)
        desc_doc = st.text_area("Descrição / Detalhes do Arquivo *", height=80)
        arq_up = st.file_uploader(
            "Selecione o Ficheiro (PDF, DOCX, XLSX, PNG, JPG) *",
            type=["pdf", "docx", "xlsx", "png", "jpg", "csv", "txt"],
        )

        btn_enviar_doc = st.form_submit_button("Enviar Documento")

        if btn_enviar_doc:
          if not (tit_doc and desc_doc and arq_up):
            st.error("Preencha todos os campos e selecione um ficheiro.")
          else:
            # Salva o arquivo em disco
            data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_seguro = f"{data_str}_{arq_up.name}"
            caminho_final = os.path.join(PASTA_UPLOADS, nome_seguro)

            with open(caminho_final, "wb") as f:
              f.write(arq_up.getbuffer())

            novo_registro_arq = {
                "id": len(st.session_state.arquivos_db) + 1,
                "titulo": tit_doc.strip(),
                "categoria": cat_doc,
                "descricao": desc_doc.strip(),
                "nome_original": arq_up.name,
                "caminho": caminho_final,
                "autor": usuario_atual["nome"],
                "data": datetime.now().strftime("%d/%m/%Y"),
                "status": "Pendente",
            }

            st.session_state.arquivos_db.append(novo_registro_arq)
            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)

            st.success(
                "Documento enviado com sucesso! Ele aparecerá na biblioteca"
                " assim que for aprovado pelo Administrador."
            )

  # --- 6. CENTRAL DE APROVAÇÕES (EXCLUSIVO ADMIN) ---
  elif menu_selecionado == "🔑 Central de Aprovações" and is_admin:
    st.title("🔑 Central de Aprovações (Administrador)")

    tab_acessos, tab_perfis, tab_files = st.tabs(
        ["1. Novos Acessos", "2. Alterações de Perfil", "3. Aprovar Arquivos"]
    )

    # Tab 1: Novos Acessos
    with tab_acessos:
      pend_acessos = [
          u for u in st.session_state.usuarios if u.get("status") == "Pendente"
      ]
      if pend_acessos:
        for idx, u in enumerate(pend_acessos):
          c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
          with c_inf:
            st.write(f"👤 **{u['nome']}** (Usuário: `{u['usuario']}`)")
            st.caption(
                f"Cat: {u.get('categoria','-')} | Tel: {u.get('telefone','-')} |"
                f" Email: {u.get('email','-')}"
            )
          with c_b1:
            if st.button("✅ Aprovar", key=f"ap_usr_{idx}", type="primary"):
              u["status"] = "Aprovado"
              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

              for p in st.session_state.integrantes:
                if p["Nome"].lower() == u["nome"].lower():
                  p["Situação"] = "Ativo"
                  p["Categoria"] = u.get("categoria", p["Categoria"])
                  p["Telefone"] = u.get("telefone", p.get("Telefone", "-"))
                  p["Email"] = u.get("email", p.get("Email", "-"))

              salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
              st.success(f"Acesso aprovado para {u['nome']}!")
              st.rerun()
          with c_b2:
            if st.button("❌ Recusar", key=f"rec_usr_{idx}"):
              st.session_state.usuarios = [
                  usr
                  for usr in st.session_state.usuarios
                  if usr["usuario"] != u["usuario"]
              ]
              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
              st.warning(f"Solicitação de {u['nome']} removida.")
              st.rerun()
      else:
        st.info("Nenhuma solicitação de novo acesso pendente.")

    # Tab 2: Alterações de Perfil
    with tab_perfis:
      pend_perfis = [
          u for u in st.session_state.usuarios if u.get("pendente_atualizacao")
      ]
      if pend_perfis:
        for idx, u in enumerate(pend_perfis):
          p_data = u["pendente_atualizacao"]
          c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
          with c_inf:
            st.write(f"👤 **{u['nome']}** (`{u['usuario']}`)")
            st.caption(
                f"Novo Tel: {p_data.get('telefone')} | Novo Email:"
                f" {p_data.get('email')}"
            )
          with c_b1:
            if st.button(
                "✅ Aprovar Mudança", key=f"ap_prf_{idx}", type="primary"
            ):
              u["categoria"] = p_data.get("categoria")
              u["vinculo"] = p_data.get("vinculo")
              u["telefone"] = p_data.get("telefone")
              u["email"] = p_data.get("email")
              del u["pendente_atualizacao"]

              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

              for p in st.session_state.integrantes:
                if p["Nome"].lower() == u["nome"].lower():
                  p["Categoria"] = u["categoria"]
                  p["Vínculo"] = u["vinculo"]
                  p["Telefone"] = u["telefone"]
                  p["Email"] = u["email"]

              salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
              st.success(f"Perfil de {u['nome']} atualizado!")
              st.rerun()
          with c_b2:
            if st.button("❌ Recusar", key=f"rec_prf_{idx}"):
              del u["pendente_atualizacao"]
              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
              st.warning("Mudança recusada.")
              st.rerun()
      else:
        st.info("Nenhuma alteração de perfil pendente.")

    # Tab 3: Aprovação de Arquivos
    with tab_files:
      pend_arquivos = [
          a
          for a in st.session_state.arquivos_db
          if a.get("status") == "Pendente"
      ]
      if pend_arquivos:
        for idx, doc in enumerate(pend_arquivos):
          c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
          with c_inf:
            st.write(f"📄 **{doc['titulo']}** ({doc['categoria']})")
            st.caption(
                f"Enviado por: {doc['autor']} | Ficheiro:"
                f" {doc['nome_original']}"
            )
            st.caption(f"Descrição: {doc['descricao']}")

          with c_b1:
            if st.button(
                "✅ Aprovar Ficheiro", key=f"ap_file_{idx}", type="primary"
            ):
              doc["status"] = "Aprovado"
              salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
              st.success(
                  f"Ficheiro '{doc['titulo']}' aprovado para publicação!"
              )
              st.rerun()
          with c_b2:
            if st.button("❌ Apagar Ficheiro", key=f"rec_file_{idx}"):
              if os.path.exists(doc.get("caminho", "")):
                os.remove(doc["caminho"])
              st.session_state.arquivos_db = [
                  item
                  for item in st.session_state.arquivos_db
                  if item["id"] != doc["id"]
              ]
              salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
              st.warning("Ficheiro recusado e apagado.")
              st.rerun()
      else:
        st.info("Nenhum arquivo pendente de aprovação.")

  # --- 7. MEU PERFIL ---
  elif menu_selecionado == "👤 Meu Perfil":
    st.title("👤 Meu Perfil e Configurações")

    st.subheader("Meus Dados Registrados")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
      st.write(f"**Nome:** {usuario_atual.get('nome')}")
      st.write(f"**Usuário:** `{usuario_atual.get('usuario')}`")
      st.write(f"**Categoria:** {usuario_atual.get('categoria', '-')}")
    with c_p2:
      st.write(f"**Vínculo:** {usuario_atual.get('vinculo', '-')}")
      st.write(f"**Telefone:** {usuario_atual.get('telefone', '-')}")
      st.write(f"**E-mail:** {usuario_atual.get('email', '-')}")

    st.markdown("---")
    st.subheader("✏️ Solicitar Alteração de Dados ao Administrador")

    with st.form("form_edit_perfil"):
      nova_cat = st.selectbox("Categoria", CATEGORIAS_PADRAO)
      novo_vinc = st.text_input(
          "Vínculo", value=usuario_atual.get("vinculo", "UFRRJ")
      )
      novo_tel = st.text_input(
          "Telefone (Obrigatório) *", value=usuario_atual.get("telefone", "")
      )
      novo_email = st.text_input(
          "E-mail (Obrigatório) *", value=usuario_atual.get("email", "")
      )

      btn_env_prof = st.form_submit_button("Enviar Alterações para Aprovação")

      if btn_env_prof:
        if not (novo_tel.strip() and novo_email.strip()):
          st.error("Preencha Telefone e E-mail.")
        else:
          dados_m = {
              "categoria": nova_cat,
              "vinculo": novo_vinc.strip(),
              "telefone": novo_tel.strip(),
              "email": novo_email.strip(),
          }

          usuario_atual["pendente_atualizacao"] = dados_m
          for u in st.session_state.usuarios:
            if u["usuario"] == usuario_atual["usuario"]:
              u["pendente_atualizacao"] = dados_m
              break

          salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
          st.success("Solicitação enviada ao Administrador!")
          st.rerun()
