# Importar bibliotecas necessárias
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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

# Carregar o conjunto de dados
try:
    data = pd.read_csv(file_path, encoding='utf-8')
except UnicodeDecodeError:
    data = pd.read_csv(file_path, encoding='ISO-8859-1')

# Limpeza e conversão dos dados
data = data.dropna(axis=1, how='all')  # Remove colunas completamente vazias
data = data.iloc[1:]  # Remove a linha com os nomes das colunas
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

# Converter colunas de data para datetime
data['data_nascimento'] = data['data_nascimento'].apply(converter_data)
data['data_admissao'] = data['data_admissao'].apply(converter_data_hora)
data['data_alta'] = data['data_alta'].apply(converter_data_hora)
data['data_obito'] = data['data_obito'].apply(converter_data)

# Calcular a idade do paciente
data['idade'] = data.apply(lambda row: (datetime.now().date() - row['data_nascimento']).days // 365 if row['data_nascimento'] else None, axis=1)

# Criar grupos etários
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

# Layout do painel
app.layout = html.Div([
    html.H1("Painel de Gestão Hospitalar", style={'text-align': 'center'}),

    # Filtros
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
            start_date=data['data_obito'].dropna().min().strftime('%Y-%m-%d') if not data['data_obito'].dropna().empty else None,
            end_date=data['data_obito'].dropna().max().strftime('%Y-%m-%d') if not data['data_obito'].dropna().empty else None,
            display_format='YYYY-MM-DD'
        )
    ], style={'width': '40%', 'margin': 'auto'}),

    html.Hr(),

    # Gráficos
    html.Div([
        dcc.Graph(id='grafico-procedimentos'),
        dcc.Graph(id='grafico-genero'),
        dcc.Graph(id='grafico-faixa-etaria'),
        dcc.Graph(id='grafico-admissoes-altas'),
        dcc.Graph(id='grafico-mortalidade'),
        dcc.Graph(id='grafico-tipos-procedimentos'),
    ])
])

# Callbacks para comportamento interativo
@app.callback(
    [Output('grafico-procedimentos', 'figure'),
     Output('grafico-genero', 'figure'),
     Output('grafico-faixa-etaria', 'figure'),
     Output('grafico-admissoes-altas', 'figure'),
     Output('grafico-mortalidade', 'figure'),
     Output('grafico-tipos-procedimentos', 'figure')],
    [Input('filtro-hospital', 'value'),
     Input('intervalo-datas', 'start_date'),
     Input('intervalo-datas', 'end_date')]
)
def atualizar_graficos(hospital, data_inicio, data_fim):
    try:
        # Filtrar os dados
        dados_filtrados = data.copy()

        if data_inicio and data_fim:
            dados_filtrados = dados_filtrados[
                (dados_filtrados['data_obito'].dt.date >= pd.to_datetime(data_inicio).date()) &
                (dados_filtrados['data_obito'].dt.date <= pd.to_datetime(data_fim).date())
            ]

        if hospital:
            dados_filtrados = dados_filtrados[dados_filtrados['nome_hospital_atual'] == hospital]

        # Gráfico 1: Procedimentos por Hospital
        procedimentos = dados_filtrados['nome_hospital_atual'].value_counts().reset_index()
        procedimentos.columns = ['Hospital', 'Número de Procedimentos']
        fig1 = px.bar(procedimentos, x='Hospital', y='Número de Procedimentos', title="Procedimentos por Hospital")

        # Gráfico 2: Pacientes por Gênero
        genero = dados_filtrados['grupo_sanguineo'].value_counts().reset_index()
        genero.columns = ['Gênero', 'Quantidade']
        fig2 = px.pie(genero, names='Gênero', values='Quantidade', title="Pacientes por Gênero")

        # Gráfico 3: Pacientes por Faixa Etária
        faixa_etaria = dados_filtrados['faixa_etaria'].value_counts().reset_index()
        faixa_etaria.columns = ['Faixa Etária', 'Quantidade']
        fig3 = px.bar(faixa_etaria, x='Faixa Etária', y='Quantidade', title="Pacientes por Faixa Etária")

        # Gráfico 4: Admissões e Altas
        admissoes = dados_filtrados.groupby(dados_filtrados['data_admissao'].dt.date).size().reset_index(name='Admissões')
        altas = dados_filtrados.groupby(dados_filtrados['data_alta'].dt.date).size().reset_index(name='Altas')
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=admissoes['data_admissao'], y=admissoes['Admissões'], mode='lines+markers', name='Admissões'))
        fig4.add_trace(go.Scatter(x=altas['data_alta'], y=altas['Altas'], mode='lines+markers', name='Altas'))
        fig4.update_layout(title="Admissões e Altas por Período", xaxis_title="Data", yaxis_title="Quantidade")

        # Gráfico 5: Taxa de Mortalidade
        mortalidade = dados_filtrados.groupby('nome_hospital_atual')['data_obito'].count().reset_index(name='Óbitos')
        fig5 = px.bar(mortalidade, x='nome_hospital_atual', y='Óbitos', title="Taxa de Mortalidade por Hospital")

        # Gráfico 6: Tipos de Procedimentos
        tipos_procedimentos = dados_filtrados['diagnostico_principal'].value_counts().reset_index()
        tipos_procedimentos.columns = ['Tipo de Procedimento', 'Quantidade']
        fig6 = px.bar(tipos_procedimentos, x='Tipo de Procedimento', y='Quantidade', title="Tipos de Procedimentos")

        return fig1, fig2, fig3, fig4, fig5, fig6
    except Exception as e:
        print(f"Erro: {e}")
        fig_vazia = go.Figure().update_layout(title="Erro. Verifique os filtros ou os dados.")
        return fig_vazia, fig_vazia, fig_vazia, fig_vazia, fig_vazia, fig_vazia


server = app.server


# Executar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
