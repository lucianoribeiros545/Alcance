import streamlit as st
import os
from cadastro_atividades import cadastro_atividades_page
from configuracoes import configuracoes_page
from login import login_page
from dashboard import dashboard_page   # ✅ Importa o módulo existente
from dashboard_view import dashboard_view   # ✅ Importa o novo módulo
from streamlit_option_menu import option_menu

st.set_page_config(page_title="FAST TD", layout="wide")

# 🔹 Controle de login
if "usuario_logado" not in st.session_state:
    login_page()
else:
    #logo_path = os.path.join("imagens", "logo.png")
    if os.path.exists("imagens/logo.png"):
        st.image("imagens/logo.png", width=120)
    else:
        st.warning("Logo não encontrada. Verifique se 'imagens/logo.png' existe.")

    # Cabeçalho
    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=120)
    with col2:
        st.markdown("<h1 style='text-align:center;'></h1>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<p style='text-align:right;'>👋 Olá, {st.session_state['usuario_logado']}!</p>", unsafe_allow_html=True)

    # 🔹 Menu conforme perfil
    if st.session_state["usuario_logado"].lower() == "admin":
       menu_opcoes = ["📈 Dashboard", "📋 Atividades", "⚙️ Configurações", "📈 Dashboard View++", "🚪 Sair"]
       menu_icones = ["bar-chart", "list-task", "gear", "person-lines-fill", "door-closed"]

    elif st.session_state["usuario_logado"].lower() == "gestor":
       menu_opcoes = ["📈 Dashboard", "📋 Atividades", "📈 Dashboard View++", "🚪 Sair"]
       menu_icones = ["bar-chart", "list-task", "person-lines-fill", "door-closed"]

    else:
       menu_opcoes = ["📋 Atividades", "🚪 Sair"]
       menu_icones = ["list-task", "door-closed"]

    selected = option_menu(
        menu_title=None,
        options=menu_opcoes,
        icons=menu_icones,
        orientation="horizontal",
        styles={
            "container": {"padding": "5px", "background-color": "#1e3c72"},
            "icon": {"color": "white", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "5px",
                "color": "white",
                "font-weight": "normal"
            },
            "nav-link-selected": {"background-color": "#0078D7"},
        }
    )

    st.write("---")  # separador abaixo do menu

    # 🔹 Conteúdo das abas
    if selected == "📈 Dashboard":
        st.subheader("📈 Módulo de Dashboard")
        dashboard_page()   # ✅ Chama o dashboard existente

    elif selected == "📋 Atividades":
        st.subheader("📋 Minhas Atividades")
        cadastro_atividades_page()

    elif selected == "⚙️ Configurações":
        st.subheader("⚙️ Módulo de Configurações")
        configuracoes_page()

    elif selected == "📈 Dashboard View++":   # ✅ Nome idêntico ao menu_opcoes
        st.subheader("📈 Módulo Gestão")
        dashboard_view()   # ✅ Chama o novo dashboard

    elif selected == "🚪 Sair":
        st.subheader("🚪 Encerrar Sessão")
        if st.button("Encerrar sessão"):
            st.session_state.clear()
            st.success("👋 Sessão encerrada com sucesso!")
            st.rerun()
