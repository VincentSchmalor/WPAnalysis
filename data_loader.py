# data_loader.py
import requests
from bs4 import BeautifulSoup
import pandas as pd

def daten_laden():
    URL = "https://dsvdaten.dsv.de/Modules/WB/League.aspx?Season=2024&LeagueID=77&Group=&LeagueKind=L&StateID=17"
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    return soup

def spielplan_laden(soup):
    spielplan = soup.find_all("table")[1]
    results = []

    for spiele in spielplan.find_all("tr")[2:]:
        cols = spiele.find_all("td")

        ergebnis_tag = cols[5].find("a")
        protokoll_link = ergebnis_tag.get("href", "") if ergebnis_tag else ""

        results.append({
            "Spielnummer": cols[0].text,
            "Datum & Uhrzeit": cols[1].text,
            "Heim": cols[2].text,
            "Gast": cols[3].text,
            "Ort": cols[4].text,
            "Ergebnis": cols[5].text,
            "Viertel": cols[6].text,
            "Protokoll": protokoll_link
        })

    return pd.DataFrame(results)

def tabelle_laden(soup):
    tabelle = soup.find_all("table")[2]

    results = []

    for team in tabelle.find_all("tr")[1:]:
        cols = team.find_all("td")

        if len(cols) < 9:
            continue

        results.append({
            "Platzierung": cols[0].text,
            "Team": cols[1].text,
            "Spiele": cols[2].text,
            "Siege": cols[3].text,
            #"Unentschieden": cols[4].text,
            "Niederlagen": cols[5].text,
            "Tore": cols[6].text,
            "Tordifferenz": cols[7].text,
            "Punkte": cols[8].text
        })

    return pd.DataFrame(results)