import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# PARTE 1: Configuração e Estilização
# ==========================================
st.set_page_config(layout="wide", page_title="Cockpit de Performance 360°")

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
        .big-number { font-size: 2.2rem; font-weight: 800; color: #64ffda; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# PARTE 2: Camada de Dados
# ==========================================
def carregar_dados():
    try:
        conn = sqlite3.connect("database.db")
        query = "SELECT usuario, status, COUNT(*) as count, data FROM atividades GROUP BY usuario, status, data"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return pd.DataFrame()

# ==========================================
# PARTE 3: KPIs e Cabeçalho
# ==========================================
def renderizar_kpis(df, selecionados):
    df_filtered = df[df['usuario'].isin(selecionados)]
    total_atividades = df_filtered['count'].sum()
    total_vendas = df_filtered[df_filtered['status'] == 'LEAD FECHOU']['count'].sum()
    taxa = (total_vendas / total_atividades * 100) if total_atividades > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Volume Geral", total_atividades)
    c2.metric("Total de Vendas", total_vendas)
    c3.metric("Taxa de Conversão", f"{taxa:.1f}%")
    c4.metric("Vendedores", len(selecionados))
    st.markdown("---")

# ==========================================
# PARTE 4: Cards de Vendedores
# ==========================================
def renderizar_cards_vendedores(df, selecionados):
    df_filtered = df[df['usuario'].isin(selecionados)]
    resumo = df_filtered.pivot_table(index='usuario', columns='status', values='count', aggfunc='sum', fill_value=0)
    
    cols = st.columns(4)
    for i, (usuario, row) in enumerate(resumo.iterrows()):
        conversao = (row.get('LEAD FECHOU', 0) / row.sum() * 100) if row.sum() > 0 else 0
        with cols[i % 4]:
            st.markdown(f"""
            <div class="glass-card">
                <h4>{usuario}</h4>
                <div class="big-number">{int(row.get('LEAD FECHOU', 0))}</div>
                <small>Conversão: {conversao:.1f}% de {int(row.sum())} leads</small>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# PARTE 5: Gráficos de Alta Performance
# ==========================================
def renderizar_graficos(df, selecionados):
    df_filtered = df[df['usuario'].isin(selecionados)]
    c_graf1, c_graf2 = st.columns([2, 1])
    
    with c_graf1:
        st.subheader("📊 Funil de Conversão")
        fig_funnel = px.funnel(df_filtered.groupby('status')['count'].sum().reset_index(), x='count', y='status')
        st.plotly_chart(fig_funnel, use_container_width=True)

    with c_graf2:
        st.subheader("🎯 Comparativo (Radar)")
        fig_radar = go.Figure()
        for user in selecionados[:3]:
            d = df_filtered[df_filtered['usuario'] == user].set_index('status')['count']
            fig_radar.add_trace(go.Scatterpolar(r=d.values, theta=d.index, name=user, fill='toself'))
        st.plotly_chart(fig_radar, use_container_width=True)

# ==========================================
# PARTE 6: Análise Temporal
# ==========================================
def renderizar_evolucao_temporal():
    st.subheader("📈 Tendência de Vendas (Diária)")
    conn = sqlite3.connect("database.db")
    query = "SELECT data, COUNT(*) as total FROM atividades WHERE status = 'LEAD FECHOU' GROUP BY data ORDER BY data DESC LIMIT 14"
    df_temp = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_temp.empty:
        fig = px.area(df_temp, x='data', y='total', template="plotly_dark")
        fig.update_traces(line_color='#64ffda', fill='tozeroy')
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PARTE 7: Exportação de Dados
# ==========================================
def renderizar_exportacao(df):
    st.markdown("---")
    st.subheader("📥 Exportação de Dados")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Baixar Relatório (CSV)", data=csv, file_name='relatorio_performance.csv', mime='text/csv')

# ==========================================
# PARTE 8: Orquestrador Principal
# ==========================================
def main():
    aplicar_estilos()
    dados = carregar_dados()
    
    if dados.empty:
        st.warning("Banco de dados vazio.")
        return

    st.sidebar.header("⚙️ Filtros")
    usuarios = dados['usuario'].unique()
    selecionados = st.sidebar.multiselect("Selecione Vendedores:", usuarios, default=usuarios)
    
    st.title("⚡ Cockpit de Performance 360°")
    renderizar_kpis(dados, selecionados)
    renderizar_cards_vendedores(dados, selecionados)
    renderizar_graficos(dados, selecionados)
    renderizar_evolucao_temporal()
    renderizar_exportacao(dados[dados['usuario'].isin(selecionados)])

if __name__ == "__main__":
    main()
