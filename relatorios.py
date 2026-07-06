import streamlit as st

def relatorios_page():
    st.markdown("<h1>Relatórios</h1>", unsafe_allow_html=True)
    st.write("Aqui você pode visualizar e exportar relatórios das atividades cadastradas.")
    st.button("Gerar Relatório")
