import pandas as pd
import numpy as np
import re

def spielplan_aufbereiten(df):
    #Texte bereinigen
    def clean_cell(x):
        if not isinstance(x, str):
            return x
        return (
            x.strip()                              # Leerzeichen vorn/hinten
             .replace("\u00a0", " ")                # geschütztes Leerzeichen
             .replace("\n", " ")                    # Zeilenumbrüche entfernen
        )
    df = df.applymap(clean_cell)

    #Viertelergebnisse splitten
    viertel_liste = df["Viertel"].apply(lambda x: re.findall(r"(\d+):(\d+)", x))
    for i in range(5):
        df[f"Q{i+1}_Heim"] = viertel_liste.apply(lambda x: int(x[i][0]) if len(x) > i else np.nan)
        df[f"Q{i+1}_Gast"] = viertel_liste.apply(lambda x: int(x[i][1]) if len(x) > i else np.nan)

    #Ergebnis in Heim und Gast teilen
    df["Ergebnis"] = df["Ergebnis"].str.replace(" n.EW", "", regex=False)
    tore = df["Ergebnis"].str.extract(r"(?P<Heim_Tore>\d+)\s*[:]\s*(?P<Gast_Tore>\d+)")
    df["Heim_Tore"] = pd.to_numeric(tore["Heim_Tore"], errors="coerce")
    df["Gast_Tore"] = pd.to_numeric(tore["Gast_Tore"], errors="coerce")

    #Fünf Meterschießen bestimmen

    
    #Datum teilen
    df[["Datum_str", "Uhrzeit_str"]] = df["Datum & Uhrzeit"].str.split(",", n=1, expand=True)
    df["Datum_str"] = df["Datum_str"].str.strip()
    df["Uhrzeit_str"] = df["Uhrzeit_str"].str.strip().str.replace(" uhr", "", case=False)
    df["Datum"] = pd.to_datetime(df["Datum_str"], format="%d.%m.%y", errors="coerce")
    df["Uhrzeit"] = pd.to_datetime(df["Uhrzeit_str"], format="%H:%M", errors="coerce").dt.time
    def combine_date_time(row):
        if pd.notnull(row["Datum"]) and pd.notnull(row["Uhrzeit"]):
            return pd.to_datetime(f"{row['Datum']} {row['Uhrzeit']}")
        else:
            return pd.NaT
    df["Datum_Uhrzeit"] = df.apply(combine_date_time, axis=1)
    df["Datum_Uhrzeit"] = pd.to_datetime(df["Datum_Uhrzeit"], errors="coerce").dt.strftime("%d.%m.%Y, %H:%M")
    
    #Weitere Datumsfelder berechnen
    df["Wochentag"] = None
    df["Wochenende"] = None
    df["Spieltagstyp"] = None

    if "Datum" in df.columns:
        valid_dates = df["Datum"].notna()

        df.loc[valid_dates, "Wochentag"] = df.loc[valid_dates, "Datum"].dt.day_name()
        df.loc[valid_dates, "Wochenende"] = df.loc[valid_dates, "Datum"].dt.weekday >= 5
        df.loc[valid_dates, "Spieltagstyp"] = df.loc[valid_dates, "Wochenende"].apply(
            lambda x: "Wochenende" if x else "Wochentag"
        )

    #Spielstatus bestimmen
    df["Status"] = df["Ergebnis"].apply(lambda x: "Gespielt" if ":" in str(x) else "Offen")
    return df

def teamplaene_erstellen(df):
    teams = pd.unique(df[["Heim", "Gast"]].values.ravel())
    teamplaene = {}

    for team in teams:
        spiele = df[(df["Heim"] == team) | (df["Gast"] == team)].copy()

        spiele["Heimspiel"] = spiele["Heim"] == team
        spiele["Auswaertsspiel"] = spiele["Gast"] == team

        spiele["Spielort"] = spiele.apply(lambda row: "Heim" if row["Heim"] == team else ("Auswärts" if row["Gast"] == team else None), axis=1)

        spiele["Eigene_Tore"] = spiele.apply(
            lambda row: row["Heim_Tore"] if row["Heim"] == team else row["Gast_Tore"], axis=1)
        spiele["Gegentore"] = spiele.apply(
            lambda row: row["Gast_Tore"] if row["Heim"] == team else row["Heim_Tore"], axis=1)
        
        # Eigene Vierteltore berechnen
        for i in range(1, 5):
            q = f"Q{i}"
            spiele[f"{q}_Eigene"] = spiele.apply(
                lambda row: row[f"{q}_Heim"] if row["Heim"] == team else row[f"{q}_Gast"], axis=1)
            
        for i in range(1, 5):
            q = f"Q{i}"
            spiele[f"{q}_Gast"] = spiele.apply(
                lambda row: row[f"{q}_Gast"] if row["Gast"] == team else row[f"{q}_Heim"], axis=1)

        def ergebnis_typ(row):
            if pd.isna(row["Eigene_Tore"]) or pd.isna(row["Gegentore"]):
                return "Offen"
            
            # Prüfe, ob 5-Meter-Schießen vorliegt
            hat_q5 = not pd.isna(row.get("Q5_Heim", np.nan)) or not pd.isna(row.get("Q5_Gast", np.nan))

            if row["Eigene_Tore"] > row["Gegentore"]:
                return "Sieg nach 5m" if hat_q5 else "Sieg"
            elif row["Eigene_Tore"] < row["Gegentore"]:
                return "Niederlage nach 5m" if hat_q5 else "Niederlage"
            else:
                return "Offen"
                
        spiele["Ergebnis_Typ"] = spiele.apply(ergebnis_typ, axis=1)


        teamplaene[team] = spiele

    return teamplaene

def teamstatistiken_erstellen(teamplaene):
    stats_liste = []

    for team, spiele in teamplaene.items():
        stats = {
            "Team": team,
            "Spiele_gesamt": len(spiele),
            "Gespielt": (spiele["Status"] == "Gespielt").sum(),
            "Offen": (spiele["Status"] == "Offen").sum(),
            "Tore_ges": spiele["Eigene_Tore"].sum(),
            "Gegentore_ges": spiele["Gegentore"].sum(),
            "Ø Tore": round(spiele["Eigene_Tore"].mean(), 2),
            "Ø Gegentore": round(spiele["Gegentore"].mean(), 2),
            "Tordifferenz": spiele["Eigene_Tore"].sum() - spiele["Gegentore"].sum(),
            "Q1_Tordifferenz": spiele["Q1_Eigene"].sum() - spiele["Q1_Gast"].sum(),
            "Q2_Tordifferenz": spiele["Q2_Eigene"].sum() - spiele["Q2_Gast"].sum(),
            "Q3_Tordifferenz": spiele["Q3_Eigene"].sum() - spiele["Q3_Gast"].sum(),
            "Q4_Tordifferenz": spiele["Q4_Eigene"].sum() - spiele["Q4_Gast"].sum(),
            "Siege": (spiele["Ergebnis_Typ"] == "Sieg").sum(),
            "Unentschieden": (spiele["Ergebnis_Typ"] == "Unentschieden").sum(),
            "Niederlagen": (spiele["Ergebnis_Typ"] == "Niederlage").sum()
        }

        stats_liste.append(stats)

    return pd.DataFrame(stats_liste)