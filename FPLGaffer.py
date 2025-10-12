import requests
import os
import statistics
import sys
import json
import textwrap
import re
from openai import OpenAI
from dotenv import load_dotenv
from tabulate import tabulate

# Load .env
load_dotenv()

# --- Global Constants ---
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURE_URL = "https://fantasy.premierleague.com/api/fixtures/"
POS_MAP = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
TEAM_ID = os.getenv("FPL_TEAM_ID")
AI_MODEL = "qwen/qwen3-32b"

# --- AI setup ---
API_KEY = os.getenv("GROQ_API_KEY")
client = None
if API_KEY:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=API_KEY,
    )

# Global weights for all numeric keys in your player dict.
# Positive weights = increase rating when high.
# Negative weights = reduce rating when high (e.g. goals conceded).
# team/fixture/availability weights set to 0 to use them as multipliers.
ATTRIBUTE_WEIGHTS = {
    "minutes": 2.0,
    "goals_scored": 4.0,
    "assists": 3.0,
    "bonus": 1.5,
    "bps": 1.0,
    "total_points": 3.5,
    "points_per_game": 2.5,
    "form": 3.0,
    "ep_next": 2.5,
    "value_form": 1.5,
    "value_season": 1.5,
    "expected_goals": 2.5,
    "expected_assists": 2.0,
    "expected_goal_involvements": 2.5,
    "expected_goals_per_90": 2.0,
    "expected_assists_per_90": 1.5,
    "expected_goal_involvements_per_90": 2.0,
    "ict_index": 1.5,
    "influence": 1.0,
    "creativity": 1.0,
    "threat": 1.5,
    "clean_sheets": 2.5,
    "clean_sheets_per_90": 1.5,
    "saves": 2.0,
    "saves_per_90": 2.0,
    "penalties_saved": 1.0,
    "goals_conceded": -2.0,
    "goals_conceded_per_90": -2.0,
    "expected_goals_conceded": -1.5,
    "expected_goals_conceded_per_90": -1.5,
    # multipliers (handled separately) -> give weight 0 so they don't double-count in the base score
    "team_strength": 0.0,
    "team_fix_dif": 0.0,
    "chance_of_playing_next_round": 0.0
}


