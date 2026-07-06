import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import traceback

SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"

endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def formatar_data_iso(valor):
    if pd.isna(valor) or not valor:
        return None
    try:
        return datetime.strptime(str(valor).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return str(valor).strip()
def cadastro_atividades_page():
    try:
        if "usuario_logado" not in st.session_state or not st.session_state["usuario_logado"]:
            st.error("⚠️ Nenhum usuário logado. Faça login para acessar esta página.")
            st.stop()

        usuario_logado = st.session_state["usuario_logado"].upper()
        st.markdown(f"<h1 style='text-align:center;'>Inclusão de Atividades ({usuario_logado})</h1>", unsafe_allow_html=True)

        col1, col2 = st.columns([4,2])
        with col2:
            if st.button("📊 Consultar Inclusões do Dia"):
                hoje = datetime.now().strftime("%Y-%m-%d")
                params = {"data_cadastro": f"eq.{hoje}"}
                if usuario_logado not in ["ADMIN", "GESTOR"]:
                    params["usuario"] = f"eq.{usuario_logado}"
                response = requests.get(endpoint, headers=headers, params=params)
                st.session_state["inclusoes_hoje"] = len(response.json()) if response.status_code == 200 else 0

            st.markdown(
                f"""
                <div style="background-color:#0073e6;
                            padding:15px;
                            border-radius:10px;
                            text-align:center;
                            font-weight:bold;
                            font-size:18px;
                            color:#ffffff;">
                    📌 Inclusões do dia<br>
                    <span style="font-size:24px; color:#ffffff;">{st.session_state.get('inclusoes_hoje', 0)}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with st.form(key="filtro_form_unico"):
            st.subheader("🔎 Filtros de Pesquisa")
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

            with col1: data_inicial = st.date_input("Data inicial", value=None, format="DD/MM/YYYY")
            with col2: data_final = st.date_input("Data final", value=None, format="DD/MM/YYYY")
            with col3: contato_filtro = st.text_input("Contato", autocomplete="off")
            with col4: numero_valido_filtro = st.selectbox("Número Válido", options=["", "Sim", "Não"])
            with col5: negociacao_filtro = st.selectbox("Negociação", options=["", "Sim", "Não"])
            with col6: vendedor_filtro = st.text_input("Vendedor") if usuario_logado in ["ADMIN","GESTOR"] else ""
            with col7: canal_filtro = st.selectbox("Canal", options=["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"])

            aplicar_filtro = st.form_submit_button("Pesquisar")

        params = {}
        if usuario_logado not in ["ADMIN","GESTOR"]:
            params["usuario"] = f"eq.{usuario_logado}"
        if aplicar_filtro:
            if data_inicial: params["data"] = f"gte.{data_inicial.strftime('%Y-%m-%d')}"
            if data_final: params["data"] = f"lte.{data_final.strftime('%Y-%m-%d')}"
            if contato_filtro.strip(): params["contato"] = f"ilike.%{contato_filtro.strip()}%"
            if numero_valido_filtro.strip(): params["retornar"] = f"eq.{numero_valido_filtro.strip()}"
            if negociacao_filtro.strip(): params["negociacao"] = f"eq.{negociacao_filtro.strip()}"
            if vendedor_filtro.strip(): params["usuario"] = f"eq.{vendedor_filtro.strip().upper()}"
            if canal_filtro.strip(): params["canal"] = f"eq.{canal_filtro.strip()}"
        response = requests.get(endpoint, headers=headers, params=params)
        df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()

        if df.empty:
            df = pd.DataFrame(columns=[
                "data","contato","tipo_atividade","retornar","canal","status",
                "negociacao","previsao","descricao","recepcao","clinica",
                "usuario","data_cadastro","hora_cadastro","id"
            ])

        for col in ["data","previsao","data_cadastro"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

        ids_originais = set(df["id"].tolist()) if "id" in df.columns else set()
        colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                         "negociacao","previsao","descricao","recepcao","clinica",
                         "usuario","data_cadastro","hora_cadastro","id"]
        df = df[[c for c in colunas_ordem if c in df.columns]]
        salvar_topo = st.button("💾 Salvar alterações (Topo)", key="salvar_topo")
        column_config = {
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "contato": st.column_config.TextColumn("Contato"),
            "tipo_atividade": st.column_config.SelectboxColumn("Tipo de Atividade", options=[
                "","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"]),
            "retornar": st.column_config.SelectboxColumn("Número Válido", options=["","Sim","Não"]),
            "canal": st.column_config.SelectboxColumn("Canal", options=[
                "","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"]),
            "status": st.column_config.SelectboxColumn("Status", options=[
                "","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"]),
            "negociacao": st.column_config.SelectboxColumn("Negociação", options=["","Sim","Não"]),
            "previsao": st.column_config.DateColumn("Previsão", format="DD/MM/YYYY"),
            "descricao": st.column_config.TextColumn("Descrição"),
            "recepcao": st.column_config.SelectboxColumn("Recepção", options=[
                "","ATUALIZAÇÃO CADASTRAL","PAGAMENTO","CANCELAMENTO","VENDA","INFORMAÇÃO GERAL","CARTEIRINHA"]),
            "clinica": st.column_config.SelectboxColumn("Clínica", options=[
                "","APP","PAGAMENTO","CANCELAMENTO","RETENÇÃO","VENDA","INFORMAÇÃO GERAL"]),
            "usuario": st.column_config.TextColumn("Vendedor", disabled=True),
            "data_cadastro": st.column_config.DateColumn("Data Cadastro", format="DD/MM/YYYY", disabled=True),
            "hora_cadastro": st.column_config.TextColumn("Hora Cadastro", disabled=True),
            "id": st.column_config.TextColumn("ID", disabled=True)
        }

        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            width="stretch",
            height=600,
            key="atividades_grid",
            column_config=column_config,
            hide_index=True
        )
        salvar_base = st.button("💾 Salvar alterações (Base)", key="salvar_base")
        if salvar_topo or salvar_base:
            inseridos = atualizados = excluidos = 0

            # 🔹 Detecta exclusões
            ids_atuais = set(edited_df["id"].dropna().tolist()) if "id" in edited_df.columns else set()
            ids_excluidos = ids_originais - ids_atuais
            for id_excluir in ids_excluidos:
                delete_endpoint = f"{endpoint}?id=eq.{id_excluir}"
                response = requests.delete(delete_endpoint, headers=headers)
                if response.status_code in [200, 204]:
                    excluidos += 1
                else:
                    st.error(f"❌ Falha ao excluir {id_excluir}: {response.text}")

            # 🔹 Detecta alterações reais
            edited_rows = st.session_state["atividades_grid"].get("edited_rows", {})

            for idx, row in edited_df.reset_index(drop=True).iterrows():
                contato = str(row.get("contato", "")).strip()
                data = formatar_data_iso(row.get("data", ""))

                if not contato or not data:
                    continue

                if pd.isna(row.get("id")) or str(row.get("id")).strip() == "":
                    # Novo registro → inclui data/hora
                    novo_registro = {
                        "data": data,
                        "contato": contato,
                        "canal": str(row.get("canal", "")).strip(),
                        "tipo_atividade": str(row.get("tipo_atividade", "")).strip(),
                        "status": str(row.get("status", "")).strip(),
                        "negociacao": str(row.get("negociacao", "")).strip(),
                        "previsao": formatar_data_iso(row.get("previsao", "")),
                        "retornar": str(row.get("retornar", "")).strip(),
                        "descricao": str(row.get("descricao", "")).strip(),
                        "recepcao": str(row.get("recepcao", "")).strip(),
                        "clinica": str(row.get("clinica", "")).strip(),
                        "usuario": usuario_logado,
                        "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
                        "hora_cadastro": datetime.now().strftime("%H:%M:%S")
                    }

                    response = requests.post(endpoint, headers=headers, json=novo_registro)
                    if response.status_code == 201:
                        inseridos += 1
                    else:
                        st.error(f"❌ Falha ao inserir registro {idx+1}: {response.text}")
                elif idx in edited_rows:
                    # Atualização apenas dos campos alterados
                    changes = edited_rows[idx]
                    update_endpoint = f"{endpoint}?id=eq.{row['id']}"
                    response = requests.patch(update_endpoint, headers=headers, json=changes)
                    if response.status_code in [200, 204]:
                        atualizados += 1
                    else:
                        st.error(f"❌ Falha ao atualizar registro {row['id']}: {response.text}")
            # ✅ Mostra resumo das operações
            st.success(f"✅ Inseridos: {inseridos} | 🔄 Atualizados: {atualizados} | ❌ Excluídos: {excluidos}")

    except Exception as e:
        st.error("❌ Erro ao carregar a página de cadastro de atividades.")
        st.text(traceback.format_exc())
     