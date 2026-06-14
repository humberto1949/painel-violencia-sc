import pandas as pd
import streamlit as st
import altair as alt
import re

st.set_page_config(page_title="Painel de Dados - SC", layout="wide")

# CSS para customização visual e remoção de elementos de interface
st.markdown(
    """
    <style>
    /* Esconde o menu de opções e o cabeçalho/footer do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    h1 {
        font-size: 28px !important;
        font-weight: 700 !important;
        padding-bottom: 10px !important;
    }
    div[data-baseweb="select"] {
        width: max-content !important;
        min-width: 400px;
    }
    div[data-testid="stSelectbox"] {
        width: max-content !important;
    }
    [data-testid="stDataFrameHeaderCell"],
    [data-testid="stDataFrameHeaderCell"] div,
    [data-testid="stDataFrameHeaderCell"] span {
        text-align: center !important;
        justify-content: center !important;
    }
    [data-testid="stDataFrameDataCell"] div,
    [data-testid="stDataFrameDataCell"] span {
        text-align: center !important;
        justify-content: center !important;
        display: flex !important;
        align-items: center !important;
    }
    .grafico-container {
        overflow-x: auto;
        overflow-y: auto;
        width: 100%;
        padding-bottom: 15px;
    }
    .vega-actions {
        display: none !important;
    }
    .legenda-container {
        display: flex;
        gap: 20px;
        margin-top: 15px;
        margin-bottom: 15px;
        font-family: sans-serif;
    }
    .legenda-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
        font-size: 14px;
    }
    .legenda-cor {
        width: 24px;
        height: 12px;
        border-radius: 3px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Violência contra mulher / Dados por região")

CHAVE_PLANILHA = "2PACX-1vRw2uafpMmb-dtOv9fZpqN1vVwkdxV6diO1bUj-FPQJm_-M5vIEEW_q7mqoEE_AmrF_WWjL92KfB3xk"

MAPA_REGIOES = {
    "Grande Florianópolis": "0",
    "Norte": "2083350771",
    "Oeste": "1832830464",
    "Serrana": "1821320456",
    "Sul": "993904023",
    "Itajai": "575766075",
}

MAPA_REGIOES = dict(sorted(MAPA_REGIOES.items()))

@st.cache_data
def carregar_dados_brutos(chave, gid):
    url_csv = f"https://docs.google.com/spreadsheets/d/e/{chave}/pub?gid={gid}&single=true&output=csv"
    df = pd.read_csv(url_csv, header=None, dtype=str)
    return df

try:
    opcoes_regiao = ["Escolha a Região..."] + list(MAPA_REGIOES.keys())
    aba_selecionada = st.selectbox("Selecione a Região (Guia):", options=opcoes_regiao)

    if aba_selecionada == "Escolha a Região...":
        st.info("ℹ️ Por favor, selecione uma região acima para começar.")
    else:
        gid_atual = MAPA_REGIOES[aba_selecionada]
        
        with st.spinner(f"Carregando dados de: {aba_selecionada}..."):
            df_bruto = carregar_dados_brutos(CHAVE_PLANILHA, gid_atual)

        populacao_atual = None
        texto_populacao_formatado = "Não localizada na célula E3"
        
        try:
            if df_bruto.shape[0] > 2 and df_bruto.shape[1] > 4:
                celula_e3 = str(df_bruto.iloc[2, 4]).strip()
                apenas_numeros = re.sub(r"\D", "", celula_e3)
                if apenas_numeros:
                    populacao_atual = float(apenas_numeros)
                    texto_populacao_formatado = f"{int(populacao_atual):,}".replace(",", ".")
        except Exception:
            pass
            
        if not populacao_atual or populacao_atual == 0:
            populacao_atual = 1000000
            texto_populacao_formatado = "Erro de leitura / Célula vazia"
            
        st.metric(label="👥 População Feminina Aproximada", value=texto_populacao_formatado)

        indices_titulos = []
        nomes_titulos = []

        for idx, row in df_bruto.iterrows():
            celula_texto = str(row.iloc[0]).upper()
            if "FATO COMUNICADO" in celula_texto or "OCORRÊNCIA" in celula_texto:
                indices_titulos.append(idx)
                nomes_titulos.append(str(row.iloc[0]).strip())

        if not nomes_titulos:
            st.warning("⚠️ Nenhum padrão 'FATO COMUNICADO' localizado nesta guia.")
            opcoes_combo = ["Padrão não encontrado"]
        else:
            opcoes_combo = ["Escolha a Ocorrência..."] + nomes_titulos

        chave_seletor_dinamico = f"seletor_ocorrencia_{aba_selecionada}"
        titulo_selecionado = st.selectbox("Selecione o Tipo de Ocorrência:", options=opcoes_combo, key=chave_seletor_dinamico)

        if titulo_selecionado == "Escolha a Ocorrência...":
            st.info("ℹ️ Por favor, selecione o tipo de ocorrência desejado.")
        elif titulo_selecionado == "Padrão não encontrado":
            st.dataframe(df_bruto, use_container_width=True)
        else:
            st.write("---")
            idx_selecionado = nomes_titulos.index(titulo_selecionado)
            linha_inicio_titulo = indices_titulos[idx_selecionado]
            linha_cabecalho_colunas = linha_inicio_titulo + 1
            linha_inicio_dados = linha_inicio_titulo + 2

            if idx_selecionado + 1 < len(indices_titulos):
                linha_fim_dados = indices_titulos[idx_selecionado + 1]
            else:
                linha_fim_dados = len(df_bruto)

            df_bloco = df_bruto.iloc[linha_inicio_dados:linha_fim_dados].copy()
            nomes_colunas = []
            for i in range(df_bloco.shape[1]):
                celula_cabecalho = str(df_bruto.iloc[linha_cabecalho_colunas, i]).strip()
                nomes_colunas.append(celula_cabecalho if celula_cabecalho.lower() != "nan" and celula_cabecalho != "" else f"Unnamed_{i}")

            df_bloco.columns = nomes_colunas
            df_bloco = df_bloco.dropna(how="all").reset_index(drop=True)

            coluna_ano_real = df_bloco.columns[0]
            coluna_casos_reais = None
            for col in df_bloco.columns:
                nome_coluna = str(col).lower()
                if "ano" in nome_coluna: coluna_ano_real = col
                if "caso" in nome_coluna or "real" in nome_coluna: coluna_casos_reais = col

            colunas_permitidas = []
            for col in df_bloco.columns:
                c_low = str(col).lower()
                if "unnamed" not in c_low:
                    if col == coluna_ano_real or col == coluna_casos_reais or "pa" in c_low or "pg" in c_low or "media" in c_low or "média" in c_low:
                        colunas_permitidas.append(col)

            df_exibicao = df_bloco[colunas_permitidas].copy()
            df_exibicao = df_exibicao[df_exibicao[coluna_ano_real].astype(str).str.strip().str.isnumeric()]

            if coluna_casos_reais and not df_exibicao.empty:
                vetor_casos = df_exibicao[coluna_casos_reais].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                numeros_finais = pd.to_numeric(vetor_casos, errors="coerce").to_numpy()
                
                strings_var_final = ["-----"]
                valores_per_capita = []
                
                if len(numeros_finais) > 0:
                    if pd.isna(numeros_finais[0]): 
                        valores_per_capita.append("-----")
                    else:
                        calc_pc = (numeros_finais[0] / populacao_atual) * 1000
                        valores_per_capita.append(f"{round(calc_pc, 1):.1f}")

                for idx in range(1, len(numeros_finais)):
                    anterior, atual = numeros_finais[idx - 1], numeros_finais[idx]
                    if pd.isna(anterior) or pd.isna(atual) or anterior == 0: 
                        strings_var_final.append("-----")
                    else:
                        calc = ((atual - anterior) / anterior) * 100
                        calc_arredondado = round(calc, 1)
                        if calc_arredondado == 0.0:
                            strings_var_final.append("-----")
                        else:
                            strings_var_final.append(f"{'+' if calc_arredondado > 0 else ''}{calc_arredondado:.1f}%")
                    
                    if pd.isna(atual):
                        valores_per_capita.append("-----")
                    else:
                        calc_pc = (atual / populacao_atual) * 1000
                        valores_per_capita.append(f"{round(calc_pc, 1):.1f}")
                
                df_exibicao["VARIAÇÃO %"] = strings_var_final
                df_exibicao["Taxa por 1.000 Hab."] = valores_per_capita
                
                todas_cols = list(df_exibicao.columns)
                if "VARIAÇÃO %" in todas_cols: todas_cols.remove("VARIAÇÃO %")
                if "Taxa por 1.000 Hab." in todas_cols: todas_cols.remove("Taxa por 1.000 Hab.")
                
                idx_pos = todas_cols.index(coluna_casos_reais)
                todas_cols.insert(idx_pos + 1, "VARIAÇÃO %")
                todas_cols.insert(idx_pos + 2, "Taxa por 1.000 Hab.")
                df_exibicao = df_exibicao[todas_cols]

            for coluna in df_exibicao.columns:
                df_exibicao[coluna] = df_exibicao[coluna].astype(str).str.strip().replace(["", "None", "none", "NaN", "nan", None], "-----")

            st.subheader(f"📋 Tabela de Dados — {titulo_selecionado}")
            if not df_exibicao.empty:
                st.dataframe(df_exibicao, width=950, hide_index=True)
                
                if coluna_casos_reais:
                    st.write("---")
                    st.subheader("📊 Visualização Gráfica")
                    tipo_grafico = st.radio("Escolha o formato do gráfico:", options=["Linha", "Barra"], horizontal=True, key=f"radio_{aba_selecionada}_{idx_selecionado}")

                    mapeamento_checkboxes = {}
                    for col in df_exibicao.columns:
                        c_low = col.lower()
                        if col == coluna_ano_real or col == coluna_casos_reais or "variação" in c_low or "1.000" in c_low: continue
                        if "pa" in c_low and "media" not in c_low: mapeamento_checkboxes["Projeções PA"] = col
                        elif "pg" in c_low and "media" not in c_low: mapeamento_checkboxes["Projeções PG"] = col
                        elif "aumento" in c_low: mapeamento_checkboxes["Aumento"] = col
                        elif "redução" in c_low: mapeamento_checkboxes["Redução"] = col

                    colunas_selecionadas_reais = []
                    if mapeamento_checkboxes:
                        st.markdown("**Selecione as projeções desejadas:**")
                        opcoes_labels = list(mapeamento_checkboxes.keys())
                        cols_checkboxes = st.columns(len(opcoes_labels))
                        for i, label in enumerate(opcoes_labels):
                            with cols_checkboxes[i]:
                                if st.checkbox(label, key=f"c_{label}_{aba_selecionada}_{idx_selecionado}"):
                                    colunas_selecionadas_reais.append(mapeamento_checkboxes[label])

                    if st.button("Gerar Gráfico", key=f"btn_{aba_selecionada}_{idx_selecionado}"):
                        st.markdown("""<div class="legenda-container"><div class="legenda-item"><div class="legenda-cor" style="background-color: #007bff;"></div><span>Casos Reais</span></div><div class="legenda-item"><div class="legenda-cor" style="background-color: #28a745;"></div><span>Projeções PA</span></div><div class="legenda-item"><div class="legenda-cor" style="background-color: #dc3545;"></div><span>Projeções PG</span></div></div>""", unsafe_allow_html=True)
                        
                        df_grafico = df_exibicao.copy()
                        colunas_para_plotar = [coluna_casos_reais] + colunas_selecionadas_reais
                        for col in colunas_para_plotar:
                            df_grafico[col] = pd.to_numeric(df_grafico[col].astype(str).str.replace(".", "").str.replace(",", "."), errors="coerce")
                        
                        df_grafico[coluna_ano_real] = pd.to_numeric(df_grafico[coluna_ano_real], errors="coerce")
                        df_grafico = df_grafico.dropna(subset=[coluna_ano_real]).sort_values(by=coluna_ano_real)
                        
                        mapeamento_cores = {}
                        for col in colunas_para_plotar:
                            c_low = col.lower()
                            if col == coluna_casos_reais: mapeamento_cores[col] = "#007bff"
                            elif "pa" in c_low: mapeamento_cores[col] = "#28a745"
                            elif "pg" in c_low: mapeamento_cores[col] = "#dc3545"
                            else: mapeamento_cores[col] = "#6c757d"

                        df_longo = df_grafico.melt(id_vars=[coluna_ano_real], value_vars=colunas_para_plotar, var_name="Métrica", value_name="Valores")
                        
                        if not df_longo.dropna(subset=["Valores"]).empty:
                            base = alt.Chart(df_longo).encode(
                                x=alt.X(f"{coluna_ano_real}:O", title="Ano", axis=alt.Axis(labelAngle=0)),
                                y=alt.Y("Valores:Q", title="Quantidade de Casos"),
                                color=alt.Color("Métrica:N", scale=alt.Scale(domain=list(mapeamento_cores.keys()), range=list(mapeamento_cores.values())), legend=None)
                            )
                            chart = base.mark_line(strokeWidth=4, point=alt.OverlayMarkDef(size=80, filled=True)) if tipo_grafico == "Linha" else base.mark_bar().encode(xOffset="Métrica:N")
                            st.markdown('<div class="grafico-container">', unsafe_allow_html=True)
                            st.altair_chart(chart.properties(width=900, height=450).interactive(), use_container_width=False)
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ Dados insuficientes para plotagem do gráfico.")
            else:
                st.warning("⚠️ Bloco sem dados estruturados.")
except Exception as e:
    st.error(f"Erro: {e}")
