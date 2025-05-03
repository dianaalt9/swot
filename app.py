import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import re

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

color_palette = ['blue', 'green', 'red', 'orange', 'purple']

app.layout = html.Div([
    html.H2("Инвестиционный симулятор недвижимости", className="text-center my-4 text-white"),

    dcc.Store(id='scenario_ids', data=[]),

    html.Div([
        dbc.Button("Добавить сценарий", id="add_scenario", n_clicks=0, color="primary"),
    ], className="d-flex justify-content-center mb-3"),

    dbc.Row(id="scenario_container", className="gy-4"),

    html.Div([
        dbc.Button("Построить график", id="build_graph", n_clicks=0, color="success", className="mb-4")
    ], className="d-flex justify-content-center"),

    html.Div([
        dcc.Graph(id='profit_graph'),
        dcc.Graph(id='annual_bar_graph'),
        html.Div(id='sale_results', className="text-center fw-bold fs-5 my-3")
    ], className="p-3 bg-light rounded shadow"),

], style={"backgroundColor": "#1e1e2f", "minHeight": "100vh", "padding": "20px"})

# Шаблон карточки сценария

def scenario_block(scenario_id):
    color = color_palette[(int(scenario_id)-1) % len(color_palette)]
    return dbc.Col([
        dbc.Card([
            dbc.CardHeader(html.Span([
                html.Span("● ", style={"color": color, "fontSize": "1.2em"}),
                f"Сценарий {scenario_id}"
            ])),
            dbc.CardBody([
                dbc.Label("Название сценария"),
                dbc.Input(id={'type': 'name', 'index': scenario_id}, value=f"Сценарий {scenario_id}"),

                dbc.Label("Начальная аренда (₽/м²/год)"),
                dbc.Input(id={'type': 'initial_rent', 'index': scenario_id}, type="number", value=12000),

                dbc.Label("Строительство (₽/м²)"),
                dbc.Input(id={'type': 'construction_cost', 'index': scenario_id}, type="number", value=80000),

                dbc.Label("Площадь здания (м²)"),
                dbc.Input(id={'type': 'total_area', 'index': scenario_id}, type="number", value=1000),

                dbc.Label("Сдаваемый %"),
                dbc.Input(id={'type': 'rentable_percent', 'index': scenario_id}, type="number", value=80),

                dbc.Label("Затраты (₽/год) за м²"),
                dbc.Input(id={'type': 'annual_expenses', 'index': scenario_id}, type="number", value=100),

                dbc.Label("Рост аренды по годам (%) через запятую"),
                dbc.Input(id={'type': 'growth_list', 'index': scenario_id}, value="5,5,4,4,3,3,2,2,1,1"),

                dbc.Label("Цена продажи (₽/м²)"),
                dbc.Input(id={'type': 'sale_price_per_m2', 'index': scenario_id}, type="number", value=100000),

                dbc.Label("Год продажи (например: 10)"),
                dbc.Input(id={'type': 'sale_year', 'index': scenario_id}, type="number", value=10),
            ])
        ], className="h-100 bg-light rounded shadow")
    ], width=6)

# Callback: динамическое добавление сценариев
@app.callback(
    Output("scenario_container", "children"),
    Output("scenario_ids", "data"),
    Input("add_scenario", "n_clicks"),
    State("scenario_ids", "data")
)
def update_scenarios(n_clicks, existing_ids):
    if n_clicks is None:
        return dash.no_update

    if len(existing_ids) >= 5:
        return [scenario_block(i) for i in existing_ids], existing_ids

    new_id = str(len(existing_ids) + 1)
    updated_ids = existing_ids + [new_id]
    blocks = [scenario_block(i) for i in updated_ids]
    return blocks, updated_ids

@app.callback(
    Output('profit_graph', 'figure'),
    Output('annual_bar_graph', 'figure'),
    Output('sale_results', 'children'),
    Input('build_graph', 'n_clicks'),
    State({'type': 'name', 'index': dash.ALL}, 'value'),
    State({'type': 'initial_rent', 'index': dash.ALL}, 'value'),
    State({'type': 'construction_cost', 'index': dash.ALL}, 'value'),
    State({'type': 'total_area', 'index': dash.ALL}, 'value'),
    State({'type': 'rentable_percent', 'index': dash.ALL}, 'value'),
    State({'type': 'annual_expenses', 'index': dash.ALL}, 'value'),
    State({'type': 'growth_list', 'index': dash.ALL}, 'value'),
    State({'type': 'sale_price_per_m2', 'index': dash.ALL}, 'value'),
    State({'type': 'sale_year', 'index': dash.ALL}, 'value')
)
def build_charts(n_clicks, names, rents, costs, areas, percents, expenses, growths, sale_prices, sale_years):
    profit_fig = go.Figure()
    bar_fig = go.Figure()
    result_texts = []

    for i in range(len(names)):
        try:
            growth_list = [float(g.strip()) / 100 for g in re.split(r'[;,\s]+', growths[i]) if g.strip()]
        except:
            growth_list = [0.03] * 10

        years = len(growth_list)
        rent = rents[i]
        total = -costs[i] * areas[i]
        cumulative = []
        annual = []

        for y in range(years):
            rent *= (1 + growth_list[y])
            income = rent * areas[i] * (percents[i] / 100)
            profit = income - expenses[i] * areas[i]
            total += profit
            cumulative.append(total)
            annual.append(profit)

        sale_year = sale_years[i] if 1 <= sale_years[i] <= years else years
        sale_total = cumulative[sale_year - 1] + (sale_prices[i] * areas[i])

        color = color_palette[i % len(color_palette)]

        profit_fig.add_trace(go.Scatter(
            x=list(range(1, years + 1)),
            y=cumulative,
            mode='lines+markers',
            name=names[i],
            line=dict(color=color)
        ))

        bar_fig.add_trace(go.Bar(
            x=list(range(1, years + 1)),
            y=annual,
            name=names[i],
            marker=dict(color=color)
        ))

        result_texts.append(f"{names[i]} → Продажа в {sale_year} год: {sale_total:,.0f} ₽")

    profit_fig.add_hline(y=0, line_dash="dot", line_color="black", line_width=2)
    profit_fig.update_layout(
        title={"text": "<b>Накопленная прибыль по сценариям</b>", "x": 0.5},
        xaxis_title="Год",
        yaxis_title="₽",
        xaxis=dict(showgrid=True, dtick=1),
        yaxis=dict(showgrid=True, zeroline=True, zerolinewidth=2, zerolinecolor='black')
    )
    bar_fig.update_layout(
        title={"text": "<b>Годовая прибыль по сценариям</b>", "x": 0.5},
        xaxis_title="Год",
        yaxis_title="₽",
        barmode='group',
        xaxis=dict(showgrid=True, dtick=1),
        yaxis=dict(showgrid=True)
    )

    return profit_fig, bar_fig, html.Ul([html.Li(txt) for txt in result_texts])

if __name__ == '__main__':
    app.run(debug=True)
    
server = app.server
