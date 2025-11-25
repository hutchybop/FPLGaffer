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
        list: replacement player dicts up to num_replacements
    """
    # Calculate max and min price of replacements
    player_cost = player.get("now_cost(m)", 0)
    available_budget = (bank) + player_cost
    min_price = 4.0
    max_price = available_budget
    # position = POS_MAP.get(player.get("element_type"))
    position = player.get("pos", "")
    # Filter candidates by budget, availability, and not in current team
    current_team_ids = {p["id"] for p in current_team}
    candidates = [
        p
        for p in sorted_players[position]
        if (
            min_price <= p["now_cost(m)"] <= max_price
            and p["id"] not in current_team_ids
            and p["status"] == "available"
            and p["chance_of_playing_next_round"] == 100
        )
    ]
    # Sort replacements best rated first
    sorted_candidates = sorted(candidates, key=lambda x: x["rating"], reverse=True)
    return sorted_candidates[:num_replacements]
