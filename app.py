import streamlit as st
from cadastro_atividades import cadastro_atividades_page
from configuracoes import configuracoes_page
from login import login_page
from dashboard import dashboard_page
from dashboard_view import dashboard_view
from streamlit_option_menu import option_menu

st.set_page_config(page_title="FAST TD", layout="wide")

# CSS para remover o espaço extra do topo e dar um estilo moderno ao menu
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    div.row-widget.stRadio > div{flex-direction:row;}
    </style>
""", unsafe_allow_html=True)

if "usuario_logado" not in st.session_state:
    login_page()
else:
    # Definição do menu
    if st.session_state["usuario_logado"].lower() == "admin":
        menu_opcoes = ["Dashboard", "Atividades", "Configurações", "Gestão", "Sair"]
        menu_icones = ["bar-chart-line", "clipboard-data", "gear", "shield-lock", "box-arrow-right"]
    elif st.session_state["usuario_logado"].lower() == "gestor":
        menu_opcoes = ["Dashboard", "Atividades", "Gestão", "Sair"]
        menu_icones = ["bar-chart-line", "clipboard-data", "shield-lock", "box-arrow-right"]
    else:
        menu_opcoes = ["Atividades", "Sair"]
        menu_icones = ["clipboard-data", "box-arrow-right"]

    # Menu com visual "Modern Card"
    selected = option_menu(
        menu_title=None,
        options=menu_opcoes,
        icons=menu_icones,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "2px", 
                "background-color": "#ffffff",
                "border": "1px solid #e6e6e6",
                "border-radius": "10px",
                "box-shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
            },
            "icon": {"color": "#0078D7", "font-size": "17px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "center",
                "margin": "0px 2px",
                "padding": "10px 15px",
                "color": "#4a4a4a",
                "border-radius": "8px",
            },
            "nav-link-selected": {
                "background-color": "#0078D7",
                "color": "white",
                "font-weight": "600",
            },
        }
    )

    # Mensagem de Boas-vindas abaixo do menu
    st.markdown(f"""
        <div style="margin-top: 15px; margin-bottom: 20px; color: #555; font-size: 1.1rem;">
            Olá, <b>{st.session_state['usuario_logado']}</b>! Bem-vindo ao <b>FAST TD</b>.
        </div>
    """, unsafe_allow_html=True)

    # Conteúdo
    if selected == "Dashboard":
        dashboard_page()
    elif selected == "Atividades":
        cadastro_atividades_page()
    elif selected == "Configurações":
        configuracoes_page()
    elif selected == "Gestão":
        dashboard_view()
    elif selected == "Sair":
        if st.button("Confirmar saída"):
            st.session_state.clear()
            st.rerun()