def ai_fpl_helper(prompt):
    """
    Get AI recommendations for FPL transfers.
    Args:
        prompt: json of players with replacements
    Returns:
        wrapped: str of ai response
    """
    SYSTEM_PROMPT = """
        You are an expert Fantasy Premier League (FPL) assistant.
        You will receive a JSON object.
        Never include <think> or hidden reasoning steps.
        ONLY ever return the suggested transfer and the reason

        Each key is a player currently in the user's team (a potential transfer OUT).
        Each value is a list of candidate players who could replace that player.

        Your task:
        - Review **all** possible transfers across the whole dataset.
        - Choose **only one** transfer (OUT → IN) that gives the greatest overall benefit.
        - Consider player form, expected returns (xGI), fixture difficulty, and availability.
        - Ignore players who are injured or unlikely to play ('status' != 'a' or chance_of_playing_next_round < 75).
        - Prefer realistic upgrades that fit typical FPL budgets (avoid big cost jumps).
        - Explain your reasoning briefly in natural text.

        Output format (plain text only, no JSON):
        OUT → IN (Team, £price) — short reasoning.
        Example:
        Baleba → Palmer (Chelsea, £6.7m) — higher xGI and strong upcoming fixtures.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    resp = client.chat.completions.create(
        model=AI_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=600,
    )
    raw = resp.choices[0].message.content.strip()
    # Remove <think> sections if present and wrap text
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    wrapped = "\n".join(textwrap.fill(line, width=120) for line in cleaned.splitlines())
    return wrapped


def fetch_bootstrap_data():
    """
    Fetch bootstrap data from FPL API.
    Returns:
        response: json of all FPL bootstrap data
    """
    response = requests.get(BOOTSTRAP_URL)
    response.raise_for_status() # Stops code if error in response
    return response.json()


def fetch_fixture_data():
    """
    "Fetch fixture data from FPL API.
    Returns:
        response: json of all FPL fixture data
    """
    response = requests.get(FIXTURE_URL)
    response.raise_for_status() # Stops code if error in response
    return response.json()


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
    squad_url = f"https://fantasy.premierleague.com/api/entry/{TEAM_ID}/event/{gw}/picks/"
    response = requests.get(squad_url)
    response.raise_for_status()
    picks = response.json()
    bank = picks.get("entry_history", {}).get("bank", 0) / 10.0  # Convert to millions
    picks_pids = [el.get("element") for el in picks.get("picks", [])]
    return bank, picks_pids


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
            "name": team["name"],
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
            "news": el.get("news", ""),
            "chance_of_playing_next_round": el.get("chance_of_playing_next_round", ""),
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
            "expected_goals_per_90": el.get("expected_goals_per_90", ""),
            "expected_assists_per_90": el.get("expected_assists_per_90", ""),
            "expected_goal_involvements_per_90": el.get("expected_goal_involvements_per_90", ""),
            "ict_index": el.get("ict_index", ""),
            "influence": el.get("influence", ""),
            "creativity": el.get("creativity", ""),
            "threat": el.get("threat", ""),
            "clean_sheets": el.get("clean_sheets", ""),
            "saves": el.get("saves", ""),
            "penalties_saved": el.get("penalties_saved", ""),
            "goals_conceded": el.get("goals_conceded", ""),
            "saves_per_90": el.get("saves_per_90", ""),
            "expected_goals_conceded": el.get("expected_goals_conceded", ""),
            "expected_goals_conceded_per_90": el.get("expected_goals_conceded_per_90", ""),
            "clean_sheets_per_90": el.get("clean_sheets_per_90", ""),
            "goals_conceded_per_90": el.get("goals_conceded_per_90", ""),
            "selected_by_percent": el.get("selected_by_percent", "")
        }
        players.append(player)
    return players


def build_attribute_ranges(players):
    """
    Build min/max ranges for each numeric attribute across all players.
    Args:
        players: List of player dict with team stats (format_all_players)
    Returns:
        ranges: {attribute: {min: float, max: float}}
    """
    ranges = {}
    for key in players[0].keys():
        # Skip meta fields
        if key in ["web_name", "team_name", "status", "news", "element_type"]:
            continue
        # Try converting values to float; skip non-numeric
        values = []
        for p in players:
            try:
                val = float(p.get(key, 0))
                if not (val is None or val != val):  # not None or NaN
                    values.append(val)
            except:
                pass
        if values:
            ranges[key] = {"min": min(values), "max": max(values)}
    return ranges


def compute_generic_rating(player, ranges, attribute_weights):
    """
    Compute player rating (0-1000) based on attributes and weights.
    Args:
        player: dict (format_all_players)
        ranges: dict mapping attribute -> {"min": x, "max": y} (build_attribute_ranges)
        attribute_weights: dict of weights for each attribute (ATTRIBUTE_WEIGHTS)
    Returns: 
        rating: num (0..1000)
    """
    def safe_float(value, default=0.0):
        """Safely convert value to float."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def normalize(value, min_val, max_val):
        """Normalize value to 0-1 range."""
        val = safe_float(value)
        if max_val == min_val:
            # if no spread, treat as 0
            return 0.0
        return max(0.0, min(1.0, (val - min_val) / (max_val - min_val)))
    
    # Calculate base score from attributes
    numerator = 0.0
    pos_weight_sum = 0.0
    neg_weight_sum = 0.0
    # Iterate over each attribute  in ranges
    for key, r in ranges.items():
        # skip anything explicitly non-numeric/meta if present
        weight = attribute_weights.get(key, 1.0)  # default 1.0 if not explicitly defined
        # skip attributes intended as multipliers
        if weight == 0.0:
            continue
        norm = normalize(player.get(key), r["min"], r["max"])
        numerator += norm * weight
        if weight > 0:
            pos_weight_sum += weight
        else:
            neg_weight_sum += abs(weight)
    # Calculate base score
    total_weight_span = pos_weight_sum + neg_weight_sum
    if total_weight_span == 0:
        base_score = 0.0
    else:
        min_possible = -neg_weight_sum
        max_possible = pos_weight_sum
        if max_possible - min_possible == 0:
            base_score = 0.0
        else:
            base_score = (numerator - min_possible) / (max_possible - min_possible)
            base_score = max(0.0, min(1.0, base_score))
    # Availability multiplier (use chance_of_playing_next_round as multiplier)
    availability = safe_float(player.get("chance_of_playing_next_round") or 100.0) / 100.0
    # Fixture difficulty adjustment (assume 1..5 where lower is easier)
    fix_dif = safe_float(player.get("team_fix_dif", 2.5))
    fixture_factor = 1.0 + (2.5 - fix_dif) * 0.05  # easier fixtures => small boost
    # Team strength adjustment (small boost)
    team_strength = safe_float(player.get("team_strength", 100.0))
    # Convert team_strength 1-5 scale to 100-based
    if team_strength <= 10:
        team_strength_scaled = 100.0 + (team_strength - 3.0) * 5.0  # small conversion heuristic
    else:
        team_strength_scaled = team_strength
    team_factor = 1.0 + (team_strength_scaled - 100.0) / 1000.0
    # Final rating scaled to 0..1000
    rating = base_score * availability * fixture_factor * team_factor * 1000.0
    return round(rating, 2)


