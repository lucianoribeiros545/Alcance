import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import calendar
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO E ESTILOS
# ==========================================
st.set_page_config(layout="wide", page_title="Cockpit de Performance 360°")

# Conexão Supabase
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"
endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def aplicar_estilos():
    st.markdown("""
        <style>
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            text-align: center;
        }
        .big-number { font-size: 2.0rem; font-weight: 800; color: #64ffda; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CARREGAMENTO DE DADOS
# ==========================================
def carregar_dados():
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            for col in ["data", "previsao", "data_cadastro"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            
            status_map = {0: "EM NEGOCIAÇÃO", 1: "AGUARDANDO", 2: "SEM RESPOSTA", 3: "JÁ ERA CLIENTE", 4: "LEAD DESISTIU", 5: "LEAD FECHOU"}
            if "status" in df.columns:
                df["status_legivel"] = df["status"].apply(lambda x: status_map.get(int(x), str(x)) if pd.notnull(x) else x)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# ==========================================
# 3. INTERFACE E DASHBOARD
# ==========================================
def dashboard_view():
    aplicar_estilos()
    st.markdown("<h1 style='text-align:center;'>⚡ Cockpit de Performance 360°</h1>", unsafe_allow_html=True)
    
    df = carregar_dados()
    if df.empty:
        st.warning("Nenhum dado encontrado no Supabase.")
        return

    # Filtros
    st.sidebar.header("🔍 Filtros")
    usuarios = ["Todos"] + sorted(df["usuario"].dropna().unique().tolist())
    vendedor_filtro = st.sidebar.selectbox("Vendedor", usuarios)
    if vendedor_filtro != "Todos":
        df = df[df["usuario"] == vendedor_filtro]

    # KPIs com Cards Glassmorphism
    total = len(df)
    vendas = len(df[df["status_legivel"] == "LEAD FECHOU"])
    taxa = (vendas / total * 100) if total > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    for col, titulo, valor in zip([c1,c2,c3,c4], ["Volume Geral", "Total Vendas", "Conversão", "Vendedores"], [total, vendas, f"{taxa:.1f}%", df["usuario"].nunique()]):
        with col:
            st.markdown(f"""
            <div class="glass-card">
                <small>{titulo}</small>
                <div class="big-number">{valor}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Funil de Status")
        fig_funnel = px.funnel(df.groupby("status_legivel").size().reset_index(name="count"), x="count", y="status_legivel")
        st.plotly_chart(fig_funnel, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Ranking de Vendas")
        ranking = df[df["status_legivel"] == "LEAD FECHOU"].groupby("usuario").size().reset_index(name="vendas")
        st.plotly_chart(px.bar(ranking, x="vendas", y="usuario", orientation='h', color_discrete_sequence=['#64ffda']), use_container_width=True)

    # Evolução
    if "data_cadastro" in df.columns:
        st.subheader("📈 Evolução Diária")
        evolucao = df.groupby(df["data_cadastro"].dt.date).size().reset_index(name="total")
        st.plotly_chart(px.area(evolucao, x="data_cadastro", y="total", color_discrete_sequence=['#64ffda']), use_container_width=True)

if __name__ == "__main__":
    dashboard_view()
