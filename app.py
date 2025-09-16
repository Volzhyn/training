from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import os

# ==================== СОЗДАЕМ ДАННЫЕ ====================
def create_data():
    main_data = {
        'Cohort': ['2024-05', '2024-06', '2024-07'],
        'UA': [9810, 14547, 17094],
        'C1': [2.01, 1.38, 0.87],
        'B': [197, 201, 149],
        'AOV': [10.0, 10.0, 10.0],
        'COGS': [1.3, 1.3, 1.3],
        'T': [328, 268, 149],
        'APC': [1.66, 1.33, 1.00],
        'CLTV': [14.49, 11.60, 8.70],
        'LTV': [0.29, 0.16, 0.08],
        'LTC': [11.55, 8.12, 5.26],
        'AC': [113352, 118106, 89907],
        'CM': [-110498.4, -115774.4, -88610.7],
        'Revenue': [3280, 2680, 1490],
        'Retention_Rate': [51.27, 33.33, 0.00]
    }
    
    repeat_data = {
        'Cohort': ['2024-05', '2024-06', '2024-07'],
        'UA': [9810, 14547, 17094],
        'C1': ['1.03%', '0.46%', '0.0%'],
        'B': [101, 67, 0],
        'AOV': [10.0, 10.0, 0.0],
        'COGS': [1.3, 1.3, 0.0],
        'T': [232, 134, 0],
        'APC': [2.3, 2.0, 0.0],
        'CLTV': [19.98, 17.40, 0.00],
        'LTV': [0.21, 0.08, 0.00],
        'LTC/CPA': [0.12, 0.06, 0.00],
        'AC': [1224, 802, 0],
        'CM': [794.4, 363.8, 0.0],
        'Revenue': [2320, 1340, 0]
    }
    
    return pd.DataFrame(main_data), pd.DataFrame(repeat_data)

main_table, repeat_table = create_data()

# ==================== ФОРМУЛЫ ====================
main_formulas = [
    "UA = COUNTUNIQUE(uuid) - Уникальные пользователи",
    "B = COUNTUNIQUE(buyer) - Уникальные покупатели",
    "C1 = B / UA × 100% - Конверсия в покупателей",
    "Retention_Rate = (Повторные покупатели) / B × 100% - Доля возвращающихся",
    "T = COUNT транзакций - Общее количество покупок",
    "Revenue = SUM(aov) - Общая выручка",
    "Total_COGS = SUM(cogs) - Общая себестоимость",
    "COGS_per_transaction = Total_COGS / T - Себестоимость на транзакцию",
    "AOV = Revenue / T - Средний чек",
    "APC = T / B - Среднее количество покупок на клиента",
    "AC = SUM(ltc WHERE ltc > 0) - Общие затраты на привлечение",
    "LTC = AC / UA - Затраты на привлечение одного пользователя",
    "CPA = AC / B - Cost Per Acquisition (на покупателя)",
    "CLTV = (AOV - COGS_per_transaction) × APC - Валовая прибыль с клиента",
    "LTV = CLTV × C1 - Ценность пользователя с учетом конверсии",
    "CM = UA × (CLTV × C1 - LTC) - Маржинальная прибыль когорты",
    "Gross_Margin_% = (Revenue - Total_COGS) / Revenue × 100% - Валовая маржа"
]

repeat_formulas = [
    "UA = COUNTUNIQUE(uuid) - Уникальные пользователи всей когорты",
    "B = COUNTUNIQUE(buyer WHERE payment_count > 1) - Покупатели с 2+ покупками",
    "C1 = B / UA × 100% - Конверсия в повторных покупателей",
    "T = COUNT(aov > 0 WHERE buyer IN repeat_buyers) - Транзакции от повторных",
    "Revenue = SUM(aov WHERE buyer IN repeat_buyers) - Выручка от сегмента 2+",
    "Total_COGS = SUM(cogs WHERE buyer IN repeat_buyers) - Себестоимость сегмента 2+",
    "COGS_per_transaction = Total_COGS / T - Средняя себестоимость транзакции",
    "AOV = Revenue / T - Средний чек сегмента 2+",
    "APC = T / B - Среднее количество покупок на клиента 2+",
    "AC_repeat = SUM(ltc WHERE buyer IN repeat_buyers AND ltc > 0) - Затраты на сегмент 2+",
    "LTC/CPA = AC_repeat / UA - Затраты на сегмент 2+ в расчёте на одного пользователя когорты",
    "CLTV = (AOV - COGS_per_transaction) × APC - Ценность повторного клиента",
    "LTV = CLTV × C1 - Ценность пользователя для сегмента 2+",
    "CM = Revenue - Total_COGS - AC_repeat - Прибыль от сегмента 2+"
]

# ==================== DASH ПРИЛОЖЕНИЕ ====================
app = Dash(__name__)
server = app.server   # 🔑 Render подхватывает Flask сервер

app.layout = html.Div([
    html.H1("📊 Анализ юнит-экономики по когортам", 
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px'}),
    
    html.Div([
        dcc.RadioItems(
            id='table-selector',
            options=[
                {'label': '📋 Основная таблица', 'value': 'main'},
                {'label': '🔄 Повторные покупатели', 'value': 'repeat'}
            ],
            value='main',
            labelStyle={'display': 'inline-block', 'margin': '10px'}
        )
    ], style={'textAlign': 'center', 'margin': '20px'}),
    
    html.Div(id='table-container'),
    
    html.H2("📘 Основные формулы юнит-экономики", style={'marginTop': '40px'}),
    html.Ul([html.Li(f) for f in main_formulas], style={'marginBottom': '40px'}),
    
    html.H2("📘 Формулы для сегмента покупателей с 1+ покупками"),
    html.Ul([html.Li(f) for f in repeat_formulas])
])

@callback(
    Output('table-container', 'children'),
    Input('table-selector', 'value')
)
def update_table(selected_table):
    if selected_table == 'main':
        current_table = main_table
        title = "ЮНИТ-ЭКОНОМИКА ДЛЯ КЛИЕНТОВ ПО КОГОРТАМ ПРИВЛЕЧЕНИЯ"
    else:
        current_table = repeat_table
        title = "ЮНИТ-ЭКОНОМИКА ДЛЯ СЕГМЕНТА ПОКУПАТЕЛЕЙ С >1 ПОКУПКАМИ"
    
    # Стили для таблицы
    table_style = {
        'width': '100%',
        'borderCollapse': 'collapse',
        'margin': '20px auto'
    }
    cell_style = {
        'border': '1px solid black',
        'padding': '6px',
        'textAlign': 'center'
    }
    
    table = html.Table([
        html.Thead(
            html.Tr([html.Th(col, style=cell_style) for col in current_table.columns])
        ),
        html.Tbody([
            html.Tr([html.Td(current_table.iloc[i][col], style=cell_style) for col in current_table.columns])
            for i in range(len(current_table))
        ])
    ], style=table_style)
    
    return html.Div([
        html.H3(title, style={'textAlign': 'center', 'marginTop': '20px'}),
        table
    ])

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Render передаст порт
    app.run(host="0.0.0.0", port=port, debug=False)
