import streamlit as st
import sqlite3
import pandas as pd

def listas_suspensas_page():
    st.markdown("<h1>Manutenção de Listas Suspensas</h1>", unsafe_allow_html=True)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Carregar todos os registros da tabela listas
    df = pd.read_sql_query("SELECT id, campo, valor FROM listas", conn)

    st.write("### Itens cadastrados")

    # Exibir grid editável
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="listas_grid",
        column_config={
            "campo": st.column_config.TextColumn("Campo"),
            "valor": st.column_config.TextColumn("Valor"),
        }
    )

    # Botão para salvar alterações
    if st.button("Salvar alterações"):
        cursor.execute("DELETE FROM listas")  # limpa tabela
        for _, row in edited_df.iterrows():
            cursor.execute("INSERT INTO listas (campo, valor) VALUES (?, ?)", (row["campo"], row["valor"]))
        conn.commit()
        st.success("✅ Alterações salvas com sucesso!")
        st.rerun()

    conn.close()
