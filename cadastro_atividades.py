import streamlit as st
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# 1. Configuração essencial da página
st.set_page_config(layout="wide")

# 2. Configurações de Conexão
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"
endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def carregar_grid():
    # Inicializa ou recupera o DataFrame
    if "df_grid" not in st.session_state:
        response = requests.get(endpoint, headers=headers)
        df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
        st.session_state["df_grid"] = df

    # Configuração de todas as colunas conforme solicitado
    gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
    gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=True)
    
    gb.configure_column("data", header_name="Data", minWidth=110)
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
    gb.configure_grid_options(enterMovesDownAfterEdit=True, enableClipboard=True, clipboardDelimitedByChars="\t")
    
    # Renderização final
    AgGrid(
        st.session_state["df_grid"],
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        theme="alpine",
        height=600,
        fit_columns_on_grid_load=True
    )

carregar_grid()
