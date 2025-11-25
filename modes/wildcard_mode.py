import json

# Local imports
from utils import format_date, print_output


def wildcard(sorted_players):
    """
    Handle wildcard mode interface and generate AI prompt.
    Args:
        sorted_players: dict of players per position (sort_players)
    Returns:
        tuple: (AI_PROMPT, total_team_cost) - JSON string and team budget
    """
    # Find out the current team total cost from the user
    total_team_cost = -1
    while not 0 <= total_team_cost <= 100:
        try:
            total_team_cost = float(
                input("Enter the current total value of your team (0-100): ")
            )
        except ValueError:
            print("Please enter a valid number between 0 and 100")

    # Shows best players from each position
    print("\n")
    print("=" * 60)
    print(f"WILDCARD MODE ({format_date.format_date_with_ordinal()})")
    print("=" * 60)

    # Create a dict with the required amount of players per position
    wildcard_trimmed = {
        "GKP": sorted_players["GKP"][:5],
        "DEF": sorted_players["DEF"][:15],
        "MID": sorted_players["MID"][:15],
        "FWD": sorted_players["FWD"][:10],
    }

    # Print tables for each position
    positions = [
        ("TOP GOALKEEPERS", "GKP"),
        ("TOP DEFENDERS", "DEF"),
        ("TOP MIDFIELDERS", "MID"),
        ("TOP FORWARDS", "FWD"),
    ]

    for title, position in positions:
        print("\n")
        print("=" * 60)
        print(title)
        print("=" * 60)
        print_output.print_players(wildcard_trimmed[position])

    # Prepare AI prompt for the wildcard selection
    AI_PROMPT = json.dumps(wildcard_trimmed, ensure_ascii=False, indent=2)
    return AI_PROMPT, total_team_cost
