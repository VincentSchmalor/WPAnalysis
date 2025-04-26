# app.py

from dash import Dash, html, dash_table, dcc, Input, Output, callback_context
import dash_mantine_components as dmc
import pandas as pd
import datetime
import data.data_handler as data_handler
import plotly.express as px

df_game_plan, df_team_plans, df_team_stats, df_score_board = data_handler.get_second_league()
last_update = datetime.datetime.now()

app = Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/@mantine/core@7.17.5/styles.css"])

app.layout = dmc.MantineProvider(
    children=[
        html.Div([
            # Headline
            html.H2("Wasserball Team Dashboard"),

            # Update Button and last update info
            html.Div(
                [
                    dmc.Button("Daten aktualisieren", id="update-button", variant="light", color="blue"),
                    html.Div(
                        id="update-info",
                        children=f"Letzte Aktualisierung: {last_update.strftime('%d.%m.%Y %H:%M:%S')}",
                        style={"whiteSpace": "nowrap"}
                    )
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "gap": "10px",
                    "flexWrap": "nowrap"
                }
            ),

            # Dropdown for team selection
            html.Div(
                dcc.Dropdown(
                    id="team-dropdown",
                    options=[{"label": team, "value": team} for team in df_team_stats["Team"].sort_values()],
                    placeholder="Team auswählen"
                ),
                style={"marginTop": "15px"}
            ),

            html.Br(),

            # Scoreboard
            html.H4("Tabelle"),
            dash_table.DataTable(
                id="scoreboard",
                columns=[
                    {"name": "#", "id": "Platzierung"},
                    {"name": "Team", "id": "Team"},
                    {"name": "Punkte", "id": "Punkte"},
                    {"name": "Tore", "id": "Tore"},
                    {"name": "Tordifferenz", "id": "Tordifferenz"}
                ],
                data=df_score_board.to_dict("records"),
                style_table={"overflowX": "auto", "width": "100%"},
                style_cell={"textAlign": "center", "minWidth": "100px", "whiteSpace": "normal"}
            ),

            # Stacked Bar Chart
            html.H4("Spielausgänge pro Team"),
            dcc.Graph(id="stacked-bar-chart"),

            html.Br(),

            # Gameplan
            html.H4("Spieleübersicht"),
            dash_table.DataTable(
                id="gameplan",
                style_table={"overflowX": "auto", "width": "100%"},
                style_cell={"textAlign": "center", "minWidth": "100px", "whiteSpace": "normal"}
            )
        ], style={
            "paddingLeft": "0",
            "paddingRight": "0",
            "marginLeft": "0",
            "marginRight": "0",
            "width": "100%"
        })
    ]
)

@app.callback(
    [Output("scoreboard", "style_data_conditional"),
     Output("gameplan", "columns"),
     Output("gameplan", "data"),
     Output("gameplan", "style_data_conditional"),
     Output("stacked-bar-chart", "figure")], 
    Input("team-dropdown", "value")
)
def update_dashboard(team):
    if team:
        table_style_data = [
            {
                "if": {"filter_query": f"{{Team}} = '{team}'"},
                "backgroundColor": "#e0f3ff"
            }
        ]
    else:
        table_style_data = []
    
    if not team:
        df_game_plan_filtered = df_game_plan.copy()
        games_data = df_game_plan_filtered[["Datum_Uhrzeit", "Heim", "Gast", "Ergebnis", "Status"]].to_dict("records")
        table_format = [
            {"name": "Datum", "id": "Datum_Uhrzeit"},
            {"name": "Heim", "id": "Heim"},
            {"name": "Gast", "id": "Gast"},
            {"name": "Ergebnis", "id": "Ergebnis"},
            #{"name": "Status", "id": "Status"}
        ]
    else:
        df_team_plans_filtered = df_team_plans.get(team, pd.DataFrame())
        games_data = df_team_plans_filtered[["Datum_Uhrzeit", "Heim", "Gast", "Ergebnis", "Ergebnis_Typ", "Spielort", "Status"]].to_dict("records")
        table_format = [
            {"name": "Datum", "id": "Datum_Uhrzeit"},
            {"name": "Heim", "id": "Heim"},
            {"name": "Gast", "id": "Gast"},
            {"name": "Ergebnis", "id": "Ergebnis"},
            #{"name": "Ergebnis_Typ", "id": "Ergebnis_Typ"},
            #{"name": "Spielort", "id": "Spielort"},
            #{"name": "Status", "id": "Status"}
        ]

    game_plan_style_data = [
        {
            "if": {"filter_query": "{Ergebnis_Typ} = 'Sieg'", "column_id": "Ergebnis"},
            "backgroundColor": "#d4edda", "color": "#155724"
        },
        {
            "if": {"filter_query": "{Ergebnis_Typ} = 'Niederlage'", "column_id": "Ergebnis"},
            "backgroundColor": "#f8d7da", "color": "#721c24"
        },
        {
            "if": {"filter_query": "{Ergebnis_Typ} = 'Sieg nach 5m'", "column_id": "Ergebnis"},
            "backgroundColor": "#e6f4ea", "color": "#1b5e20"
        },
        {
            "if": {"filter_query": "{Ergebnis_Typ} = 'Niederlage nach 5m'", "column_id": "Ergebnis"},
            "backgroundColor": "#fcebea", "color": "#b71c1c"
        }
    ]

    if team:
        game_plan_style_data += [
            {
                "if": {"filter_query": f"{{Heim}} = '{team}'", "column_id": "Heim"},
                "backgroundColor": "#e0f3ff"
            },
            {
                "if": {"filter_query": f"{{Gast}} = '{team}'", "column_id": "Gast"},
                "backgroundColor": "#e0f3ff"
            }
        ]

    fig = px.bar(
        df_score_board,
        x="Team",
        y=["Siege", "Niederlagen", "Offen"],
        title="Spielausgänge pro Team",
        labels={"value": "Anzahl Spiele", "variable": "Ergebnis"},
        barmode="stack",
        text_auto="total",
        color_discrete_map={
            "Siege": "#28a745",        # Grün
            "Niederlagen": "#dc3545",  # Rot
            "Offen": "#6c757d"         # Grau
        }
    )
    fig.update_layout(
    xaxis_title=None,
    yaxis_title=None,
    legend=dict(visible=False)
    )

    return table_style_data, table_format, games_data, game_plan_style_data, fig

@app.callback(
    Output("update-info", "children"),
    [Input("update-button", "n_clicks"),
     Input("update-info", "id")]
)
def update_info(n_clicks, _):
    global df_game_plan, df_team_plans, df_team_stats, df_tabelle, last_update
    ctx = callback_context
    if not ctx.triggered:
        # Initial call, just show timestamp
        return f"Letzte Aktualisierung: {last_update.strftime('%d.%m.%Y %H:%M:%S')}"
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "update-button":
        df_game_plan, df_team_plans, df_team_stats, df_tabelle = data_handler.get_second_league()
        last_update = datetime.datetime.now()
        return f"Letzte Aktualisierung: {last_update.strftime('%d.%m.%Y %H:%M:%S')}"
    # Otherwise, just return the current timestamp
    return f"Letzte Aktualisierung: {last_update.strftime('%d.%m.%Y %H:%M:%S')}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
