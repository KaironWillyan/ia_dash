import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from unidecode import unidecode

# Função para normalizar textos
def normalizar_texto(texto):
    if isinstance(texto, str):
        return unidecode(texto).lower().strip()
    return texto

# Função para converter datas
def converter_data(data_string):
    if isinstance(data_string, str) and data_string != 'Não informado':
        try:
            return datetime.strptime(data_string, '%d/%m/%Y').date()
        except ValueError:
            try:
                return datetime.strptime(data_string, '%d/%m/%Y %H:%M').date()
            except ValueError:
                return None
    return None

# Função para converter data e hora
def converter_data_hora(data_string):
    if isinstance(data_string, str) and data_string != 'Não informado':
        try:
            return datetime.strptime(data_string, '%d/%m/%Y %H:%M')
        except ValueError:
            try:
                return datetime.strptime(data_string, '%d/%m/%Y').replace(hour=0, minute=0, second=0)
            except ValueError:
                return None
    return None

file_path = './dataset/2024-12-26T20-43_export.csv'

# Carregar e processar o conjunto de dados
try:
    data = pd.read_csv(file_path, encoding='utf-8')
except UnicodeDecodeError:
    data = pd.read_csv(file_path, encoding='ISO-8859-1')

# Limpeza e transformação
data = data.dropna(axis=1, how='all')  # Remove colunas vazias
data = data.iloc[1:]  # Remove linha com os nomes das colunas
data.columns = [
    "id", "documento", "documento_tipo", "codigo_documento", "numero_prontuario",
    "nome_hospital_atual", "nome_hospital_solicitante", "grupo_sanguineo", "fator_rh",
    "data_nascimento", "cpf", "cartao_sus", "profissao", "bairro", "cep", "municipio",
    "estado_civil", "grau_instrucao", "sexo", "data_admissao", "data_alta", "motivo_alta",
    "justificativa_internacao", "cor_classificacao_risco", "sinais_sintomas",
    "diagnostico_principal", "diagnostico_provisorio", "causa_obito", "data_obito",
    "codigo_procedimento_solicitado", "codigo_procedimento_principal",
    "procedimentos_realizados", "exames", "dieta", "crm"
]

# Normalizar textos
data['nome_hospital_atual'] = data['nome_hospital_atual'].apply(normalizar_texto)
data['bairro'] = data['bairro'].apply(normalizar_texto)
data['diagnostico_principal'] = data['diagnostico_principal'].apply(normalizar_texto)
data['motivo_alta'] = data['motivo_alta'].apply(normalizar_texto)
data['foi_obito'] = data['motivo_alta'].apply(lambda x: 'obito' in str(x).lower())
data['causa_obito'] = data['causa_obito'].apply(normalizar_texto)
data['sexo'] = data['sexo'].apply(normalizar_texto)

# Converter datas
data['data_nascimento'] = data['data_nascimento'].apply(converter_data)
data['data_admissao'] = data['data_admissao'].apply(converter_data_hora)
data['data_alta'] = data['data_alta'].apply(converter_data_hora)
data['data_obito'] = data['data_obito'].apply(converter_data)

