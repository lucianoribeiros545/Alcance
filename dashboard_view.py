import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar
import numpy as np
import requests

# 🔹 Configuração Supabase
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"

endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def dashboard_view():
    st.markdown("<h1 style='text-align:center;'>📈 Dashboard Gerencial</h1>", unsafe_allow_html=True)
    # 🔹 Carregar dados do Supabase
    response = requests.get(endpoint, headers=headers)
    df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()

    # Converte datas
    for col in ["data", "previsao", "data_cadastro"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    # ✅ Mapeamento de status numéricos para nomes legíveis
    status_map = {
        0: "EM NEGOCIAÇÃO",
        1: "AGUARDANDO",
        2: "SEM RESPOSTA",
        3: "JÁ ERA CLIENTE",
        4: "LEAD DESISTIU",
        5: "LEAD FECHOU"
    }

    if "status" in df.columns:
        def traduz_status(x):
            try:
                return status_map[int(x)]
            except (ValueError, KeyError, TypeError):
                return str(x)
        df["status_legivel"] = df["status"].apply(traduz_status)
    # 🔍 Filtros laterais
    st.sidebar.header("🔍 Filtros")
    vendedor_filtro = st.sidebar.selectbox("Vendedor", ["Todos"] + sorted(df["usuario"].dropna().unique().tolist()))
    status_filtro = st.sidebar.selectbox("Status", ["Todos"] + sorted(df["status_legivel"].dropna().unique().tolist()))
    data_inicial = st.sidebar.date_input("Data Inicial", value=None, format="DD/MM/YYYY")
    data_final = st.sidebar.date_input("Data Final", value=None, format="DD/MM/YYYY")

    # Aplicação dos filtros
    if vendedor_filtro != "Todos":
        df = df[df["usuario"] == vendedor_filtro]
    if status_filtro != "Todos":
        df = df[df["status_legivel"] == status_filtro]
    if data_inicial:
        df = df[df["data_cadastro"].dt.date >= data_inicial]
    if data_final:
        df = df[df["data_cadastro"].dt.date <= data_final]
    # KPIs principais
    total_inclusoes = len(df)
    inclusoes_hoje = len(df[df["data_cadastro"].dt.date == datetime.now().date()])
    vendedores_unicos = df["usuario"].nunique()

    # ✅ Média por dia útil do mês
    hoje = datetime.now()
    dias_mes = calendar.monthrange(hoje.year, hoje.month)[1]
    inicio_mes = f"{hoje.year}-{hoje.month:02d}-01"
    fim_mes = f"{hoje.year}-{hoje.month:02d}-{dias_mes:02d}"
    dias_uteis = np.busday_count(inicio_mes, fim_mes) + 1
    media_dia_util = round(total_inclusoes / dias_uteis, 2) if dias_uteis > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Inclusões", total_inclusoes)
    col2.metric("Inclusões Hoje", inclusoes_hoje)
    col3.metric("Vendedores Ativos", vendedores_unicos)
    col4.metric("Média por Dia Útil", media_dia_util)
    col5.metric("Dias Úteis no Mês", dias_uteis)

    st.divider()
    # 👥 Atividades por Vendedor
    if "usuario" in df.columns and not df.empty:
        vendedor_df = df.groupby("usuario").size().reset_index(name="total")
        fig_vendedor = px.bar(vendedor_df, x="usuario", y="total",
                              title="👥 Atividades por Vendedor",
                              color="usuario", text="total",
                              color_discrete_sequence=px.colors.qualitative.Safe)
        fig_vendedor.update_traces(textposition="outside")
        st.plotly_chart(fig_vendedor, use_container_width=True)

    # 🏆 Ranking dos vendedores que mais venderam (status = LEAD FECHOU)
    if "usuario" in df.columns and "status_legivel" in df.columns:
        vendas_df = df[df["status_legivel"] == "LEAD FECHOU"].groupby("usuario").size().reset_index(name="vendas")
        if not vendas_df.empty:
            vendas_df = vendas_df.sort_values("vendas", ascending=False)
            fig_ranking = px.bar(vendas_df, x="vendas", y="usuario",
                                 orientation="h", text="vendas",
                                 title="🏆 Ranking dos Vendedores que Mais Venderam",
                                 color="usuario", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_ranking.update_traces(textposition="outside")
            st.plotly_chart(fig_ranking, use_container_width=True)
        else:
            st.info("⚠️ Nenhum vendedor com vendas registradas (LEAD FECHOU).")
    # 📞 Atividades por Canal
    if "canal" in df.columns and not df.empty:
        canal_df = df.groupby("canal").size().reset_index(name="total")
        fig_canal = px.bar(canal_df, x="canal", y="total",
                           title="📞 Atividades por Canal",
                           color="canal", text="total",
                           color_discrete_sequence=px.colors.qualitative.Safe)
        fig_canal.update_traces(textposition="outside")
        st.plotly_chart(fig_canal, use_container_width=True)

    # 💬 Atividades por Tipo
    if "tipo_atividade" in df.columns and not df.empty:
        tipo_df = df.groupby("tipo_atividade").size().reset_index(name="total")
        fig_tipo = px.bar(tipo_df, x="tipo_atividade", y="total",
                          title="💬 Atividades por Tipo de Atividade",
                          color="tipo_atividade", text="total",
                          color_discrete_sequence=px.colors.qualitative.Safe)
        fig_tipo.update_traces(textposition="outside")
        st.plotly_chart(fig_tipo, use_container_width=True)
    # 📆 Evolução diária
    if "data_cadastro" in df.columns and not df.empty:
        evolucao_df = df.groupby("data_cadastro").size().reset_index(name="total")
        fig_evolucao = px.line(evolucao_df, x="data_cadastro", y="total",
                               title="📆 Evolução Diária de Inclusões",
                               markers=True, color_discrete_sequence=["#0078D7"])
        st.plotly_chart(fig_evolucao, use_container_width=True)

    # ⏳ Pipeline de Previsões
    if "previsao" in df.columns:
        df["previsao"] = pd.to_datetime(df["previsao"], errors="coerce", dayfirst=True)
        previsao_df = df.dropna(subset=["previsao"])
        if not previsao_df.empty:
            fig_previsao = px.histogram(previsao_df, x="previsao",
                                        title="⏳ Pipeline de Previsões Futuras",
                                        nbins=15, color_discrete_sequence=["#0078D7"])
            st.plotly_chart(fig_previsao, use_container_width=True)
        else:
            st.info("⚠️ Nenhuma previsão cadastrada ainda.")
