# data_operator.py

import pandas as pd
import numpy as np
import re

def clean_text(df):
    # Apply cleaning functions to all string columns
    def clean_cell(x):
        if not isinstance(x, str):
            return x
        return (
            x.strip() # Whitespace
             .replace("\u00a0", " ") # Non-breaking space
             .replace("\n", " ") #Line breaks
        )
    df = df.map(clean_cell)

    return df

def split_quarters(df):
    quarters_list = df["Viertel"].apply(lambda x: re.findall(r"(\d+):(\d+)", x))
    for i in range(5):
        df[f"Q{i+1}_Heim"] = quarters_list.apply(lambda x: int(x[i][0]) if len(x) > i else np.nan)
        df[f"Q{i+1}_Gast"] = quarters_list.apply(lambda x: int(x[i][1]) if len(x) > i else np.nan)

    return df

def split_score(df):
    # Remove unwanted characters
    df["Ergebnis"] = df["Ergebnis"].str.replace(" n.EW", "", regex=False)
    # Extract the score using regex
    goals = df["Ergebnis"].str.extract(r"(?P<Heim_Tore>\d+)\s*[:]\s*(?P<Gast_Tore>\d+)")
    df["Heim_Tore"] = pd.to_numeric(goals["Heim_Tore"], errors="coerce")
    df["Gast_Tore"] = pd.to_numeric(goals["Gast_Tore"], errors="coerce")

    return df

def split_date_time(df):
    # Split "Datum & Uhrzeit" column into separate columns
    df[["Datum_str", "Uhrzeit_str"]] = df["Datum & Uhrzeit"].str.split(",", n=1, expand=True)
    # Clean strings
    df["Datum_str"] = df["Datum_str"].str.strip()
    df["Uhrzeit_str"] = df["Uhrzeit_str"].str.strip().str.replace(" uhr", "", case=False)
    # Convert to datetime
    df["Datum"] = pd.to_datetime(df["Datum_str"], format="%d.%m.%y", errors="coerce")
    df["Uhrzeit"] = pd.to_datetime(df["Uhrzeit_str"], format="%H:%M", errors="coerce").dt.time
    def combine_date_time(row):
        if pd.notnull(row["Datum"]) and pd.notnull(row["Uhrzeit"]):
            return pd.to_datetime(f"{row['Datum']} {row['Uhrzeit']}")
        else:
            return pd.NaT
    # Combine date and time into a single column
    df["Datum_Uhrzeit"] = df.apply(combine_date_time, axis=1)
    df["Datum_Uhrzeit"] = pd.to_datetime(df["Datum_Uhrzeit"], errors="coerce").dt.strftime("%d.%m.%Y, %H:%M")
    
    return df

def add_weekday(df):
    df["Wochentag"] = None
    df["Wochenende"] = None
    df["Spieltagstyp"] = None
    
    if "Datum" in df.columns:
        valid_dates = df["Datum"].notna()

        # Add weekday information
        df.loc[valid_dates, "Wochentag"] = df.loc[valid_dates, "Datum"].dt.day_name()
        df.loc[valid_dates, "Wochenende"] = df.loc[valid_dates, "Datum"].dt.weekday >= 5
        df.loc[valid_dates, "Spieltagstyp"] = df.loc[valid_dates, "Wochenende"].apply(
            lambda x: "Wochenende" if x else "Wochentag"
        )

    return df

def add_game_status(df):
    df["Status"] = df["Ergebnis"].apply(lambda x: "Gespielt" if ":" in str(x) else "Offen")

    return df

# Function to extend the game plan with additional information
def extend_game_plan(df):
    df = clean_text(df)
    df = split_quarters(df)
    df = split_score(df)
    df = split_date_time(df)
    df = add_weekday(df)
    df = add_game_status(df)

    return df

def add_game_location(games, team):
    games["Heimspiel"] = games["Heim"] == team
    games["Auswaertsspiel"] = games["Gast"] == team
    games["Spielort"] = games.apply(
        lambda row: "Heim" if row["Heim"] == team else ("Auswärts" if row["Gast"] == team else None), axis=1)
    
    return games

def add_goals(games, team):
    games["Eigene_Tore"] = games.apply(
        lambda row: row["Heim_Tore"] if row["Heim"] == team else row["Gast_Tore"], axis=1)
    games["Gegentore"] = games.apply(
        lambda row: row["Gast_Tore"] if row["Heim"] == team else row["Heim_Tore"], axis=1)
    
    return games

def add_quarter_goals(games, team):
    for i in range(1, 5):
        q = f"Q{i}"
        games[f"{q}_Eigene"] = games.apply(
            lambda row: row[f"{q}_Heim"] if row["Heim"] == team else row[f"{q}_Gast"], axis=1)
        games[f"{q}_Gast"] = games.apply(
            lambda row: row[f"{q}_Gast"] if row["Gast"] == team else row[f"{q}_Heim"], axis=1)
        
    return games

def add_result_type(games):
    def ergebnis_typ(row):
        if pd.isna(row["Eigene_Tore"]) or pd.isna(row["Gegentore"]):
            return "Offen"
        
        # Check if game ended in a draw
        hat_q5 = not pd.isna(row.get("Q5_Heim", np.nan)) or not pd.isna(row.get("Q5_Gast", np.nan))

        if row["Eigene_Tore"] > row["Gegentore"]:
            return "Sieg nach 5m" if hat_q5 else "Sieg"
        elif row["Eigene_Tore"] < row["Gegentore"]:
            return "Niederlage nach 5m" if hat_q5 else "Niederlage"
        else:
            return "Offen"
            
    games["Ergebnis_Typ"] = games.apply(ergebnis_typ, axis=1)

    return games

# Function to create game plans filtered by team
def create_team_plans(df):
    teams = pd.unique(df[["Heim", "Gast"]].values.ravel())
    team_plans = {}

    for team in teams:
        games = df[(df["Heim"] == team) | (df["Gast"] == team)].copy()

        games = add_game_location(games, team)
        games = add_goals(games, team)
        games = add_quarter_goals(games, team)
        games = add_result_type(games)
        team_plans[team] = games

    return team_plans

# Function to create team statistics
def create_team_stats(df_team_plans):
    stats_list = []

    for team, games in df_team_plans.items():
        stats = {
            "Team": team,
            "Spiele_gesamt": len(games),
            "Gespielt": (games["Status"] == "Gespielt").sum(),
            "Offen": (games["Status"] == "Offen").sum(),
            "Tore_ges": games["Eigene_Tore"].sum(),
            "Gegentore_ges": games["Gegentore"].sum(),
            "Ø Tore": round(games["Eigene_Tore"].mean(), 2),
            "Ø Gegentore": round(games["Gegentore"].mean(), 2),
            "Tordifferenz": games["Eigene_Tore"].sum() - games["Gegentore"].sum(),
            "Q1_Tordifferenz": games["Q1_Eigene"].sum() - games["Q1_Gast"].sum(),
            "Q2_Tordifferenz": games["Q2_Eigene"].sum() - games["Q2_Gast"].sum(),
            "Q3_Tordifferenz": games["Q3_Eigene"].sum() - games["Q3_Gast"].sum(),
            "Q4_Tordifferenz": games["Q4_Eigene"].sum() - games["Q4_Gast"].sum(),
            "Siege": (games["Ergebnis_Typ"] == "Sieg").sum(),
            "Unentschieden": (games["Ergebnis_Typ"] == "Unentschieden").sum(),
            "Niederlagen": (games["Ergebnis_Typ"] == "Niederlage").sum()
        }

        stats_list.append(stats)

    return pd.DataFrame(stats_list)