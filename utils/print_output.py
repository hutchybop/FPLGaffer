from tabulate import tabulate


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
            player.get("team_name", ""),
            player.get("rating", ""),
            player.get("pos", ""),
            f"£{player.get("now_cost(m)", "")}m",
            player.get("form", ""),
            player.get("ep_next", ""),
            player.get("total_points", ""),
            player.get("minutes", ""),
            ppm,
            f"{player.get("selected_by_percent", "")}%",
            f"{player.get('chance_of_playing_next_round', '')}%" if player.get("chance_of_playing_next_round") is not None else "High",
            player.get("news", "")
        ])
    headers = ["Name", "Team", "Rating", "Pos", "Cost", "Form", "Exp Pts", "Pts", "Mins", "Pts/m", "Owned", "Chance of PLaying", "News"]
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
    player_cost = player.get("now_cost(m)", "")
    for i, candidate in enumerate(candidates, 1):
        cost_diff = (candidate.get("now_cost(m)", "") - player_cost)
        if cost_diff > 0:
            cost_str = f"£{cost_diff:.1f}m more"
        elif cost_diff < 0:
            cost_str = f"£{abs(cost_diff):.1f}m less"
        else:
            cost_str = "Same price"
        print(f"{i}. {candidate['web_name']} - {cost_str} (Rating: {candidate["rating"]:.1f})")


def print_ai_response(API_KEY, resp):
    if API_KEY:
        print("\n" + "=" * 60)
        print("AI Response")
        print("=" * 60)
        print(resp)   
        print("\n") 
    else:
        print("\n" + "=" * 60)
        print("AI Response")
        print("=" * 60)
        print("AI features disabled - No API key found in .env")
        print("Read readme.md for help") 
        print("\n") 