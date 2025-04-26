# data_handler.py

import data.data_scraper as data_scraper
import data.data_parser as data_parser
import data.data_operator as data_operator

URL_SECOND_LEAGUE = "https://dsvdaten.dsv.de/Modules/WB/League.aspx?Season=2024&LeagueID=77&Group=&LeagueKind=L&StateID=17"

def scrape_data_to_df(url_league):
    # Scrape data from the website
    soup = data_scraper.scrape_dsv(url_league)
    
    # Parse into dataframes
    df_game_plan = data_parser.parse_game_plan(soup)
    df_score_board = data_parser.parse_score_board(soup)
    
    return df_game_plan, df_score_board

def extend_game_plan_and_score_board(df_game_plan, df_score_board):
    # Extend game plan with additional information
    df_game_plan = data_operator.extend_game_plan(df_game_plan)
    
    # Create team plans and stats
    df_team_plans = data_operator.create_team_plans(df_game_plan)
    df_team_stats = data_operator.create_team_stats(df_team_plans)

    df_score_board = data_operator.extend_score_board(df_score_board)
    
    return df_game_plan, df_team_plans, df_team_stats, df_score_board

# Function to get data from the second league
def get_second_league():
    # Get data from the second league
    df_game_plan, df_score_board = scrape_data_to_df(URL_SECOND_LEAGUE)

    # Extend data with additional information, team plans and stats
    df_game_plan, df_team_plans, df_team_stats, df_score_board = extend_game_plan_and_score_board(df_game_plan, df_score_board)
    return df_game_plan, df_team_plans, df_team_stats, df_score_board