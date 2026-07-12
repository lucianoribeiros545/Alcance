import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import traceback
import time
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"
endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def formatar_data_iso(valor):
    if pd.isna(valor) or not valor: return None
    try: return datetime.strptime(str(valor).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        try: return pd.to_datetime(valor).strftime("%Y-%m-%d")
        except: return str(valor).strip()

def cadastro_atividades_page():
    st.markdown("<style>html { scroll-behavior: auto !important; }</style>", unsafe_allow_html=True)
    if "usuario_logado" not in st.session_state or not st.session_state["usuario_logado"]:
        st.error("⚠️ Nenhum usuário logado. Faça login.")
        st.stop()
    usuario_logado = st.session_state["usuario_logado"].upper()# Carregamento
    colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status","negociacao","previsao","descricao","recepcao","clinica","usuario","data_cadastro","hora_cadastro","id"]
    if "df_grid" not in st.session_state:
        response = requests.get(endpoint, headers=headers)
        df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame(columns=colunas_ordem)
        st.session_state["df_grid"] = df.reset_index(drop=True)
        st.session_state["df_original_dict"] = df[df["id"] != ""].set_index("id").to_dict(orient="index") if not df.empty else {}

    # Renderização do GRID no TOPO
    st.write('<div id="grid-ancora"></div>', unsafe_allow_html=True)
    gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
    gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=True)
    
    gb.configure_column("contato", header_name="Contato", minWidth=150)
    gb.configure_column("tipo_atividade", header_name="Tipo de Atividade", minWidth=160, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"]})
    gb.configure_column("retornar", header_name="Número Válido", minWidth=120, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
    gb.configure_column("canal", header_name="Canal", minWidth=140, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"]})
    gb.configure_column("status", header_name="Status", minWidth=150, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"]})
    gb.configure_column("negociacao", header_name="Negociação", minWidth=120, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
    gb.configure_column("previsao", header_name="Previsão", minWidth=110)
    gb.configure_column("descricao", header_name="Descrição", minWidth=200)
    gb.configure_column("recepcao", header_name="Recepção", minWidth=180, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","ATUALIZAÇÃO CADASTRAL","PAGAMENTO","CANCELAMENTO","VENDA","INFORMAÇÃO GERAL","CARTEIRINHA"]})
    gb.configure_column("clinica", header_name="Clínica", minWidth=150, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","APP","PAGAMENTO","CANCELAMENTO","RETENÇÃO","VENDA","INFORMAÇÃO GERAL"]})
    gb.configure_column("usuario", header_name="Vendedor", editable=False, minWidth=120)
    gb.configure_column("data_cadastro", header_name="Data Cadastro", editable=False, minWidth=130)
    gb.configure_column("hora_cadastro", header_name="Hora Cadastro", editable=False, minWidth=130)
    gb.configure_column("id", header_name="ID", editable=False, minWidth=80)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_grid_options(enterMovesDownAfterEdit=True, enableClipboard=True, clipboardDelimitedByChars="\t", suppressClipboardPaste=False)
    
    grid_response = AgGrid(st.session_state["df_grid"], gridOptions=gb.build(), data_return_mode=DataReturnMode.FILTERED_AND_SORTED, update_mode=GridUpdateMode.SELECTION_CHANGED, fit_columns_on_grid_load=True, theme="alpine", height=400)# Filtros e Contador abaixo do grid
    col1, col2 = st.columns([4, 2])
    with col2:
        if st.button("📊 Consultar Inclusões do Dia"):
            hoje = datetime.now().strftime("%Y-%m-%d")
            res = requests.get(endpoint, headers=headers, params={"data_cadastro": f"eq.{hoje}"})
            st.session_state["inclusoes_hoje"] = len(res.json()) if res.status_code == 200 else 0
        st.markdown(f"**📌 Inclusões do dia: {st.session_state.get('inclusoes_hoje', 0)}**")

    with st.form(key="filtro_form_unico"):
        st.subheader("🔎 Filtros de Pesquisa")
        # [Seus campos de filtros aqui...]
        aplicar_filtro = st.form_submit_button("Pesquisar")

    # Painel de Edição e Ações
    st.subheader("📋 Painel de Edição de Atividades")
    c_qtd, c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 2, 3])
    with c_qtd: qtd_linhas = st.number_input("Qtd", min_value=1, value=1)
    with c_btn1: btn_add = st.button("➕ Incluir Linha(s)")
    with c_btn2: btn_del = st.button("❌ Excluir Selecionadas")
    with c_btn3: salvar_topo = st.button("💾 Salvar Alterações")

    # [Sua lógica de processamento de botões aqui...]# Lógica de aplicação dos filtros que estão abaixo do Grid
    params = {"usuario": f"eq.{usuario_logado}"} if usuario_logado not in ["ADMIN", "GESTOR"] else {}
    if 'aplicar_filtro' in locals() and aplicar_filtro:
        if data_inicial: params["data"] = f"gte.{data_inicial.strftime('%Y-%m-%d')}"
        if contato_filtro.strip(): params["contato"] = f"ilike.%{contato_filtro.strip()}%"
        # ... (adicione aqui os demais parâmetros de filtro conforme seu padrão original)
        st.session_state.pop("df_grid", None)
        st.rerun()if btn_add:
        hoje_br = datetime.now().strftime("%d/%m/%Y")
        hora_atual = datetime.now().strftime("%H:%M:%S")
        novas = [{"data": hoje_br, "usuario": usuario_logado, "data_cadastro": hoje_br, "hora_cadastro": hora_atual, "id": ""} for _ in range(int(qtd_linhas))]
        st.session_state["df_grid"] = pd.concat([pd.DataFrame(novas), st.session_state["df_grid"]], ignore_index=True)
        st.rerun()if btn_del:
        raw_data = grid_response.get("selected_rows", [])
        if isinstance(raw_data, pd.DataFrame): registros = raw_data.to_dict('records')
        else: registros = raw_data
        
        ids_excluir = [str(r.get("id", "")).strip() for r in registros if str(r.get("id", "")).strip()]
        for id_del in ids_excluir:
            requests.delete(f"{endpoint}?id=eq.{id_del}", headers=headers)
        
        st.session_state.pop("df_grid", None)
        st.rerun()if salvar_topo:
        df_editado = pd.DataFrame(grid_response["data"])
        for _, row in df_editado.iterrows():
            id_val = str(row.get("id", "")).strip()
            dados_payload = {k: v for k, v in row.to_dict().items() if k in colunas_ordem and k != "id"}
            
            if not id_val: # Novo registro
                requests.post(endpoint, headers=headers, json=dados_payload)
            else: # Atualização
                requests.patch(f"{endpoint}?id=eq.{id_val}", headers=headers, json=dados_payload)
        
        st.session_state.pop("df_grid", None)
        st.success("✅ Dados salvos com sucesso!")
        st.rerun()except Exception as e:
        st.error("❌ Ocorreu um erro ao processar a tabela.")
        st.write(traceback.format_exc())

# Chamada da função para rodar a página
if __name__ == "__main__":
    cadastro_atividades_page()
