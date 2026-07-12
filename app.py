import streamlit as st
from cadastro_atividades import cadastro_atividades_page
from configuracoes import configuracoes_page
from login import login_page
from dashboard import dashboard_page
from dashboard_view import dashboard_view
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide")

# CSS Ajustado: Removemos o padding superior do .block-container e adicionamos um espaço fixo
st.markdown("""
    <style>
    /* Força o topo da página a não cortar o conteúdo */
    .block-container {
        padding-top: 1rem !important;
    }
    /* Garante que o elemento que envolve o menu tenha altura suficiente */
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
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

    # --- MENU COM AJUSTE DE ALTURA ---
    # Colocamos um espacinho inicial (st.write) caso precise, 
    # mas o CSS acima deve resolver o corte.
    selected = option_menu(
        menu_title=None,
        options=menu_opcoes,
        icons=menu_icones,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0px!important",
                "background-color": "#ffffff",
                "border": "1px solid #e6e6e6",
                "border-radius": "10px",
                "height": "60px"  # Altura fixa para evitar cortes
            },
            "nav-link": {
                "font-size": "14px",
                "text-align": "center",
                "margin": "0px",
                "padding": "15px 10px", # Padding interno do botão
                "height": "60px"
            },
            "nav-link-selected": {
                "background-color": "#0078D7",
                "color": "white",
            },
        }
    )

    # Conteúdo principal logo após o menu
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
