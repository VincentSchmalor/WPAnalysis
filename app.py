from dash import Dash, html, dash_table, dcc, Input, Output
import dash_mantine_components as dmc
import pandas as pd
import data_loader
import data_operator

soup = data_loader.daten_laden()
df_spielplan = data_loader.spielplan_laden(soup)
df_spielplan = data_operator.spielplan_aufbereiten(df_spielplan)
teamplaene = data_operator.teamplaene_erstellen(df_spielplan)
df_teams = data_operator.teamstatistiken_erstellen(teamplaene)
df_tabelle = data_loader.tabelle_laden(soup)

app = Dash(__name__, external_stylesheets=["https://unpkg.com/@mantine/core@6.0.4/styles.css"])

app.layout = dmc.MantineProvider(
    children=[
        html.Div([
            html.H2("Wasserball Team Dashboard"),

            # Dropdown zur Teamwahl
            dcc.Dropdown(
                id="team-dropdown",
                options=[{"label": team, "value": team} for team in df_teams["Team"].sort_values()],
                placeholder="Team auswählen"
            ),

            html.Br(),

            # Tabelle
            html.H4("Tabelle"),
            dash_table.DataTable(
                id="tabelle-uebersicht",
                columns=[{"name": i, "id": i} for i in df_tabelle.columns],
                data=df_tabelle.to_dict("records"),
                style_table={"overflowX": "auto", "width": "100%"},
                style_cell={"textAlign": "center", "minWidth": "100px", "whiteSpace": "normal"}
            ),
            html.Br(),

            #Spielplan
            html.H4("Spieleübersicht"),
            dash_table.DataTable(
                id="spiele-tabelle",
                style_table={"overflowX": "auto", "width": "100%"},
                style_cell={"textAlign": "center", "minWidth": "100px", "whiteSpace": "normal"}
            )
        ])
    ]
)

@app.callback(
    [Output("tabelle-uebersicht", "style_data_conditional"),
     Output("spiele-tabelle", "columns"),
     Output("spiele-tabelle", "data"),
     Output("spiele-tabelle", "style_data_conditional")], 
    Input("team-dropdown", "value")
)
def update_dashboard(team):
    if team:
        tabelle_style_data = [
            {
                "if": {"filter_query": f"{{Team}} = '{team}'"},
                "backgroundColor": "#e0f3ff"
            }
        ]
    else:
        tabelle_style_data = []
    
    if not team:
        df_spielplan_filtered = df_spielplan.copy()
        spiele_data = df_spielplan_filtered[["Datum_Uhrzeit", "Heim", "Gast", "Ergebnis", "Status"]].to_dict("records")
        table_format = [
            {"name": "Datum", "id": "Datum_Uhrzeit"},
            {"name": "Heim", "id": "Heim"},
            {"name": "Gast", "id": "Gast"},
            {"name": "Ergebnis", "id": "Ergebnis"},
            #{"name": "Status", "id": "Status"}
        ]
        stats = None
    else:
        df_teamplaene_filtered = teamplaene.get(team, pd.DataFrame())
        spiele_data = df_teamplaene_filtered[["Datum_Uhrzeit", "Heim", "Gast", "Ergebnis", "Ergebnis_Typ", "Spielort", "Status"]].to_dict("records")
        table_format = [
            {"name": "Datum", "id": "Datum_Uhrzeit"},
            {"name": "Heim", "id": "Heim"},
            {"name": "Gast", "id": "Gast"},
            {"name": "Ergebnis", "id": "Ergebnis"},
            #{"name": "Ergebnis_Typ", "id": "Ergebnis_Typ"},
            #{"name": "Spielort", "id": "Spielort"},
            #{"name": "Status", "id": "Status"}
        ]
        stats = df_teams[df_teams["Team"] == team].iloc[0] if team in df_teams["Team"].values else None

    spielplan_style_data = [
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
        spielplan_style_data += [
            {
                "if": {"filter_query": f"{{Heim}} = '{team}'", "column_id": "Heim"},
                "backgroundColor": "#e0f3ff"
            },
            {
                "if": {"filter_query": f"{{Gast}} = '{team}'", "column_id": "Gast"},
                "backgroundColor": "#e0f3ff"
            }
        ]

    return tabelle_style_data, table_format, spiele_data, spielplan_style_data

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)