def sort_players(players):
    """
    Sort players into positions and by rating.
    Args:
        players: list of player dicts (format_all_players)
    Ruturns:
        dict: {GKP: [{player}], DEF: [{player}], MID: [{player}], FWD: [{player}],}
    """
    positions = {"GKP": [], "DEF": [], "MID": [], "FWD": []}
    for player in players:
        pos_key = POS_MAP.get(player.get("element_type"))
        if pos_key in positions:
            positions[pos_key].append(player)
    # Sort each position by rating
    return {
        pos: sorted(players_list, key=lambda x: x['normalized_rating'], reverse=True)
        for pos, players_list in positions.items()
    }


def find_replacements(player, bank, sorted_players, current_team, num_replacements=4):
    """
    Find replacement candidates for a player.
        Args:
            player: dict of player to replace
            bank: num of current team bank in millions (my_picks)
            sorted_players: dict of players per position (sort_players)
            current_team: list of current team player dicts
            num_replacements: num of number of replacements to give (default = 4)
        Returns:
            list of replacement player dicts upto num_replacements
    """
    # Calculate max and min price of replacements
    player_cost = player.get("now_cost", 0)
    available_budget = (bank * 10) + player_cost
    min_price = 40
    max_price = available_budget
    position = POS_MAP.get(player.get("element_type"))
    # Filter candidates by budget, availability, and not in current team
    current_team_ids = {p["id"] for p in current_team}
    candidates = [
        p for p in sorted_players[position]
        if (min_price <= p["now_cost"] <= max_price and
            p["id"] not in current_team_ids and
            p["status"] == "a" and
            p["chance_of_playing_next_round"] == 100 or None)
    ]
    # Sort replacements best rated first
    sorted_candidates = sorted(candidates, key=lambda x: x['normalized_rating'], reverse=True)
    return sorted_candidates[:num_replacements]


class Tee:
    """Redirect stdout to both terminal and a file"""
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


def get_unique_filename(base_name, ext = ".txt"):
    """
    Generate a unique filename like base_name.txt, base_name_2.txt, etc.
    Args:
        base_name: str of naming convention for file
        ext: str of file extension (default = ".txt")
    Return:
        str of file name
    """
    filename = f"{base_name}{ext}"
    counter = 2
    while os.path.exists(filename):
        filename = f"{base_name}_{counter}{ext}"
        counter += 1
    return filename


