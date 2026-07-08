import streamlit as st
import pandas as pd
import requests
from datetime import datetime
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
        try:
            # Caso o Streamlit já envie como objeto date/datetime
            return valor.strftime("%Y-%m-%d")
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
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)

            with col1: data_inicial = st.date_input("Data inicial", value=None, format="DD/MM/YYYY")
            with col2: data_final = st.date_input("Data final", value=None, format="DD/MM/YYYY")
            with col3: contato_filtro = st.text_input("Contato", autocomplete="off")
            with col4: numero_valido_filtro = st.selectbox("Número Válido", options=["", "Sim", "Não"])
            with col5: negociacao_filtro = st.selectbox("Negociação", options=["", "Sim", "Não"])
            with col6: status_filtro = st.selectbox("Status", options=["","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"])
            with col7: tipo_atividade_filtro = st.selectbox("Tipo de Atividade", options=["","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"])
            with col8: vendedor_filtro = st.text_input("Vendedor") if usuario_logado in ["ADMIN","GESTOR"] else ""
            with col9: canal_filtro = st.selectbox("Canal", options=["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"])

            aplicar_filtro = st.form_submit_button("Pesquisar")
        
        # Se clicar em pesquisar, limpa o estado antigo para forçar recarregamento do banco
        if aplicar_filtro:
            st.session_state.pop("df_grid", None)
            st.session_state.pop("ids_originais", None)

        params = {}
        if usuario_logado not in ["ADMIN","GESTOR"]:
            params["usuario"] = f"eq.{usuario_logado}"

        if aplicar_filtro:
            if data_inicial and data_final:
                params["and"] = f"(data.gte.{data_inicial.strftime('%Y-%m-%d')},data.lte.{data_final.strftime('%Y-%m-%d')})"
            elif data_inicial:
                params["data"] = f"gte.{data_inicial.strftime('%Y-%m-%d')}"
            elif data_final:
                params["data"] = f"lte.{data_final.strftime('%Y-%m-%d')}"
            if contato_filtro.strip(): params["contato"] = f"ilike.%{contato_filtro.strip()}%"
            if numero_valido_filtro.strip(): params["retornar"] = f"eq.{numero_valido_filtro.strip()}"
            if negociacao_filtro.strip(): params["negociacao"] = f"eq.{negociacao_filtro.strip()}"
            if status_filtro.strip(): params["status"] = f"eq.{status_filtro.strip()}"
            if tipo_atividade_filtro.strip(): params["tipo_atividade"] = f"eq.{tipo_atividade_filtro.strip()}"
            if vendedor_filtro.strip(): params["usuario"] = f"eq.{vendedor_filtro.strip().upper()}"
            if canal_filtro.strip(): params["canal"] = f"eq.{canal_filtro.strip()}"

        # Carrega dados do Supabase apenas se o estado não existir
        if "df_grid" not in st.session_state:
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

            colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                             "negociacao","previsao","descricao","recepcao","clinica",
                             "usuario","data_cadastro","hora_cadastro","id"]
            df = df[[c for c in colunas_ordem if c in df.columns]]

            if "data" in df.columns and "hora_cadastro" in df.columns:
                df = df.sort_values(by=["data", "hora_cadastro"], ascending=[True, True])
            
            # Reset do index limpo antes de salvar no estado
            df = df.reset_index(drop=True)
            st.session_state["df_grid"] = df.copy()
            # Mapeamento rígido e imutável dos IDs como string para evitar falsos positivos
            st.session_state["ids_originais"] = set(str(x) for x in df["id"].dropna().tolist())

        salvar_topo = st.button("💾 Salvar alterações (Topo)", key="salvar_topo")
        
        column_config = {
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "contato": st.column_config.TextColumn("Contato"),
            "tipo_atividade": st.column_config.SelectboxColumn("Tipo de Atividade", options=["","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"]),
            "retornar": st.column_config.SelectboxColumn("Número Válido", options=["","Sim","Não"]),
            "canal": st.column_config.SelectboxColumn("Canal", options=["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"]),
            "status": st.column_config.SelectboxColumn("Status", options=["","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"]),
            "negociacao": st.column_config.SelectboxColumn("Negociação", options=["","Sim","Não"]),
            "previsao": st.column_config.DateColumn("Previsão", format="DD/MM/YYYY"),
            "descricao": st.column_config.TextColumn("Descrição"),
            "recepcao": st.column_config.SelectboxColumn("Recepção", options=["","ATUALIZAÇÃO CADASTRAL","PAGAMENTO","CANCELAMENTO","VENDA","INFORMAÇÃO GERAL","CARTEIRINHA"]),
            "clinica": st.column_config.SelectboxColumn("Clínica", options=["","APP","PAGAMENTO","CANCELAMENTO","RETENÇÃO","VENDA","INFORMAÇÃO GERAL"]),
            "usuario": st.column_config.TextColumn("Vendedor", disabled=True),
            "data_cadastro": st.column_config.DateColumn("Data Cadastro", format="DD/MM/YYYY", disabled=True),
            "hora_cadastro": st.column_config.TextColumn("Hora Cadastro", disabled=True),
            "id": st.column_config.TextColumn("ID", disabled=True)
        }

        edited_df = st.data_editor(
            st.session_state["df_grid"],
            num_rows="dynamic",
            width="stretch",
            height=400,
            key="atividades_grid",
            column_config=column_config,
            hide_index=True
        )

        st.markdown(f"**Total de registros exibidos: {len(edited_df)}**")
        salvar_base = st.button("💾 Salvar alterações (Base)", key="salvar_base")
        
        if salvar_topo or salvar_base:
            inseridos = atualizados = excluidos = 0
            
            # --- 1. SEGURANÇA MÁXIMA CONTRA EXCLUSÃO ERRADA ---
            ids_originais = st.session_state.get("ids_originais", set())
            # Lê apenas quem mantém IDs válidos visíveis na tela
            ids_na_tela = set(str(row["id"]) for _, row in edited_df.dropna(subset=["id"]).iterrows())
            # A exclusão ocorre APENAS se o ID existia originalmente e sumiu por completo da tela
            ids_para_deletar = ids_originais - ids_na_tela

            for id_excluir in ids_para_deletar:
                delete_endpoint = f"{endpoint}?id=eq.{id_excluir}"
                response = requests.delete(delete_endpoint, headers=headers)
                if response.status_code in [200, 204]:
                    excluidos += 1
                else:
                    st.error(f"❌ Falha ao excluir {id_excluir}: {response.text}")

            # --- 2. SALVAMENTO INTEGRAL SEM DEPENDER DE INDEX POSICIONAL ---
            for _, row in edited_df.iterrows():
                contato = str(row.get("contato", "")).strip()
                data = formatar_data_iso(row.get("data", ""))

                if not contato or not data:
                    continue

                # CASO A: Registro inteiramente novo (Sem ID de banco)
                if pd.isna(row.get("id")) or str(row.get("id")).strip() == "":
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
                    if response.status_code in [200, 201]:
                        inseridos += 1
                    else:
                        st.error(f"❌ Falha ao inserir novo registro: {response.text}")
                
                # CASO B: Registro existente na tela (Atualização via PATCH direta)
                else:
                    id_atual = str(row["id"])
                    dados_atualizados = {
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
                        "clinica": str(row.get("clinica", "")).strip()
                    }
                    
                    update_endpoint = f"{endpoint}?id=eq.{id_atual}"
                    response = requests.patch(update_endpoint, headers=headers, json=dados_atualizados)
                    if response.status_code in [200, 204]:
                        atualizados += 1

            st.success(f"✅ Sucesso! Inseridos: {inseridos} | 🔄 Processados: {atualizados} | ❌ Excluídos: {excluidos}")
            
            # --- 3. LIMPEZA TOTAL DE BUFFER E CACHE ---
            # Remove as chaves antigas e dá refresh completo na aplicação
            st.session_state.pop("df_grid", None)
            st.session_state.pop("ids_originais", None)
            st.rerun()

    except Exception as e:
        st.error("❌ Erro catastrófico ao processar a página de atividades.")
        st.text(traceback.format_exc())
