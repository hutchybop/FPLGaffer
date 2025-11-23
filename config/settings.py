import sys
import requests
import statistics
from openai import OpenAI

#  Local imports
from config import constants


def validate_team_id():
    # Validate TEAM_ID is in .env
    if not constants.TEAM_ID:
        print("No FPL team ID found in .env file")
        print("Please add: FPL_TEAM_ID=<your_team_id> to your .env file")
        print("Refer to README.md for setup instructions")
        sys.exit(1)


def ai_client():
    # Create clients
    API_KEY = True
    print("\n")
    print("=" * 60)
    print("AI API KEY STATUS")
    print("=" * 60)
    if constants.FREE_API_KEY and constants.PAID_API_KEY:
        client_free = OpenAI(base_url=constants.BASE_URL, api_key=constants.FREE_API_KEY)
        client_paid = OpenAI(base_url=constants.BASE_URL, api_key=constants.PAID_API_KEY)
        print("Both FREE and PAID AI API keys avaliable")
        print("Will revert to PAID if free limits are met")
    elif not constants.FREE_API_KEY and constants.PAID_API_KEY:
        client_paid = OpenAI(base_url=constants.BASE_URL, api_key=constants.PAID_API_KEY)
        client_free = None
        print("Only PAID API KEY available, you will be charged per request")
    elif not constants.PAID_API_KEY and constants.FREE_API_KEY:
        client_free = OpenAI(base_url=constants.BASE_URL, api_key=constants.FREE_API_KEY)
        client_paid = None
        print("Only FREE AI API key available")
    else:
        client_free = None
        client_paid = None
        API_KEY = False
        print("No AI API keys available, AI function disabled")
    print("=" * 60)
    return API_KEY, client_free, client_paid


def fetch_fixture_data():
    """
    "Fetch fixture data from FPL API.
    Returns:
        response: json of all FPL fixture data
    """
    response = requests.get(constants.FIXTURE_URL)
    response.raise_for_status() # Stops code if error in response
    return response.json()


def fetch_bootstrap_data():
    """
    Fetch bootstrap data from FPL API.
    Returns:
        response: json of all FPL bootstrap data
    """
    response = requests.get(constants.BOOTSTRAP_URL)
    response.raise_for_status() # Stops code if error in response
    return response.json()


def team_stats(bootstrap_data, fixture_data, num_fix=3):
    """
    Pre-calculate fixture difficulties for all teams to avoid repeated calculations.
    Args: 
        bootstrap_data: json of all the FPL bootstrap data (fetch_bootstrap_data)
        fixture_data: json of all the FPL fixture data (fetch_fixture_data)
        num_fix: num of fixtures to assess (default = 3)
    Returns: 
        dict: {team_id: {"name": str, "strength": int, "fix_diff": float}}
    """
    team_data = {}
    # Initialize with team names and strengths
    for team in bootstrap_data["teams"]:
        team_id = team["id"]
        team_data[team_id] = {
            "name": team["short_name"],
            "strength": team["strength"]
        }
    # Calculate fixture difficulties for each team
    for team_id in team_data.keys():
        team_fixtures = []
        for fixture in fixture_data:
            if (fixture["team_h"] == team_id or fixture["team_a"] == team_id) and not fixture["finished"]:
                team_fixtures.append(fixture)
        # Sort by kickoff time and take next N fixtures
        team_fixtures.sort(key=lambda x: x["kickoff_time"])
        next_fixtures = team_fixtures[:num_fix]
        # Calculate average difficulty
        difficulties = []
        for fixture in next_fixtures:
            if fixture["team_h"] == team_id:
                difficulties.append(fixture["team_h_difficulty"])
            else:
                difficulties.append(fixture["team_a_difficulty"])
        team_data[team_id]["fix_diff"] = statistics.mean(difficulties) if difficulties else 2.5
    return team_data

def safe_chance(v):
    if v in [None, "None", ""]:
        return float(100)  # assume 100% if missing
    try:
        return float(v)
    except Exception as e:
        return 100.0  # fallback


def format_all_players(bootstrap_data):
    """
    Format all player data with team statistics.
    Args:
        bootstrap_data: json of all the FPL bootstrap data (fetch_bootstrap_data)
    Returns:
        player: List of player dict with team stats
    """
    fixture_data = fetch_fixture_data()
    team_data = team_stats(bootstrap_data, fixture_data)
    players = []
    for el in bootstrap_data["elements"]:
        team_id = el.get("team")
        team_info = team_data.get(team_id, {"name": "", "strength": 0, "fix_diff": 2.5})
        player = {
            "web_name": el.get("web_name", ""),
            "element_type": el.get("element_type", ""),
            "id": el.get("id", ""),
            "now_cost": el.get("now_cost", ""),
            "team_name": team_info["name"],
            "team_strength": team_info["strength"],
            "team_fix_dif": team_info["fix_diff"],
            "status": el.get("status", ""),
            "chance_of_playing_next_round": safe_chance(el.get("chance_of_playing_next_round")),
            "news": el.get("news", ""),
            "minutes": el.get("minutes", ""),
            "goals_scored": el.get("goals_scored", ""),
            "assists": el.get("assists", ""),
            "bonus": el.get("bonus", ""),
            "bps": el.get("bps", ""),
            "total_points": el.get("total_points", ""),
            "points_per_game": el.get("points_per_game", ""),
            "form": el.get("form", ""),
            "ep_next": el.get("ep_next", ""),
            "value_form": el.get("value_form", ""),
            "value_season": el.get("value_season", ""),
            "expected_goals": el.get("expected_goals", ""),
            "expected_assists": el.get("expected_assists", ""),
            "expected_goal_involvements": el.get("expected_goal_involvements", ""),
            "ict_index": el.get("ict_index", ""),
            "influence": el.get("influence", ""),
            "creativity": el.get("creativity", ""),
            "threat": el.get("threat", ""),
            "clean_sheets": el.get("clean_sheets", ""),
            "saves": el.get("saves", ""),
            "penalties_saved": el.get("penalties_saved", ""),
            "goals_conceded": el.get("goals_conceded", ""),
            "expected_goals_conceded": el.get("expected_goals_conceded", ""),
            "selected_by_percent": el.get("selected_by_percent", "")
        }
        players.append(player)
    return players


def get_current_gameweek(bootstrap_data):
    """
    Get current gameweek from bootstrap data.
    Args:
        bootstrap_data: json of all the FPL bootstrap data (fetch_bootstrap_data)
    Returns:
        game week: num of actual game week or 1 if not found
    """
    for event in bootstrap_data["events"]:
        if event.get("is_current"):
            return event["id"]
    return 1  # Default to GW1 if no current GW found


def my_picks(gw):
    """
    Get user's current team picks for a given gameweek.
    Args:
        gw: num of current game week (get_current_gameweek)
    Ruturns:
        bank: num of current team bank in millions
        pick_pids: List of current team players ids
    """
    squad_url = f"https://fantasy.premierleague.com/api/entry/{constants.TEAM_ID}/event/{gw}/picks/"
    response = requests.get(squad_url)
    response.raise_for_status()
    picks = response.json()
    bank = picks.get("entry_history", {}).get("bank", 0) / 10.0  # Convert to millions
    picks_pids = [el.get("element") for el in picks.get("picks", [])]
    return bank, picks_pids