def print_players(players):
    """
    Print players in a formatted table.
    Args:
        players: list of player dicts
    Returns:
        print of table containing player attributes
    """
    # Prepare table data
    table_data = []
    for player in players:
        # Calculate value for money (points per million)
        cost = player.get("now_cost", 0)
        total_points = player.get("total_points", 0)
        ppm = round((total_points / cost * 10), 2) if cost > 0 else 0.0
        # Add data for player
        table_data.append([
            player.get("web_name", ""),
            player.get("normalized_rating", ""),
            POS_MAP.get(player.get("element_type", ""), ""),
            f"£{player.get("now_cost", "") /10}m",
            player.get("form", ""),
            player.get("ep_next", ""),
            player.get("total_points", ""),
            player.get("minutes", ""),
            ppm,
            f"{player.get("selected_by_percent", "")}%",
            f"{player.get('chance_of_playing_next_round', '')}%" if player.get("chance_of_playing_next_round") is not None else "High",
            player.get("news", "")
        ])
    headers = ["Name", "Rating", "Pos", "Cost", "Form", "Exp Pts", "Pts", "Mins", "Pts/m", "Owned", "Chance of PLaying", "News"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def print_replacement_impact(player, candidates):
    """
    Print financial impact of replacements.
    Args:
        player: dict of player
        candidates: list of replacement player dicts
    Returns: print of replacement players cost impact
    """
    # Print financial impact
    player_cost = player.get("now_cost", "")
    for i, candidate in enumerate(candidates, 1):
        cost_diff = (candidate.get("now_cost", "") - player_cost) /10
        if cost_diff > 0:
            cost_str = f"£{cost_diff:.1f}m more"
        elif cost_diff < 0:
            cost_str = f"£{abs(cost_diff):.1f}m less"
        else:
            cost_str = "Same price"
        print(f"{i}. {candidate['web_name']} - {cost_str} (Rating: {candidate["normalized_rating"]:.1f})")


# Main script
if __name__ == "__main__":
    # Fetch and process data
    bootstrap_data = fetch_bootstrap_data()
    players = format_all_players(bootstrap_data)
    ranges = build_attribute_ranges(players)
    gw = get_current_gameweek(bootstrap_data)
    bank, picks_pids = my_picks(gw)

    # Create an output txt file name
    base_name = f"GW_{gw}_report"
    filename = get_unique_filename(base_name)

    # Open the file and tee output
    f = open(filename, "w")
    original_stdout = sys.stdout
    sys.stdout = Tee(sys.stdout, f)
    
    try:
        # Calculate player ratings and add to player dicts
        for player in players:
            player["rating"] = compute_generic_rating(player, ranges, ATTRIBUTE_WEIGHTS)

        # Normalize player ratings from 0 to 100 and add to player dicts
        min_rating = min(p["rating"] for p in players)
        max_rating = max(p["rating"] for p in players)
        for player in players:
            normalized = ((player["rating"] - min_rating) / (max_rating - min_rating)) * 100
            player["normalized_rating"] = round(normalized, 2)

        # Sort normalized rated players into a dic of GKP, DEF, MID, FWD
        sorted_players = sort_players(players)

        # Add rated players from current team into a list and sort
        current_team = [p for players_list in sorted_players.values() 
                    for p in players_list if p['id'] in picks_pids]
        sorted_current = sorted(current_team, key=lambda x: x['normalized_rating'])

        # Get user input for how many players to show replacements for
        num_of_replacements = -1
        while not 0 <= num_of_replacements <= 6:
            try:
                num_of_replacements = int(input("How many players do you want to show replacements for? (0-6) "))
            except ValueError:
                print("Please enter a valid number between 0 and 6")

        # Compute min and max rating for each position
        rating_ranges = {
            pos: {
                "min": min(p["normalized_rating"] for p in players_list),
                "max": max(p["normalized_rating"] for p in players_list)
            }
            for pos, players_list in sorted_players.items()
        }

        # Print positional ratings
        print("\n")
        print("=" * 60)
        print("POSITIONAL MIN AND MAX RATINGS")
        print("=" * 60)
        # Print nicely
        for pos, stats in rating_ranges.items():
            print(f"{pos}: MAX={stats['max']}, MIN={stats['min']}")

        # Print current team in a readable format
        print("\n")
        print("=" * 60)
        print("FPL TEAM ASSESSMENT")
        print("=" * 60)
        print("Players sorted by performance score (lowest to highest)")
        print(f"BANK: £{bank}m" + "\n")
        print_players(sorted_current)

        # Print players and replacements
        if num_of_replacements > 0:
            print("\n")
            print("=" * 60)
            print(f"REPLACEMENT SUGGESTIONS FOR {num_of_replacements} PLAYERS")
            print("=" * 60)
            # Generate replacement suggestions
            player_replacement_options = {}
            for player in sorted_current[:num_of_replacements]:
                # Get a list a 4 replacement players for player
                candidates = find_replacements(player, bank, sorted_players, sorted_current)
                player_name = player.get("web_name", "")
                player_pos = POS_MAP.get(player.get("element_type"), "")
                player_cost = player.get("now_cost", "") /10
                player_rating = player.get("normalized_rating", "")
                print("\n" + "=" * 60)
                print(f"REPLACEMENT OPTIONS FOR: {player_name} ({player_pos}, £{player_cost}m, Rating: {player_rating})")
                print("=" * 60)
                # Print replacement players, if there are any
                if candidates:
                    print_players(candidates)
                    print_replacement_impact(player, candidates)
                    player_replacement_options[player_name] = candidates
                else:
                    print("No suitable replacements found within budget.")

            if API_KEY:
                # Attributes to send to AI
                keep_keys = {
                    "web_name",
                    "element_type",
                    "now_cost",
                    "team_name",
                    "team_fix_dif",
                    "status",
                    "chance_of_playing_next_round",
                    "minutes",
                    "goals_scored",
                    "assists",
                    "clean_sheets",
                    "total_points",
                    "form",
                    "ep_next",
                    "expected_goal_involvements_per_90",
                    "expected_goals_conceded_per_90",
                    "selected_by_percent",
                    "rating",
                    "normalized_rating",
                }

                # Trim keys to the keep_keys items and convert element_type to GKP, DEF ect
                trimmed = {
                    player_name: [
                        {
                            k: (POS_MAP.get(v, v) if k == "element_type" else v)
                            for k, v in player.items()
                            if k in keep_keys
                        }
                        for player in replacements
                    ]
                    for player_name, replacements in player_replacement_options.items()
                }
                prompt= json.dumps(trimmed, ensure_ascii=False)

                # Get and Print AI recommendations:
                resp = ai_fpl_helper(prompt)
                print("\n" + "=" * 60)
                print("AI Response")
                print("=" * 60)
                print(resp)   
                print("\n") 
            
            else:
                print("\n" + "=" * 60)
                print("AI Response")
                print("=" * 60)
                print("AI features disabled - No GROQ_API_KEY found in .env")   
                print("\n") 

        else:
            print("\n")
            print("=" * 60)
            print("NO REPLACEMENTS SELECTED")
            print("=" * 60)

    finally:
        # Restore stdout
        sys.stdout = original_stdout
