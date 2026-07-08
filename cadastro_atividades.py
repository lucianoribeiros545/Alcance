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
            
            # --- PROTOCOLO DE SEGURANÇA 1: INDEXAÇÃO POR ID ---
            # Guardamos os IDs originais antes de transformar em índice
            st.session_state["ids_originais"] = set(str(x) for x in df["id"].dropna().tolist())
            # O ID vira o índice oficial do DataFrame para o Streamlit rastrear por ID e não por posição
            df = df.set_index("id", drop=False)
            st.session_state["df_grid"] = df.copy()

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

        # Renderiza o editor usando a indexação por ID estável
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
            
            # --- PROTOCOLO DE SEGURANÇA 2: EXCLUSÃO REAL ---
            ids_originais = st.session_state.get("ids_originais", set())
            # Coleta os IDs reais presentes nas linhas atuais (ignorando linhas novas temporárias do pandas)
            ids_na_tela = set(str(row["id"]) for _, row in edited_df.iterrows() if pd.notna(row.get("id")) and str(row.get("id")).strip() != "")
            # Exclusão baseada em diferença lógica pura de strings de IDs
            ids_para_deletar = ids_originais - ids_na_tela

            for id_excluir in ids_para_deletar:
                delete_endpoint = f"{endpoint}?id=eq.{id_excluir}"
                response = requests.delete(delete_endpoint, headers=headers)
                if response.status_code in [200, 204]:
                    excluidos += 1
                else:
                    st.error(f"❌ Falha ao excluir ID {id_excluir}: {response.text}")

            # --- PROTOCOLO DE SEGURANÇA 3: DICIONÁRIO MAPEADO POR ID ---
            grid_state = st.session_state.get("atividades_grid", {})
            edited_rows = grid_state.get("edited_rows", {}) # Aqui o Streamlit retorna { "ID_REAL_OU_INDEX": {campos} }

            for current_idx, row in edited_df.iterrows():
                contato = str(row.get("contato", "")).strip()
                data = formatar_data_iso(row.get("data", ""))

                # Proteção contra linhas vazias ou incompletas adicionadas na pressa
                if not contato or not data:
                    continue

                id_valor = row.get("id")

                # CASO A: Linha inteiramente nova (O ID não existe ou veio nulo do componente)
                if pd.isna(id_valor) or str(id_valor).strip() == "" or str(current_idx).startswith("_"):
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
                
                # CASO B: Registro antigo. Só executa PATCH se o ID estiver explicitamente mapeado nas edições
                elif current_idx in edited_rows or str(current_idx) in edited_rows:
                    id_atual = str(id_valor)
                    changes = edited_rows.get(current_idx, edited_rows.get(str(current_idx), {}))
                    
                    if "data" in changes: changes["data"] = formatar_data_iso(changes["data"])
                    if "previsao" in changes: changes["previsao"] = formatar_data_iso(changes["previsao"])
                    
                    if changes:
                        update_endpoint = f"{endpoint}?id=eq.{id_atual}"
                        response = requests.patch(update_endpoint, headers=headers, json=changes)
                        if response.status_code in [200, 204]:
                            atualizados += 1
                        else:
                            st.error(f"❌ Falha ao atualizar registro {id_atual}: {response.text}")

            st.success(f"✅ Alterações processadas! Inseridos: {inseridos} | 🔄 Atualizados: {atualizados} | ❌ Excluídos: {excluidos}")
            
            # --- PROTOCOLO DE SEGURANÇA 4: PURGA TOTAL DO CACHE ---
            st.session_state.pop("df_grid", None)
            st.session_state.pop("ids_originais", None)
            st.rerun()

    except Exception as e:
        st.error("❌ Ocorreu um erro ao processar a página.")
        st.text(traceback.format_exc())
