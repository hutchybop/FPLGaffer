# Local imports
from config import constants


def sort_players(players):
    """
    Sort players into positions and by rating, while cleaning and formatting each player dict.
    Args:
        players: list of player dicts (format_all_players)
    Ruturns:
        dict: {GKP: [{player}], DEF: [{player}], MID: [{player}], FWD: [{player}],}
    """
    positions = {"GKP": [], "DEF": [], "MID": [], "FWD": []}
    for p in players:
        pos_key = constants.POS_MAP.get(p.get("element_type"))
        if pos_key not in positions:
            continue  # skip unknown element types
        player = p.copy()  # avoid mutating the original dict
        # Defining the new key values
        now_cost = round(player.get("now_cost", 0) / 10, 1)
        team_fix_dif = round(player.get("team_fix_dif", 0), 2)
        chance_playing = (
            100
            if player.get("chance_of_playing_next_round") in [None, "None", ""]
            else player.get("chance_of_playing_next_round")
        )
        status = constants.STATUS_MAP.get(player.get("status", "a"), "available")
        # Apply transformations
        player["pos"] = pos_key
        player["now_cost(m)"] = now_cost
        player["team_fix_dif"] = team_fix_dif
        player["status"] = status
        player["chance_of_playing_next_round"] = chance_playing
        # Remove unwanted keys
        player.pop("now_cost", None)
        player.pop("value_form", None)
        player.pop("value_season", None)
        positions[pos_key].append(player)
    # Sort each position by rating
    return {
        pos: sorted(players_list, key=lambda x: x['normalized_rating'], reverse=True)
        for pos, players_list in positions.items()
    }

def sort_current_team(sorted_players, picks_pids):
    # Add rated players from current team into a list and sort
    current_team = [p for players_list in sorted_players.values() 
                for p in players_list if p['id'] in picks_pids]
    sorted_current = sorted(current_team, key=lambda x: x['normalized_rating'])
    return sorted_current