import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# Configuração da página Streamlit
st.set_page_config(
    page_title="Dashboard Escolar",
    page_icon="Resultados_diagnosticas/img/diplomado.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Adicionando o logotipo na barra lateral
logo_url = 'Resultados_diagnosticas/img/Logomarca da Secretaria de Educação 2021.png'
with st.sidebar:
    st.image(logo_url, width=300)

# Título principal do aplicativo
st.title("📊 Dashboard de Resultados Escolares")
st.markdown("Bem-vindo ao sistema de acesso aos resultados escolares.")

# Função para carregar os dados
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    return df

# Carregamento dos dados
try:
    df_login = load_data('Resultados_diagnosticas/xls/senhas_acesso.xlsx')
    df_dados = load_data('Resultados_diagnosticas/xls/bd_dados.xlsx')
    df_ama = load_data('Resultados_diagnosticas/xls/bd_ama.xlsx')  # Carrega a nova tabela de alfabetização
    
    # Remover espaços extras nos nomes das colunas e valores
    df_login.columns = df_login.columns.str.strip()
    df_dados.columns = df_dados.columns.str.strip()
    df_ama.columns = df_ama.columns.str.strip()  # Limpa os nomes das colunas da nova tabela
    df_login['INEP'] = df_login['INEP'].astype(str).str.strip()
    df_dados['INEP'] = df_dados['INEP'].astype(str).str.strip()
    df_ama['INEP'] = df_ama['INEP'].astype(str).str.strip()  # Limpa a coluna INEP da nova tabela

    # Formatar a coluna 'EDIÇÃO' corretamente
    df_dados['EDIÇÃO'] = df_dados['EDIÇÃO'].astype(float).map(lambda x: f"{x:.1f}")
    df_ama['EDIÇÃO'] = df_ama['EDIÇÃO'].astype(int).astype(str)
    #df_dados['EDIÇÃO'] = df_dados['EDIÇÃO'].astype(int).astype(str)

except FileNotFoundError as e:
    st.error(f"Erro: Arquivo não encontrado: {e.filename}. Verifique os arquivos.")
    st.stop()

# Função de logout
def logout():
    st.session_state.login_success = False
    st.session_state.escola_logada = None
    st.success("Logout realizado com sucesso!")

# Função para formatar a variação
def formatar_variacao(valor, eh_percentual=False):
    if valor > 0:
        sinal = "▲"
        cor = "green"
    elif valor < 0:
        sinal = "▼"
        cor = "red"
    else:
        sinal = ""
        cor = "blue"
    
    if eh_percentual:
        return f'<p style="color:{cor};">{sinal} {valor:.2f}%</p>'
    else:
        return f'<p style="color:{cor};">{sinal} {valor:.2f}</p>'

# Credenciais mestre
INEP_MESTRE = '2307650'

# Barra lateral para login
with st.sidebar:
    st.header("🔒 Acesso Restrito")
    st.markdown("Para acessar, insira o INEP da escola.")

    with st.form(key='login_form'):
        inep = st.text_input('INEP').strip()
        login_button = st.form_submit_button('Login')

# Verificação de login
if 'login_success' not in st.session_state:
    st.session_state.login_success = False

if login_button:
    if inep == INEP_MESTRE:
        st.session_state.login_success = True
        st.session_state.escola_logada = 'TODAS'
        st.success('Login realizado com sucesso como administrador!')
    else:
        usuario = df_login[df_login['INEP'] == inep]
        if not usuario.empty:
            # Verifica se o INEP existe em df_dados
            escola_filtrada = df_dados[df_dados['INEP'] == inep]
            if not escola_filtrada.empty:
                st.session_state.login_success = True
                st.session_state.escola_logada = inep
                nome_escola = escola_filtrada['ESCOLA'].iloc[0]  # Pega o nome da escola
                st.success(f'Login realizado com sucesso! Bem-vindo, {nome_escola}!')
            else:
                st.error('INEP não encontrado nos dados das escolas.')
                st.session_state.login_success = False
        else:
            st.error('INEP incorreto.')
            st.session_state.login_success = False

# Exibir dashboard após login
if st.session_state.login_success:
    if st.sidebar.button("Sair"):
        logout()
    
    # Seletor de escola para administrador (INEP mestre)
    if st.session_state.escola_logada == 'TODAS':
        escolas = df_dados['ESCOLA'].unique().tolist()
        escolas.insert(0, 'TODAS')  # Adiciona a opção "TODAS"
        escola_selecionada = st.selectbox("Selecione a ESCOLA", escolas, key='escola_seletor')
        
        if escola_selecionada == 'TODAS':
            df_escola = df_dados.copy()
            df_escola_ama = df_ama.copy()  # Filtra a tabela de alfabetização para todas as escolas
        else:
            df_escola = df_dados[df_dados['ESCOLA'] == escola_selecionada].copy()
            df_escola_ama = df_ama[df_ama['ESCOLA'] == escola_selecionada].copy()  # Filtra a tabela de alfabetização para a escola selecionada
        
        st.header(f"📊 Resultados de {escola_selecionada if escola_selecionada != 'TODAS' else 'Todas as Escolas'}")
    else:
        # Verifica se st.session_state.escola_logada não é None antes de acessar o nome da escola
        if st.session_state.escola_logada is not None:
            nome_escola = df_dados[df_dados['INEP'] == st.session_state.escola_logada]['ESCOLA'].iloc[0]
            st.markdown(f"<h3>Bem-vindo, escola <span style='color: blue;'>{nome_escola}</span></h3>", unsafe_allow_html=True)
            df_escola = df_dados[df_dados['INEP'] == st.session_state.escola_logada].copy()
            df_escola_ama = df_ama[df_ama['INEP'] == st.session_state.escola_logada].copy()  # Filtra a tabela de alfabetização para a escola logada
        else:
            st.warning("Nenhuma escola logada.")
            df_escola = pd.DataFrame()  # DataFrame vazio para evitar erros
            df_escola_ama = pd.DataFrame()  # DataFrame vazio para a tabela de alfabetização

    if df_escola.empty:
        st.warning("Não há dados disponíveis para esta escola.")
    else:
        # Cria duas abas: uma para os resultados das avaliações e outra para a alfabetização
        tab1, tab2 = st.tabs(["AVALIAÇÃO DIAGNÓSTICA MUNICIPAL", "AVALIAÇÃO MUNICIPAL DE ALFABETIZAÇÃO"])

        with tab1:
            # Classificar edições e separar por ciclos
            edicoes_unicas = sorted(df_escola['EDIÇÃO'].unique(), key=float)
            ponto_corte = len(edicoes_unicas) // 2
            ciclo_1_edicoes = edicoes_unicas[:ponto_corte]
            ciclo_2_edicoes = edicoes_unicas[ponto_corte:]

            df_escola['PERIODO'] = df_escola['EDIÇÃO'].apply(
                lambda x: 'CICLO 1' if x in ciclo_1_edicoes else 'CICLO 2'
            )

            # Filtros por ETAPA e COMP_CURRICULAR
            etapas = df_escola['ETAPA'].unique().tolist()
            etapas.insert(0, 'TODAS')  # Adiciona a opção "TODAS"
            componentes = df_escola['COMP_CURRICULAR'].unique().tolist()
            componentes.insert(0, 'TODOS')  # Adiciona a opção "TODOS"

            etapa_selecionada = st.selectbox("Selecione a ETAPA", etapas)
            componente_selecionado = st.selectbox("Selecione o COMPONENTE CURRICULAR", componentes)

            # Filtrar dados conforme seleção
            if etapa_selecionada == 'TODAS' and componente_selecionado == 'TODOS':
                df_filtrado = df_escola.copy()
            elif etapa_selecionada == 'TODAS':
                df_filtrado = df_escola[df_escola['COMP_CURRICULAR'] == componente_selecionado]
            elif componente_selecionado == 'TODOS':
                df_filtrado = df_escola[df_escola['ETAPA'] == etapa_selecionada]
            else:
                df_filtrado = df_escola[
                    (df_escola['ETAPA'] == etapa_selecionada) &
                    (df_escola['COMP_CURRICULAR'] == componente_selecionado)
                ]

            # Exibir resultados da escola logada (com filtro aplicado)
            st.subheader(f"Resultados Filtrados - {etapa_selecionada} - {componente_selecionado}")
            st.dataframe(df_filtrado.drop(columns=['Unnamed: 0'], errors='ignore'), use_container_width=True)

            # Cálculo de variação entre ciclos (com filtro aplicado)
            variacao_data = []
            for escola in df_filtrado['ESCOLA'].unique():
                df_escola_especifica = df_filtrado[df_filtrado['ESCOLA'] == escola]
                for etapa in [etapa_selecionada] if etapa_selecionada != 'TODAS' else df_filtrado['ETAPA'].unique():
                    for componente in [componente_selecionado] if componente_selecionado != 'TODOS' else df_filtrado['COMP_CURRICULAR'].unique():
                        subset = df_escola_especifica[
                            (df_escola_especifica['ETAPA'] == etapa) &
                            (df_escola_especifica['COMP_CURRICULAR'] == componente)
                        ]
                        # Separa as edições por ano e compara apenas .2 com .1 do mesmo ano
                        edicoes_ano = subset['EDIÇÃO'].unique()
                        for edicao in edicoes_ano:
                            if edicao.endswith('.2'):
                                edicao_1 = edicao.replace('.2', '.1')
                                ciclo_2 = subset[subset['EDIÇÃO'] == edicao]
                                ciclo_1 = subset[subset['EDIÇÃO'] == edicao_1]

                                desempenho_ciclo_1 = ciclo_1['DESEMPENHO_MEDIO'].mean() if not ciclo_1.empty else None
                                desempenho_ciclo_2 = ciclo_2['DESEMPENHO_MEDIO'].mean() if not ciclo_2.empty else None

                                if desempenho_ciclo_1 is not None and desempenho_ciclo_2 is not None:
                                    dif_pontos = desempenho_ciclo_2 - desempenho_ciclo_1
                                    percentual_variacao = (dif_pontos / desempenho_ciclo_1) * 100 if desempenho_ciclo_1 != 0 else 0

                                    # Captura os períodos (edições) que estão sendo comparados
                                    periodo_ciclo_1 = ciclo_1['EDIÇÃO'].iloc[0] if not ciclo_1.empty else None
                                    periodo_ciclo_2 = ciclo_2['EDIÇÃO'].iloc[0] if not ciclo_2.empty else None

                                    # Formata a string dos períodos (ex: "2024.2 - 2024.1")
                                    periodos_comparados = f"{periodo_ciclo_2} - {periodo_ciclo_1}" if periodo_ciclo_1 and periodo_ciclo_2 else "N/A"

                                    variacao_data.append({
                                        'ESCOLA': escola,
                                        'ETAPA': etapa,
                                        'COMP_CURRICULAR': componente,
                                        'Períodos Comparados': periodos_comparados,  # Adiciona os períodos comparados
                                        'Diferença de Pontos': dif_pontos,
                                        'Variação Percentual': percentual_variacao
                                    })
                                else:
                                    variacao_data.append({
                                        'ESCOLA': escola,
                                        'ETAPA': etapa,
                                        'COMP_CURRICULAR': componente,
                                        'Períodos Comparados': "N/A",  # Caso não haja dados para comparação
                                        'Diferença de Pontos': None,
                                        'Variação Percentual': None
                                    })

            if variacao_data:
                variacao_df = pd.DataFrame(variacao_data)

                variacao_df['Diferença de Pontos'] = variacao_df['Diferença de Pontos'].apply(
                    lambda x: formatar_variacao(x) if pd.notnull(x) else '<p style="color:blue;">N/A</p>'
                )
                variacao_df['Variação Percentual'] = variacao_df['Variação Percentual'].apply(
                    lambda x: formatar_variacao(x, eh_percentual=True) if pd.notnull(x) else '<p style="color:blue;">N/A</p>'
                )

                st.subheader("Tabela de Variação Entre Ciclos")
                st.write(variacao_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.write("Não há dados suficientes para calcular a variação entre os ciclos.")

            # Exibir gráficos de barras por PERIODO (após a tabela de variações)
            if etapa_selecionada != 'TODAS' and componente_selecionado != 'TODOS':
                if not df_filtrado.empty:
                    st.subheader(f"Desempenho Médio por Período - {etapa_selecionada} - {componente_selecionado}")
            
                    # Configuração das cores das barras
                    cores = {'CICLO 1': 'skyblue', 'CICLO 2': 'lightgreen'}  # Cores podem ser modificadas aqui
            
                    # Ajuste o tamanho da figura aqui (largura, altura)
                    tamanho_grafico = (8, 4)  # Tamanho do gráfico (pode ser modificado)
                    fig, ax = plt.subplots(figsize=tamanho_grafico)

                    # Adicionar título dentro da figura
                    ax.set_title(
                        f"Desempenho Médio por Período - {etapa_selecionada} - {componente_selecionado}",
                        fontsize=12,  # Tamanho da fonte
                        fontweight='bold',  # Negrito
                        pad=20  # Espaçamento entre o título e o gráfico
                    )
            
                    # Converter as edições para float para ordenação correta
                    df_filtrado['EDIÇÃO_FLOAT'] = df_filtrado['EDIÇÃO'].apply(lambda x: float(x))
            
                    # Ordenar os dados por EDIÇÃO antes de plotar
                    df_filtrado_ordenado = df_filtrado.sort_values(by='EDIÇÃO_FLOAT')
            
                    # Plotar os dados ordenados
                    for periodo, cor in cores.items():
                        dados_periodo = df_filtrado_ordenado[df_filtrado_ordenado['PERIODO'] == periodo]
                        barras = ax.bar(dados_periodo['EDIÇÃO'], dados_periodo['DESEMPENHO_MEDIO'], color=cor, label=periodo)
            
                        # Adicionar rótulos de desempenho médio nas barras
                        for barra in barras:
                            altura = barra.get_height()
                            ax.text(
                                barra.get_x() + barra.get_width() / 2,  # Posição X do rótulo
                                altura + 0.05,  # Posição Y do rótulo (acima da barra)
                                f'{altura:.2f}',  # Valor do desempenho médio
                                ha='center',  # Alinhamento horizontal
                                va='bottom',  # Alinhamento vertical
                                color='blue',  # Cor do rótulo
                                fontsize=10  # Tamanho da fonte
                            )
            
                    # Configuração dos rótulos dos eixos
                    ax.set_xlabel('Edição', color='blue', fontsize=12)  # Rótulo do eixo X
                    ax.set_ylabel('Desempenho Médio', color='blue', fontsize=12)  # Rótulo do eixo Y
                    ax.tick_params(axis='x', colors='blue', labelsize=10, rotation=45)  # Configuração dos ticks do eixo X
                    ax.tick_params(axis='y', colors='blue', labelsize=10)  # Configuração dos ticks do eixo Y
                    ax.legend()
            
                    # Exibir o gráfico
                    st.pyplot(fig)

                    # Botão de download do gráfico
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png')
                    buf.seek(0)
                    st.download_button(
                        label="Baixar Gráfico (PNG)",
                        data=buf,
                        file_name="grafico_desempenho.png",
                        mime="image/png"
                    )
                else:
                    st.write("Não há dados disponíveis para os filtros selecionados.")
            else:
                st.info("Os gráficos são exibidos apenas quando uma ETAPA e um COMPONENTE CURRICULAR específicos são selecionados.")
                
                # ... (código original anterior)

        # Exibir gráfico de desempenho médio por região e por edição
        if etapa_selecionada != 'TODAS' and componente_selecionado != 'TODOS':
            if st.session_state.escola_logada == 'TODAS':
                # INEP mestre: mostra todas as regiões
                df_regiao_edicao = df_filtrado.groupby(['REGIAO', 'EDIÇÃO'])['DESEMPENHO_MEDIO'].mean().reset_index()
                titulo_grafico = "Desempenho Médio por Região e Edição (Todas as Regiões)"
            else:
                # Escola logada: mostra apenas a região da escola logada
                try:
                    # Verifica se a coluna 'REGIAO' existe no DataFrame
                    if 'REGIAO' in df_dados.columns:
                        regiao_escola = df_dados[df_dados['INEP'] == st.session_state.escola_logada]['REGIAO'].iloc[0]
                        df_regiao_edicao = df_filtrado[df_filtrado['REGIAO'] == regiao_escola].groupby(['REGIAO', 'EDIÇÃO'])['DESEMPENHO_MEDIO'].mean().reset_index()
                        titulo_grafico = f"Desempenho Médio por Região e Edição (Região: {regiao_escola})"
                    else:
                        st.error("A coluna 'REGIAO' não foi encontrada no DataFrame.")
                        st.stop()
                except IndexError:
                    st.error("Não foi possível encontrar a região da escola logada. Verifique os dados.")
                    st.stop()
        
            if not df_regiao_edicao.empty:
                st.subheader(titulo_grafico)
        
                # Configuração do gráfico de barras agrupadas por região e edição
                fig_regiao_edicao, ax_regiao_edicao = plt.subplots(figsize=(12, 6))
        
                # Obter as regiões e edições únicas
                regioes = df_regiao_edicao['REGIAO'].unique()
                edicoes = df_regiao_edicao['EDIÇÃO'].unique()
        
                # Largura das barras
                largura_barra = 0.15
                posicoes = range(len(edicoes))
        
                # Cores para as barras
                cores = plt.cm.get_cmap('tab20', len(regioes))  # Paleta de cores para as regiões
        
                # Plotar as barras para cada região
                for i, regiao in enumerate(regioes):
                    dados_regiao = df_regiao_edicao[df_regiao_edicao['REGIAO'] == regiao]
                    barras = ax_regiao_edicao.bar(
                        [p + i * largura_barra for p in posicoes],  # Posições das barras
                        dados_regiao['DESEMPENHO_MEDIO'],  # Valores do desempenho médio
                        width=largura_barra,  # Largura das barras
                        label=regiao  # Rótulo da região
                    )
        
                    # Adicionar rótulos de desempenho médio nas barras
                    for barra in barras:
                        altura = barra.get_height()
                        ax_regiao_edicao.text(
                            barra.get_x() + barra.get_width() / 2,  # Posição X do rótulo
                            altura + 0.05,  # Posição Y do rótulo (acima da barra)
                            f'{altura:.2f}',  # Valor do desempenho médio
                            ha='center',  # Alinhamento horizontal
                            va='bottom',  # Alinhamento vertical
                            color='black',  # Cor do rótulo
                            fontsize=8  # Tamanho da fonte
                        )
        
                # Configuração dos rótulos dos eixos
                ax_regiao_edicao.set_xlabel('Edição', color='blue', fontsize=12)  # Rótulo do eixo X
                ax_regiao_edicao.set_ylabel('Desempenho Médio', color='blue', fontsize=12)  # Rótulo do eixo Y
                ax_regiao_edicao.set_xticks([p + largura_barra * (len(regioes) - 1) / 2 for p in posicoes])
                ax_regiao_edicao.set_xticklabels(edicoes, rotation=45, color='blue', fontsize=10)
                ax_regiao_edicao.tick_params(axis='y', colors='blue', labelsize=10)
        
                # Adicionar legenda informando a região (apenas para escola logada)
                if st.session_state.escola_logada != 'TODAS':
                    ax_regiao_edicao.annotate(
                        f"Região: {regiao_escola}",
                        xy=(0.5, 1.05),  # Posição do texto (acima do gráfico)
                        xycoords='axes fraction',
                        ha='center',  # Alinhamento horizontal
                        va='bottom',  # Alinhamento vertical
                        fontsize=12,  # Tamanho da fonte
                        color='blue'  # Cor do texto
                    )
        
                # Adicionar grid para melhorar a visualização
                ax_regiao_edicao.grid(axis='y', linestyle='--', alpha=0.7)
        
                # Ajustar o layout para evitar cortes
                plt.tight_layout()
        
                # Exibir o gráfico
                st.pyplot(fig_regiao_edicao)
        
                # Botão de download do gráfico
                buf_regiao_edicao = io.BytesIO()
                fig_regiao_edicao.savefig(buf_regiao_edicao, format='png', dpi=300, bbox_inches='tight')
                buf_regiao_edicao.seek(0)
                st.download_button(
                    label="Baixar Gráfico (PNG)",
                    data=buf_regiao_edicao,
                    file_name="grafico_desempenho_regiao_edicao.png",
                    mime="image/png"
                )
            else:
                st.warning("Não há dados disponíveis para a região e edição selecionadas.")
        with tab2:
            # Exibir resultados da tabela de alfabetização
            st.subheader("Percentual de Alfabetização")
            if not df_escola_ama.empty:
                st.dataframe(df_escola_ama.drop(columns=['Unnamed: 0'], errors='ignore'), use_container_width=True)

                # Remover decimais da coluna EDIÇÃO
                df_escola_ama['EDIÇÃO'] = df_escola_ama['EDIÇÃO'].astype(str).str.replace('.0', '', regex=False)

                # Ordenar os dados por EDIÇÃO em ordem crescente
                df_escola_ama = df_escola_ama.sort_values(by='EDIÇÃO', ascending=True)

                # Gráfico de barras verticais para o percentual de alfabetização por edição
                st.subheader("Gráfico de Barras - Percentual de Alfabetização por Edição")

                # Configuração do gráfico de barras
                fig_bar, ax_bar = plt.subplots(figsize=(8, 4))
                barras = ax_bar.bar(df_escola_ama['EDIÇÃO'], df_escola_ama['PERCENTUAL ALFABETIZAÇÃO'], color='blue')

                # Adicionar rótulos de percentual nas barras
                for barra in barras:
                    altura = barra.get_height()
                    ax_bar.text(
                        barra.get_x() + barra.get_width() / 2,  # Posição X do rótulo
                        altura + 0.05,  # Posição Y do rótulo (acima da barra)
                        f'{altura:.1f}%',  # Valor do percentual
                        ha='center',  # Alinhamento horizontal
                        va='bottom',  # Alinhamento vertical
                        color='black',  # Cor do rótulo
                        fontsize=8  # Tamanho da fonte
                    )

                # Configuração dos rótulos dos eixos
                ax_bar.set_xlabel('Edição', color='blue', fontsize=12)  # Rótulo do eixo X
                ax_bar.set_ylabel('Percentual de Alfabetização', color='blue', fontsize=12)  # Rótulo do eixo Y
                ax_bar.tick_params(axis='x', colors='blue', labelsize=10)  # Configuração dos ticks do eixo X
                ax_bar.tick_params(axis='y', colors='blue', labelsize=10)  # Configuração dos ticks do eixo Y

                # Exibir o gráfico
                st.pyplot(fig_bar)

                # Botão de download do gráfico
                buf_bar = io.BytesIO()
                fig_bar.savefig(buf_bar, format='png')
                buf_bar.seek(0)
                st.download_button(
                    label="Baixar Gráfico (PNG)",
                    data=buf_bar,
                    file_name="grafico_alfabetizacao_barras.png",
                    mime="image/png"
                )

                # Gráfico de linhas para o percentual de alfabetização por edição
                st.subheader("Gráfico de Linhas - Percentual de Alfabetização por Edição")

                # Configuração do gráfico de linhas
                fig_line, ax_line = plt.subplots(figsize=(8, 4))
                ax_line.plot(df_escola_ama['EDIÇÃO'], df_escola_ama['PERCENTUAL ALFABETIZAÇÃO'], marker='o', color='blue', linestyle='-', linewidth=2, markersize=8)

                # Adicionar rótulos de percentual nos pontos
                for i, (edicao, percentual) in enumerate(zip(df_escola_ama['EDIÇÃO'], df_escola_ama['PERCENTUAL ALFABETIZAÇÃO'])):
                    ax_line.text(
                        edicao,  # Posição X do rótulo
                        percentual + 0.05,  # Posição Y do rótulo (acima do ponto)
                        f'{percentual:.1f}%',  # Valor do percentual
                        ha='center',  # Alinhamento horizontal
                        va='bottom',  # Alinhamento vertical
                        color='black',  # Cor do rótulo
                        fontsize=8  # Tamanho da fonte
                    )

                # Configuração dos rótulos dos eixos
                ax_line.set_xlabel('Edição', color='blue', fontsize=12)  # Rótulo do eixo X
                ax_line.set_ylabel('Percentual de Alfabetização', color='blue', fontsize=12)  # Rótulo do eixo Y
                ax_line.tick_params(axis='x', colors='blue', labelsize=10)  # Configuração dos ticks do eixo X
                ax_line.tick_params(axis='y', colors='blue', labelsize=10)  # Configuração dos ticks do eixo Y

                # Exibir o gráfico
                st.pyplot(fig_line)

                # Botão de download do gráfico
                buf_line = io.BytesIO()
                fig_line.savefig(buf_line, format='png')
                buf_line.seek(0)
                st.download_button(
                    label="Baixar Gráfico (PNG)",
                    data=buf_line,
                    file_name="grafico_alfabetizacao_linhas.png",
                    mime="image/png"
                )
            else:
                st.warning("Não há dados disponíveis para o percentual de alfabetização.")
else:
    st.info("Por favor, faça login para acessar os dados.")
