import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

def dashboard_page():
    # 🔹 Mês atual em português
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    mes_atual = meses[datetime.now().month]

    # 🔹 Título principal
    st.markdown(f"<h1 style='text-align:center; color:#1976D2;'>Painel de Desempenho - {mes_atual}</h1>", unsafe_allow_html=True)

    # 🔹 Conexão com banco
    conn = sqlite3.connect("database.db")

    # 🔹 Ranking dos 3 melhores (geral)
    query_rank = """
        SELECT usuario, COUNT(*) as total
        FROM atividades
        WHERE status = 'LEAD FECHOU'
        GROUP BY usuario
        ORDER BY total DESC
        LIMIT 3
    """
    df_rank = pd.read_sql_query(query_rank, conn)

    # 🔹 Layout em 3 colunas
    col1, col2, col3 = st.columns(3)

    # 🔹 Estilo CSS para os cards
    st.markdown("""
        <style>
        .card {
            background-color: #1976D2;
            color: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            margin-top: 15px;
        }
        .stars {
            font-size: 28px;
            margin-bottom: 15px;
            display: block;
            color: gold;
        }
        h3 {
            margin: 10px 0;
        }
        p {
            font-size: 18px;
            margin: 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # 🔹 Exibe os 3 melhores vendedores (geral)
    if len(df_rank) > 0:
        with col1:
            st.markdown(f"""
                <div class="card">
                    <div class="stars">★★★★★</div>
                    <h3>{df_rank.iloc[0]['usuario']}</h3>
                    <p>{df_rank.iloc[0]['total']} vendas</p>
                </div>
            """, unsafe_allow_html=True)
    if len(df_rank) > 1:
        with col2:
            st.markdown(f"""
                <div class="card">
                    <div class="stars">★★★☆☆</div>
                    <h3>{df_rank.iloc[1]['usuario']}</h3>
                    <p>{df_rank.iloc[1]['total']} vendas</p>
                </div>
            """, unsafe_allow_html=True)
    if len(df_rank) > 2:
        with col3:
            st.markdown(f"""
                <div class="card">
                    <div class="stars">★☆☆☆☆</div>
                    <h3>{df_rank.iloc[2]['usuario']}</h3>
                    <p>{df_rank.iloc[2]['total']} vendas</p>
                </div>
            """, unsafe_allow_html=True)

    st.write("---")

    # 🔹 Data corrente (ISO)
    data_corrente = datetime.now().strftime("%Y-%m-%d")

    # 🔹 Grid completo do dia corrente
    query_grid = """
        SELECT 
            data AS 'Data',
            usuario AS 'Vendedora',
            COUNT(*) AS 'Total',
            SUM(CASE WHEN status='LEAD FECHOU' THEN 1 ELSE 0 END) AS 'Total de Vendas'
        FROM atividades
        WHERE date(data) = date(?)
        GROUP BY data, usuario
        ORDER BY usuario
    """
    df_grid = pd.read_sql_query(query_grid, conn, params=[data_corrente])

    # 🔹 Melhor vendedor do dia (card laranja)
    if not df_grid.empty:
        melhor_vendedora = df_grid.loc[df_grid["Total de Vendas"].idxmax()]
        st.markdown(f"""
            <div class="card" style="background-color:#FF9800; color:white; margin-top:20px;">
                <div class="stars">🏆</div>
                <h3>Melhor do Dia: {melhor_vendedora['Vendedora']}</h3>
                <p>{melhor_vendedora['Total de Vendas']} vendas</p>
                <p>Total de Atividades: {melhor_vendedora['Total']}</p>
            </div>
        """, unsafe_allow_html=True)

    # 🔹 Exibe o grid completo
    st.subheader(f"📋 Atividades do Dia {datetime.now().strftime('%d/%m/%Y')}")
    st.dataframe(df_grid, use_container_width=True, height=400)

    st.write("---")

    # 🔹 Gráficos de donut por vendedora (dia)
    st.subheader(f"🍩 Desempenho por Vendedora - Dia {datetime.now().strftime('%d/%m/%Y')}")
    if not df_grid.empty:
        for _, row in df_grid.iterrows():
            vendedora = row["Vendedora"]
            total = row["Total"]
            vendas = row["Total de Vendas"]
            dados = pd.DataFrame({
                "Categoria": ["Total de Atividades", "Total de Vendas"],
                "Quantidade": [total, vendas]
            })
            fig = px.pie(
                dados,
                names="Categoria",
                values="Quantidade",
                hole=0.5,
                color="Categoria",
                color_discrete_map={
                    "Total de Atividades": "#1976D2",
                    "Total de Vendas": "#FF9800"
                },
                title=f"{vendedora} - Dia {datetime.now().strftime('%d/%m/%Y')}"
            )
            fig.update_traces(textinfo="value+label", textfont_size=20, pull=[0, 0.05])
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum dado encontrado para o dia corrente.")

    st.write("---")

    # 🔹 Grid do mês corrente (ISO)
    mes_atual_num = f"{datetime.now().month:02d}"
    ano_atual = str(datetime.now().year)
    query_mes = """
        SELECT 
            usuario AS 'Vendedora',
            COUNT(*) AS 'Total',
            SUM(CASE WHEN status='LEAD FECHOU' THEN 1 ELSE 0 END) AS 'Total de Vendas'
        FROM atividades
        WHERE strftime('%m', data) = ? AND strftime('%Y', data) = ?
        GROUP BY usuario
        ORDER BY usuario
    """
    df_mes = pd.read_sql_query(query_mes, conn, params=[mes_atual_num, ano_atual])
    conn.close()

    # 🔹 Gráficos de donut por vendedora (mês)
    st.subheader(f"🍩 Desempenho por Vendedora - Mês de {mes_atual}")
    if not df_mes.empty:
        for _, row in df_mes.iterrows():
            vendedora = row["Vendedora"]
            total = row["Total"]
            vendas = row["Total de Vendas"]
            dados = pd.DataFrame({
                "Categoria": ["Total de Atividades", "Total de Vendas"],
                "Quantidade": [total, vendas]
            })
            fig = px.pie(
                dados,
                names="Categoria",
                values="Quantidade",
                hole=0.5,
                color="Categoria",
                color_discrete_map={
                    "Total de Atividades": "#2196F3",
                    "Total de Vendas": "#F57C00"
                },
                title=f"{vendedora} - Mês de {mes_atual}"
            )
            fig.update_traces(textinfo="value+label", textfont_size=20, pull=[0, 0.05])
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum dado encontrado para o mês corrente.")