# Criar novas colunas
data['idade'] = data.apply(lambda row: (datetime.now().date() - row['data_nascimento']).days // 365 if row['data_nascimento'] else None, axis=1)
data['faixa_etaria'] = data.apply(lambda row: pd.cut(
    [row['idade']], 
    bins=[0, 5, 12, 18, 30, 50, 70, 100], 
    labels=['0-5', '6-12', '13-18', '19-30', '31-50', '51-70', '70+'], 
    right=False,
    include_lowest=True
)[0] if row['idade'] is not None else None, axis=1)

# Inicializar o aplicativo Dash
app = dash.Dash(__name__)
app.title = "Painel de Gestão Hospitalar"

# Layout do Painel
app.layout = html.Div([
    html.H1("Painel de Gestão Hospitalar", style={'text-align': 'center'}),

    html.Div([
        html.Label("Selecione o Hospital:"),
        dcc.Dropdown(
            id="filtro-hospital",
            options=[{'label': h, 'value': h} for h in data['nome_hospital_atual'].dropna().unique()],
            placeholder="Todos os Hospitais",
            multi=False,
        ),
        html.Label("Selecione o Intervalo de Datas:"),
        dcc.DatePickerRange(
            id="intervalo-datas",
            start_date=data['data_admissao'].dropna().min().strftime('%Y-%m-%d') if not data['data_admissao'].dropna().empty else None,
            end_date=data['data_alta'].dropna().max().strftime('%Y-%m-%d') if not data['data_alta'].dropna().empty else None,
            display_format='YYYY-MM-DD'
        ),
    ], style={'width': '40%', 'margin': 'auto'}),

    html.Hr(),

    # Adicionar gráficos
    html.Div([
        dcc.Graph(id='grafico-procedimentos'),
        dcc.Graph(id='grafico-pacientes-por-sexo'),
        dcc.Graph(id='grafico-pacientes-por-faixa-etaria'),
        dcc.Graph(id='grafico-tipos-procedimentos'),
        dcc.Graph(id='grafico-procedimentos-por-procedencia'),
        dcc.Graph(id='grafico-obitos-por-hospital'),
        dcc.Graph(id='grafico-obitos-totais'),
        dcc.Graph(id='grafico-causas-obitos'),
        dcc.Graph(id='grafico-motivos-altas'),
        dcc.Graph(id='grafico-internacoes-medico'),
        dcc.Graph(id='grafico-admissoes-por-periodo'),
    ])
])

@app.callback(
    [Output('grafico-procedimentos', 'figure'),
     Output('grafico-pacientes-por-sexo', 'figure'),
     Output('grafico-pacientes-por-faixa-etaria', 'figure'),
     Output('grafico-tipos-procedimentos', 'figure'),
     Output('grafico-procedimentos-por-procedencia', 'figure'),
     Output('grafico-obitos-por-hospital', 'figure'),
     Output('grafico-obitos-totais', 'figure'),
     Output('grafico-causas-obitos', 'figure'),
     Output('grafico-motivos-altas', 'figure'),
     Output('grafico-internacoes-medico', 'figure'),
     Output('grafico-admissoes-por-periodo', 'figure')],
    [Input('filtro-hospital', 'value'),
     Input('intervalo-datas', 'start_date'),
     Input('intervalo-datas', 'end_date')]
)
def atualizar_graficos(hospital, data_inicio, data_fim):
    try:
        # Imprimir parâmetros recebidos
        print(f"\nParâmetros recebidos:")
        print(f"Hospital: {hospital}, Data início: {data_inicio}, Data fim: {data_fim}")

        # Clonar os dados originais
        dados_filtrados = data.copy()

        # Aplicar filtro de datas
        if data_inicio and data_fim:
            print("\nAplicando filtro de datas...")
            data_inicio = pd.to_datetime(data_inicio).date()
            data_fim = pd.to_datetime(data_fim).date()

            dados_filtrados = dados_filtrados[
                (dados_filtrados['data_admissao'].dt.date >= data_inicio) &
                (dados_filtrados['data_alta'].dt.date <= data_fim)
            ]

            # Verificar dados após filtro de datas
            print(f"Dados após filtro de datas: {dados_filtrados.shape[0]} registros")
            print(dados_filtrados[['data_admissao', 'data_alta']].head())

        # Aplicar filtro de hospital
        if hospital:
            print("\nAplicando filtro de hospital...")
            hospital_normalizado = normalizar_texto(hospital)
            dados_filtrados = dados_filtrados[dados_filtrados['nome_hospital_atual'] == hospital_normalizado]

            # Verificar dados após filtro de hospital
            print(f"Dados após filtro de hospital: {dados_filtrados.shape[0]} registros")
            print(dados_filtrados[['nome_hospital_atual']].head())

        # Verificar se os dados filtrados estão vazios
        if dados_filtrados.empty:
            print("\nOs dados filtrados estão vazios. Retornando gráficos vazios...")
            fig_vazio = go.Figure().update_layout(title="Sem dados para exibir")
            return [fig_vazio] * 11

        # 1. Gráfico de Procedimentos por Estabelecimento
        procedimentos = dados_filtrados['nome_hospital_atual'].value_counts().reset_index()
        procedimentos.columns = ['Hospital', 'Número de Procedimentos']
        fig1 = px.bar(procedimentos, x='Hospital', y='Número de Procedimentos', title="Procedimentos por Hospital")
        print(f"Gráfico de Procedimentos por Hospital: {procedimentos.head()}")

        # 2. Gráfico de Pacientes por Sexo
        pacientes_sexo = dados_filtrados['sexo'].value_counts().reset_index()
        pacientes_sexo.columns = ['Sexo', 'Quantidade']
        fig2 = px.pie(pacientes_sexo, names='Sexo', values='Quantidade', title="Pacientes por Sexo")
        print(f"Gráfico de Pacientes por Sexo: {pacientes_sexo.head()}")

        # 3. Gráfico de Pacientes por Faixa Etária
        faixa_etaria = dados_filtrados['faixa_etaria'].value_counts().reset_index()
        faixa_etaria.columns = ['Faixa Etária', 'Quantidade']
        fig3 = px.bar(faixa_etaria, x='Faixa Etária', y='Quantidade', title="Pacientes por Faixa Etária")
        print(f"Gráfico de Pacientes por Faixa Etária: {faixa_etaria.head()}")

        # 4. Gráfico de Tipos de Procedimentos por CID
        tipos_procedimentos = dados_filtrados['diagnostico_principal'].value_counts().reset_index()
        tipos_procedimentos.columns = ['Tipo de Procedimento', 'Quantidade']
        fig4 = px.bar(tipos_procedimentos, x='Tipo de Procedimento', y='Quantidade', title="Tipos de Procedimentos")
        print(f"Gráfico de Tipos de Procedimentos: {tipos_procedimentos.head()}")

        # 5. Procedimentos por Procedência
        procedencia = dados_filtrados['bairro'].value_counts().reset_index()
        procedencia.columns = ['Procedência', 'Quantidade']
        fig5 = px.bar(procedencia, x='Procedência', y='Quantidade', title="Procedimentos por Procedência")
        print(f"Gráfico de Procedimentos por Procedência: {procedencia.head()}")

        # 6. Óbitos por Hospital
        # obitos_hospital = dados_filtrados.groupby('nome_hospital_atual')['data_obito'].count().reset_index()
        # obitos_hospital.columns = ['Hospital', 'Óbitos']
        obitos_hospital = dados_filtrados[dados_filtrados['foi_obito']].groupby('nome_hospital_atual').size().reset_index(name='Óbitos')
        fig6 = px.bar(obitos_hospital, x='nome_hospital_atual', y='Óbitos', title="Óbitos por Hospital")

        # fig6 = px.bar(obitos_hospital, x='Hospital', y='Óbitos', title="Óbitos por Hospital")
        print(f"Gráfico de Óbitos por Hospital: {obitos_hospital.head()}")

        # 7. Total de Óbitos
        total_obitos = dados_filtrados['foi_obito'].value_counts().get(True, 0)
        fig7 = go.Figure()
        fig7.add_trace(go.Indicator(mode="number", value=total_obitos, title="Total de Óbitos"))

        # 8. Causas de Óbitos
        # causas_obitos = dados_filtrados['causa_obito'].value_counts().reset_index()
        # causas_obitos.columns = ['Causa', 'Quantidade']
        # fig8 = px.bar(causas_obitos, x='Causa', y='Quantidade', title="Causas de Óbitos")
        causas_obitos = dados_filtrados[dados_filtrados['foi_obito']]['motivo_alta'].value_counts().reset_index()
        causas_obitos.columns = ['Causa', 'Quantidade']
        fig8 = px.bar(causas_obitos, x='Causa', y='Quantidade', title="Causas de Óbitos")


        # 9. Motivos de Altas
        motivos_altas = dados_filtrados['motivo_alta'].value_counts().reset_index()
        motivos_altas.columns = ['Motivo', 'Quantidade']
        fig9 = px.bar(motivos_altas, x='Motivo', y='Quantidade', title="Motivos de Altas")

        # 10. Internações por Médico
        internacoes_medico = dados_filtrados['crm'].value_counts().reset_index()
        internacoes_medico.columns = ['CRM', 'Internações']
        fig10 = px.bar(internacoes_medico, x='CRM', y='Internações', title="Internações por Médico")

        # 11. Admissões por Período
        admissoes = dados_filtrados.groupby(dados_filtrados['data_admissao'].dt.date).size().reset_index(name='Admissões')
        fig11 = px.line(admissoes, x='data_admissao', y='Admissões', title="Admissões por Período")

        # Retornar gráficos
        return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11

    except Exception as e:
        print(f"\nErro no callback: {e}")
        fig_vazio = go.Figure().update_layout(title="Erro nos Filtros ou Dados")
        return [fig_vazio] * 11

server = app.server

# Rodar servidor
if __name__ == '__main__':
    app.run_server(debug=True)
