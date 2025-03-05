import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
    st.image(logo_url, width=200)

# Título principal do aplicativo
st.title("📊 Dashboard de Resultados Escolares - Avaliações Diagnósticas Municipais 2024")
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
    
    # Remover espaços extras nos nomes das colunas e valores
    df_login.columns = df_login.columns.str.strip()
    df_dados.columns = df_dados.columns.str.strip()
    df_login['INEP'] = df_login['INEP'].astype(str).str.strip()

    # Formatar a coluna 'EDIÇÃO' corretamente
    df_dados['EDIÇÃO'] = df_dados['EDIÇÃO'].astype(float).map(lambda x: f"{x:.1f}")

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
    st.markdown("Para acessar, insira suas credenciais correspodente ao INEP da escola.")

    with st.form(key='login_form'):
        inep = st.text_input('INEP').strip()
        login_button = st.form_submit_button('Login')

# Verificação de login
if 'login_success' not in st.session_state:
    st.session_state.login_success = False

if login_button:
    if inep == INEP_MESTRE and senha == SENHA_MESTRE:
        st.session_state.login_success = True
        st.session_state.escola_logada = 'TODAS'
        st.success('Login realizado com sucesso como administrador!')
    else:
        usuario = df_login[(df_login['INEP'] == inep) & (df_login['SENHA'] == senha)]
        if not usuario.empty:
            # Verifica se o INEP existe na planilha bd_dados
            escola_df = df_dados[df_dados['INEP'] == inep]
            if not escola_df.empty:
                st.session_state.login_success = True
                st.session_state.escola_logada = inep
                nome_escola = escola_df['ESCOLA'].iloc[0]  # Pega o nome da escola
                st.success(f'Login realizado com sucesso! Bem-vindo, {nome_escola}!')
            else:
                st.error('INEP não encontrado na base de dados.')
                st.session_state.login_success = False
        else:
            st.error('INEP ou Senha incorretos.')
            st.session_state.login_success = False

# Exibir dashboard após login
if st.session_state.login_success:
    if st.sidebar.button("Sair"):
        logout()
    
    # Seletor de escola para administrador (senha mestre)
    if st.session_state.escola_logada == 'TODAS':
        escolas = df_dados['ESCOLA'].unique().tolist()
        escolas.insert(0, 'TODAS')  # Adiciona a opção "TODAS"
        escola_selecionada = st.sidebar.selectbox("Selecione a ESCOLA", escolas)
        
        if escola_selecionada == 'TODAS':
            df_escola = df_dados.copy()
        else:
            df_escola = df_dados[df_dados['ESCOLA'] == escola_selecionada].copy()
        
        st.header(f"📊 Resultados de {escola_selecionada if escola_selecionada != 'TODAS' else 'Todas as Escolas'}")
    else:
        # Verifica se st.session_state.escola_logada não é None antes de acessar o nome da escola
        if st.session_state.escola_logada is not None:
            nome_escola = df_dados[df_dados['INEP'] == st.session_state.escola_logada]['ESCOLA'].iloc[0]
            #st.header(f"📊 Resultados da Escola: {nome_escola}")
            st.markdown(f"<h3>Bem-vindo, escola <span style='color: blue;'>{nome_escola}</span></h3>", unsafe_allow_html=True)
            df_escola = df_dados[df_dados['INEP'] == st.session_state.escola_logada].copy()
        else:
            st.warning("Nenhuma escola logada.")
            df_escola = pd.DataFrame()  # DataFrame vazio para evitar erros

    if df_escola.empty:
        st.warning("Não há dados disponíveis para esta escola.")
    else:
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
        st.dataframe(df_filtrado, use_container_width=True)

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
                    ciclo_1 = subset[subset['PERIODO'] == 'CICLO 1']
                    ciclo_2 = subset[subset['PERIODO'] == 'CICLO 2']

                    desempenho_ciclo_1 = ciclo_1['DESEMPENHO_MEDIO'].mean() if not ciclo_1.empty else None
                    desempenho_ciclo_2 = ciclo_2['DESEMPENHO_MEDIO'].mean() if not ciclo_2.empty else None

                    if desempenho_ciclo_1 is not None and desempenho_ciclo_2 is not None:
                        dif_pontos = desempenho_ciclo_2 - desempenho_ciclo_1
                        percentual_variacao = (dif_pontos / desempenho_ciclo_1) * 100 if desempenho_ciclo_1 != 0 else 0

                        variacao_data.append({
                            'ESCOLA': escola,
                            'ETAPA': etapa,
                            'COMP_CURRICULAR': componente,
                            'Diferença de Pontos': dif_pontos,
                            'Variação Percentual': percentual_variacao
                        })
                    else:
                        variacao_data.append({
                            'ESCOLA': escola,
                            'ETAPA': etapa,
                            'COMP_CURRICULAR': componente,
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

                for periodo, cor in cores.items():
                    dados_periodo = df_filtrado[df_filtrado['PERIODO'] == periodo]
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
                ax.tick_params(axis='x', colors='blue', labelsize=10)  # Configuração dos ticks do eixo X
                ax.tick_params(axis='y', colors='blue', labelsize=10)  # Configuração dos ticks do eixo Y
                ax.legend()

                st.pyplot(fig)
            else:
                st.write("Não há dados disponíveis para os filtros selecionados.")
        else:
            st.info("Os gráficos são exibidos apenas quando uma ETAPA e um COMPONENTE CURRICULAR específicos são selecionados.")
else:
    st.info("Por favor, faça login para acessar os dados.")
