import streamlit as st
from cadastro_atividades import cadastro_atividades_page
from configuracoes import configuracoes_page
from login import login_page
from dashboard import dashboard_page
from dashboard_view import dashboard_view
from streamlit_option_menu import option_menu

# Mantemos apenas o layout wide
st.set_page_config(layout="wide")

# CSS neutro (apenas para garantir largura, sem forçar o topo absoluto)
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

if "usuario_logado" not in st.session_state:
    login_page()
else:
    if st.session_state["usuario_logado"].lower() == "admin":
        menu_opcoes = ["Dashboard", "Atividades", "Configurações", "Gestão", "Sair"]
        menu_icones = ["bar-chart-line", "clipboard-data", "gear", "shield-lock", "box-arrow-right"]
    elif st.session_state["usuario_logado"].lower() == "gestor":
        menu_opcoes = ["Dashboard", "Atividades", "Gestão", "Sair"]
        menu_icones = ["bar-chart-line", "clipboard-data", "shield-lock", "box-arrow-right"]
    else:
        menu_opcoes = ["Atividades", "Sair"]
        menu_icones = ["clipboard-data", "box-arrow-right"]

    # --- MENU POSICIONADO ABAIXO DO HEADER DO STREAMLIT ---
    # Ao remover as instruções de "top: 0" e "hidden header", 
    # o Streamlit colocará este menu naturalmente logo abaixo da barra de ferramentas.
    selected = option_menu(
        menu_title=None,
        options=menu_opcoes,
        icons=menu_icones,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0px", 
                "background-color": "#ffffff",
                "border": "1px solid #e6e6e6",
                "border-radius": "10px",
                "margin-bottom": "20px"
            },
            "nav-link": {
                "font-size": "14px", 
                "text-align": "center", 
                "padding": "10px"
            },
            "nav-link-selected": {
                "background-color": "#0078D7", 
                "color": "white"
            }
        }
    )

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
