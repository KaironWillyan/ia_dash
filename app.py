import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

file_path = './dataset/dados_tratados.csv'

data = pd.read_csv(file_path)

# Inicializar o Dash com tema Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard de Gestão Hospitalar - BI"

# Carregar o dataset tratado
# data = pd.read_csv("2024-12-30T16-29_export.csv")  # Atualize o caminho do dataset
data['data_admissao'] = pd.to_datetime(data['data_admissao'])
data['data_alta'] = pd.to_datetime(data['data_alta'])
data['data_obito'] = pd.to_datetime(data['data_obito'])
data['duracao_internacao'] = (data['data_alta'] - data['data_admissao']).dt.days.fillna(0)

# Layout do Dashboard
app.layout = html.Div([
    html.H1("Dashboard de Gestão Hospitalar - BI", style={'text-align': 'center', 'margin-bottom': '20px'}),
    html.P((f'Quantidade de documentos analisados: ', len(data)), style={'text-align': 'center','margin-bottom': '20px'}),

    # Filtros
    html.Div([
        html.Div([
            html.Label("Selecione o Hospital:"),
            dcc.Dropdown(
                id="filtro-hospital",
                options=[{'label': hospital, 'value': hospital} for hospital in data['nome_hospital_atual'].unique()],
                placeholder="Todos os hospitais",
                multi=False
            )
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Selecione o Procedimento:"),
            dcc.Dropdown(
                id="filtro-procedimento",
                options=[{'label': procedimento, 'value': procedimento} for procedimento in data['procedimentos_realizados'].dropna().unique()],
                placeholder="Todos os procedimentos",
                multi=False
            )
        ], style={'width': '48%', 'display': 'inline-block', 'margin-left': '4%'}),

        html.Div([
            html.Label("Selecione o Intervalo de Datas:"),
            dcc.DatePickerRange(
                id="intervalo-datas",
                start_date=data['data_admissao'].min(),
                end_date=data['data_alta'].max(),
                display_format='YYYY-MM-DD'
            )
        ], style={'width': '48%', 'display': 'inline-block', 'margin-top': '20px'})
    ], style={'margin-bottom': '30px'}),

    html.Hr(),

    # Organização dos gráficos
    html.Div([
        html.Div([
            dcc.Graph(id=f'grafico-{i}', config={'displayModeBar': False})
            for i in range(1, 16)  # IDs para 15 gráficos
        ], style={
            'display': 'grid',
            'grid-template-columns': 'repeat(auto-fit, minmax(300px, 1fr))',
            'gap': '20px'
        })
    ]),

    # Modal para gráficos expandidos
    dbc.Modal(
        [
            dbc.ModalHeader("Gráfico Expandido"),
            dbc.ModalBody(dcc.Graph(id="grafico-expandido", config={'displayModeBar': True})),
            dbc.ModalFooter(
                dbc.Button("Fechar", id="fechar-modal", className="ml-auto", n_clicks=0)
            ),
        ],
        id="modal-grafico",
        size="xl",  # Tamanho do modal: 'sm', 'lg', ou 'xl'
        is_open=False
    )
], style={'font-family': 'Arial, sans-serif', 'padding': '20px'})

# Callback para atualizar os gráficos e abrir o modal
@app.callback(
    [Output(f'grafico-{i}', 'figure') for i in range(1, 16)] +
    [Output("modal-grafico", "is_open"),
     Output("grafico-expandido", "figure")],
    [Input('filtro-hospital', 'value'),
     Input('filtro-procedimento', 'value'),
     Input('intervalo-datas', 'start_date'),
     Input('intervalo-datas', 'end_date')] +
    [Input(f'grafico-{i}', 'clickData') for i in range(1, 16)] +
    [Input("fechar-modal", "n_clicks")]
)
def atualizar_e_expandir(hospital, procedimento, data_inicio, data_fim, *args):
    dados_filtrados = data.copy()
    ctx = dash.callback_context

    # Filtros
    if data_inicio and data_fim:
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)
        dados_filtrados = dados_filtrados[
            (dados_filtrados['data_admissao'] >= data_inicio) &
            (dados_filtrados['data_alta'] <= data_fim)
        ]

    if hospital:
        dados_filtrados = dados_filtrados[dados_filtrados['nome_hospital_atual'] == hospital]

    if procedimento:
        dados_filtrados = dados_filtrados[dados_filtrados['procedimentos_realizados'] == procedimento]

    if dados_filtrados.empty:
        vazio_figura = px.bar(title="Nenhum dado disponível")
        return [vazio_figura] * 15 + [False, vazio_figura]

    # Criar os gráficos
    graficos = [
        px.bar(dados_filtrados, x='nome_hospital_atual', y='procedimentos_realizados', title="Procedimentos por Hospital"),
        px.pie(dados_filtrados, names='sexo', title="Pacientes por Sexo"),
        px.bar(dados_filtrados, x='faixa_etaria', y='duracao_internacao', title="Faixa Etária"),
        px.bar(dados_filtrados, x='nome_hospital_atual', y='foi_obito', title="Óbitos por Hospital"),
        px.bar(dados_filtrados, x='motivo_alta', y='duracao_internacao', title="Causas de Altas Hospitalares"),
        px.line(dados_filtrados, x='data_admissao', y='procedimentos_realizados', title="Admissões por Data"),
        px.pie(dados_filtrados, names='bairro', title="Admissões por Bairro"),
        px.scatter(dados_filtrados, x='idade', y='duracao_internacao', title="Correlação: Idade vs. Duração"),
        px.density_heatmap(dados_filtrados, x='data_admissao', y='nome_hospital_atual', title="Mapa de Calor"),
        px.pie(dados_filtrados, names='cor_classificacao_risco', title="Classificação de Risco"),
        px.bar(dados_filtrados, x='data_admissao', y='duracao_internacao', title="Taxa de Ocupação Diária"),
        px.bar(dados_filtrados, x='bairro', y='procedimentos_realizados', title="Admissões por Bairro"),
        px.pie(dados_filtrados, names='sexo', title="Distribuição de Sexo"),
        px.bar(dados_filtrados, x='data_admissao', y='duracao_internacao', title="Duração Média de Internações"),
        px.bar(dados_filtrados, x='data_alta', y='procedimentos_realizados', title="Altas Hospitalares")
    ]

    # Expandir gráfico clicado
    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if "grafico" in trigger_id:
            grafico_index = int(trigger_id.split('-')[1]) - 1
            return graficos + [True, graficos[grafico_index]]

    return graficos + [False, graficos[0]]

server = app.server

# Executar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
