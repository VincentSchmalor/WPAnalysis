#data_parser.py

import pandas as pd

GAMEPLAN_TABLE_INDEX = 1
GAMEPLAN_CONTENT_ROW_INDEX = 2
SCOREBOARD_TABLE_INDEX = 2
SCOREBOARD_CONTENT_ROW_INDEX = 1
SCOREBOARD_MIN_COLS = 9

def parse_game_plan(soup):
    game_plan = soup.find_all("table")[GAMEPLAN_TABLE_INDEX]
    results = []

    for games in game_plan.find_all("tr")[GAMEPLAN_CONTENT_ROW_INDEX:]:
        cols = games.find_all("td")

        score_tag = cols[5].find("a")
        score_link = score_tag.get("href", "") if score_tag else ""

        results.append({
            "Spielnummer": cols[0].text,
            "Datum & Uhrzeit": cols[1].text,
            "Heim": cols[2].text,
            "Gast": cols[3].text,
            "Ort": cols[4].text,
            "Ergebnis": cols[5].text,
            "Viertel": cols[6].text,
            "Protokoll": score_link
        })

    return pd.DataFrame(results)

def parse_score_board(soup):
    score_board = soup.find_all("table")[SCOREBOARD_TABLE_INDEX]

    results = []

    for team in score_board.find_all("tr")[SCOREBOARD_CONTENT_ROW_INDEX:]:
        cols = team.find_all("td")

        if len(cols) < SCOREBOARD_MIN_COLS:
            continue

        results.append({
            "Platzierung": cols[0].text,
            "Team": cols[1].text,
            "Spiele": cols[2].text,
            "Siege": cols[3].text,
            "Niederlagen": cols[5].text,
            "Tore": cols[6].text,
            "Tordifferenz": cols[7].text,
            "Punkte": cols[8].text
        })

    return pd.DataFrame(results)