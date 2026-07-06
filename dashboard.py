import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"

endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def dashboard_page():
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    mes_atual = meses[datetime.now().month]
    data_corrente = datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"<h1 style='text-align:center; color:#1976D2;'>Painel de Desempenho - {mes_atual}</h1>", unsafe_allow_html=True)
    params_mes = {"select":"data,usuario,status,tipo_atividade"}
    response_mes = requests.get(endpoint, headers=headers, params=params_mes)
    df_mes = pd.DataFrame(response_mes.json()) if response_mes.status_code == 200 else pd.DataFrame()
    if not df_mes.empty:
        df_mes["data"] = pd.to_datetime(df_mes["data"], errors="coerce")
        df_mes = df_mes[df_mes["data"].dt.month == datetime.now().month]
        df_rank_mes = df_mes[df_mes["status"]=="LEAD FECHOU"].groupby("usuario").size().reset_index(name="total").sort_values("total",ascending=False).head(3)
        df_mes["ligacoes"] = df_mes["tipo_atividade"].apply(lambda x: 1 if x in ["LIGAÇÃO","WHATS","LIGAÇÃO/WHATS"] else 0)
        df_lig_mes = df_mes.groupby("usuario")["ligacoes"].sum().reset_index().sort_values("ligacoes",ascending=False).head(1)
    col1,col2,col3,col4 = st.columns(4)
    if len(df_rank_mes)>0:
        with col1: st.markdown(f"<div style='background:#1976D2;color:white;padding:20px;border-radius:12px;text-align:center;'>⭐ 1º do Mês<br>{df_rank_mes.iloc[0]['usuario']} - {df_rank_mes.iloc[0]['total']} vendas</div>",unsafe_allow_html=True)
    if len(df_rank_mes)>1:
        with col2: st.markdown(f"<div style='background:#1565C0;color:white;padding:20px;border-radius:12px;text-align:center;'>⭐⭐ 2º do Mês<br>{df_rank_mes.iloc[1]['usuario']} - {df_rank_mes.iloc[1]['total']} vendas</div>",unsafe_allow_html=True)
    if len(df_rank_mes)>2:
        with col3: st.markdown(f"<div style='background:#0D47A1;color:white;padding:20px;border-radius:12px;text-align:center;'>⭐⭐⭐ 3º do Mês<br>{df_rank_mes.iloc[2]['usuario']} - {df_rank_mes.iloc[2]['total']} vendas</div>",unsafe_allow_html=True)
    if not df_lig_mes.empty:
        with col4: st.markdown(f"<div style='background:#4CAF50;color:white;padding:20px;border-radius:12px;text-align:center;'>📞 Mais Ligações<br>{df_lig_mes.iloc[0]['usuario']} - {int(df_lig_mes.iloc[0]['ligacoes'])}</div>",unsafe_allow_html=True)
    st.write("---")
    st.markdown(f"<h1 style='text-align:center; color:#FF9800;'>Painel de Desempenho do Dia - {datetime.now().strftime('%d/%m/%Y')}</h1>", unsafe_allow_html=True)
    params_dia = {"select":"data,usuario,status,tipo_atividade"}
    response_dia = requests.get(endpoint, headers=headers, params=params_dia)
    df_dia = pd.DataFrame(response_dia.json()) if response_dia.status_code == 200 else pd.DataFrame()
    if not df_dia.empty:
        df_dia["data"] = pd.to_datetime(df_dia["data"], errors="coerce")
        df_dia_dia = df_dia[df_dia["data"].dt.strftime("%Y-%m-%d")==data_corrente]
        df_rank_dia = df_dia_dia[df_dia_dia["status"]=="LEAD FECHOU"].groupby("usuario").size().reset_index(name="total").sort_values("total",ascending=False).head(1)
        df_ativ_dia = df_dia_dia.groupby("usuario").size().reset_index(name="total").sort_values("total",ascending=False).head(1)
        df_dia_dia["ligacoes"] = df_dia_dia["tipo_atividade"].apply(lambda x: 1 if x in ["LIGAÇÃO","WHATS","LIGAÇÃO/WHATS"] else 0)
        df_lig_dia = df_dia_dia.groupby("usuario")["ligacoes"].sum().reset_index(name="total_ligacoes").sort_values("total_ligacoes",ascending=False).head(1)
    col1,col2,col3 = st.columns(3)
    if not df_rank_dia.empty:
        with col1: st.markdown(f"<div style='background:#FF9800;color:white;padding:20px;border-radius:12px;text-align:center;'>🏆 Melhor Vendedor<br>{df_rank_dia.iloc[0]['usuario']} - {df_rank_dia.iloc[0]['total']}</div>",unsafe_allow_html=True)
    if not df_ativ_dia.empty:
        with col2: st.markdown(f"<div style='background:#F57C00;color:white;padding:20px;border-radius:12px;text-align:center;'>📊 Mais Atividades<br>{df_ativ_dia.iloc[0]['usuario']} - {df_ativ_dia.iloc[0]['total']}</div>",unsafe_allow_html=True)
    if not df_lig_dia.empty:
        with col3: st.markdown(f"<div style='background:#EF6C00;color:white;padding:20px;border-radius:12px;text-align:center;'>📞 Mais Ligações<br>{df_lig_dia.iloc[0]['usuario']} - {int(df_lig_dia.iloc[0]['total_ligacoes'])}</div>",unsafe_allow_html=True)
    st.write("---")
    st.subheader("🔎 Filtros")
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("Data inicial", value=datetime.now().date(), format="DD/MM/YYYY")
    with col2:
        data_final = st.date_input("Data final", value=datetime.now().date(), format="DD/MM/YYYY")

    params_base = {"select":"data,usuario"}
    response_base = requests.get(endpoint, headers=headers, params=params_base)
    df_base = pd.DataFrame(response_base.json()) if response_base.status_code == 200 else pd.DataFrame()

    if not df_base.empty:
        df_base["data"] = pd.to_datetime(df_base["data"], errors="coerce")
        df_base = df_base[(df_base["data"].dt.date >= data_inicial) & (df_base["data"].dt.date <= data_final)]

        def consulta_supabase(campo, valor):
            params = {"select":"data,usuario", campo:f"eq.{valor}"}
            r = requests.get(endpoint, headers=headers, params=params)
            df = pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
            # ✅ Garante que colunas existam
            if "data" not in df.columns:
                df["data"] = pd.NaT
            if "usuario" not in df.columns:
                df["usuario"] = ""
            if not df.empty:
                df["data"] = pd.to_datetime(df["data"], errors="coerce")
            return df

        # consultas
        df_lig_wh = consulta_supabase("tipo_atividade","LIGAÇÃO/WHATS")
        df_lig = consulta_supabase("tipo_atividade","LIGAÇÃO")
        df_wh = consulta_supabase("tipo_atividade","WHATS")
        df_rec = consulta_supabase("tipo_atividade","RECEPÇÃO")
        df_ext = consulta_supabase("tipo_atividade","EXTERNO")
        df_rs = consulta_supabase("tipo_atividade","REDE SOCIAL")
        df_neg = consulta_supabase("negociacao","Sim")
        df_vendas = consulta_supabase("status","LEAD FECHOU")
        df_ret = consulta_supabase("retornar","Sim")

        df_grid = df_base.copy()
        # Agrupa primeiro por dia e vendedor para evitar duplicação
        df_grid = df_grid.groupby(["data","usuario"], as_index=False).size().rename(columns={"size":"dummy"})
       
        # Agora faz os cálculos com base no agrupamento
        df_grid["Ligações/WH"] = df_grid.apply(lambda x: ((df_lig_wh["usuario"]==x["usuario"]) & (df_lig_wh["data"]==x["data"])).sum(), axis=1)
        df_grid["Ligações"] = df_grid.apply(lambda x: ((df_lig["usuario"]==x["usuario"]) & (df_lig["data"]==x["data"])).sum(), axis=1)
        df_grid["Whats"] = df_grid.apply(lambda x: ((df_wh["usuario"]==x["usuario"]) & (df_wh["data"]==x["data"])).sum(), axis=1)
        df_grid["Recepção"] = df_grid.apply(lambda x: ((df_rec["usuario"]==x["usuario"]) & (df_rec["data"]==x["data"])).sum(), axis=1)
        df_grid["Externo"] = df_grid.apply(lambda x: ((df_ext["usuario"]==x["usuario"]) & (df_ext["data"]==x["data"])).sum(), axis=1)
        df_grid["Rede Social"] = df_grid.apply(lambda x: ((df_rs["usuario"]==x["usuario"]) & (df_rs["data"]==x["data"])).sum(), axis=1)
        df_grid["Total"] = df_grid[["Ligações/WH","Ligações","Whats","Recepção","Externo","Rede Social"]].sum(axis=1)
        df_grid["Negociação"] = df_grid.apply(lambda x: ((df_neg["usuario"]==x["usuario"]) & (df_neg["data"]==x["data"])).sum(), axis=1)
        df_grid["Com Previsão"] = df_grid.apply(lambda x: 1 if x["Total"]>0 else 0, axis=1)
        df_grid["Total de Vendas"] = df_grid.apply(lambda x: ((df_vendas["usuario"]==x["usuario"]) & (df_vendas["data"]==x["data"])).sum(), axis=1)
        df_grid["Números Ativos"] = df_grid.apply(lambda x: ((df_ret["usuario"]==x["usuario"]) & (df_ret["data"]==x["data"])).sum(), axis=1)

        # ✅ Agrupa por dia e vendedor para totalizar
        #df_grid= df_grid.groupby(["data","usuario"], as_index=False).sum()
        # ✅ Só aqui renomeia para exibir
        # Remove a coluna auxiliar 'dummy'
        if "dummy" in df_grid.columns:
            df_grid.drop(columns=["dummy"], inplace=True)

        df_grid["data"] = df_grid["data"].dt.strftime("%d/%m/%Y")
        df_grid.rename(columns={"data":"Data","usuario":"Vendedor"}, inplace=True)

    st.subheader(f"📋 Atividades de {data_inicial.strftime('%d/%m/%Y')} até {data_final.strftime('%d/%m/%Y')}")
    
    # ✅ Botão para atualizar o grid
    if st.button("🔄 Atualizar dados"):
        st.rerun()
    st.dataframe(df_grid, use_container_width=True, height=400)
    st.write("---")
    st.subheader("🍩 Donuts por Vendedor")

    if not df_grid.empty:
        df_vendedores = df_grid.groupby("Vendedor", as_index=False).agg({
            "Total":"sum",
            "Total de Vendas":"sum",
            "Números Ativos":"sum",
            "Ligações":"sum",
            "Whats":"sum",
            "Ligações/WH":"sum"
        })

        for i, row in df_vendedores.iterrows():
            vendedor = row["Vendedor"]
            total = row["Total"]
            vendas = row["Total de Vendas"]

            dados = pd.DataFrame({"Categoria":["Atividades","Vendas"],"Quantidade":[total,vendas]})
            fig = px.pie(dados, names="Categoria", values="Quantidade", hole=0.5,
                         color="Categoria", color_discrete_map={"Atividades":"#1976D2","Vendas":"#FF9800"},
                         title=f"{vendedor} - Atividades vs Vendas")
            fig.update_traces(textinfo="percent+value")
            st.plotly_chart(fig, use_container_width=True, key=f"donut_{i}_atividades")

            dados_ret = pd.DataFrame({"Categoria":["Números Ativos","Ligações/Whats"],
                                      "Quantidade":[row["Números Ativos"], row["Ligações"]+row["Whats"]+row["Ligações/WH"]]})
            fig_ret = px.pie(dados_ret, names="Categoria", values="Quantidade", hole=0.5,
                             color="Categoria", color_discrete_map={"Números Ativos":"#9E9E9E","Ligações/Whats":"#E91E63"},
                             title=f"{vendedor} - Números Ativos vs Ligações")
            fig_ret.update_traces(textinfo="percent+value")
            st.plotly_chart(fig_ret, use_container_width=True, key=f"donut_{i}_ligacoes")
    st.write("---")
    st.subheader("📊 Consolidado de Todos os Vendedores")

    # Totais consolidados
    total_periodo = df_grid["Total"].sum()
    vendas_periodo = df_grid["Total de Vendas"].sum()
    numeros_ativos_periodo = df_grid["Números Ativos"].sum()
    ligacoes_periodo = df_grid[["Ligações","Whats","Ligações/WH"]].sum().sum()

    # Donut consolidado Atividades vs Vendas
    dados_total = pd.DataFrame({
        "Categoria":["Total de Atividades","Total de Vendas"],
        "Quantidade":[total_periodo,vendas_periodo]
    })
    fig_total = px.pie(
        dados_total, names="Categoria", values="Quantidade", hole=0.5,
        color="Categoria",
        color_discrete_map={"Total de Atividades":"#1976D2","Total de Vendas":"#FF9800"},
        title="📊 Total de Atividades vs Total de Vendas (Consolidado)"
    )
    fig_total.update_traces(textinfo="percent+value")
    st.plotly_chart(fig_total, use_container_width=True)

    # Donut consolidado Números Ativos vs Ligações
    dados_ret = pd.DataFrame({
        "Categoria":["Números Ativos","Ligações/Whats"],
        "Quantidade":[numeros_ativos_periodo, ligacoes_periodo]
    })
    fig_ret = px.pie(
        dados_ret, names="Categoria", values="Quantidade", hole=0.5,
        color="Categoria",
        color_discrete_map={"Números Ativos":"#9E9E9E","Ligações/Whats":"#E91E63"},
        title="📊 Números Ativos vs Ligações (Consolidado)"
    )
    fig_ret.update_traces(textinfo="percent+value")
    st.plotly_chart(fig_ret, use_container_width=True)

    st.write("---")
    st.subheader("🏆 Ranking de Vendedores no Período")

    ranking_df = df_grid.groupby("Vendedor")["Total de Vendas"].sum().reset_index().sort_values("Total de Vendas", ascending=False)
    if not ranking_df.empty:
        fig_ranking = px.bar(
            ranking_df, x="Total de Vendas", y="Vendedor", orientation="h",
            text="Total de Vendas", title="🏆 Ranking de Vendas",
            color="Vendedor", color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_ranking.update_traces(textposition="outside")
        st.plotly_chart(fig_ranking, use_container_width=True)

    st.write("---")
    st.subheader("📊 Ranking de Atividades no Período")

    ranking_ativ_df = df_grid.groupby("Vendedor")["Total"].sum().reset_index().sort_values("Total", ascending=False)
    if not ranking_ativ_df.empty:
        fig_ranking_ativ = px.bar(
            ranking_ativ_df, x="Total", y="Vendedor", orientation="h",
            text="Total", title="📊 Ranking de Atividades",
            color="Vendedor", color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_ranking_ativ.update_traces(textposition="outside")
        st.plotly_chart(fig_ranking_ativ, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum dado encontrado para o período selecionado.")
