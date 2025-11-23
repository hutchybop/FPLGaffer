import json

# Local imports
from utils import format_date, print_output
from models import replacements


def transfer(bank, sorted_players, sorted_current):
    print("\n")
    print("=" * 60)
    print(f"TRANSFER MODE ({format_date.format_date_with_ordinal()})")
    print("=" * 60)

    # Get user input for how many players to show replacements for
    num_of_replacements = -1
    while not 0 <= num_of_replacements <= 15:
        try:
            num_of_replacements = int(input("How many players do you want to show replacements for? (0-15) "))
        except ValueError:
            print("Please enter a valid number between 0 and 15")

    # Compute min and max rating for each position
    rating_ranges = {
        pos: {
            "min": min(p["rating"] for p in players_list),
            "max": max(p["rating"] for p in players_list)
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
    print_output.print_players(sorted_current)

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
            candidates = replacements.find_replacements(player, bank, sorted_players, sorted_current)
            player_name = player.get("web_name", "")
            player_pos = player.get("pos", "")
            player_cost = player.get("now_cost(m)", "")
            player_rating = player.get("rating", "")
            player_team = player.get("team_name", "")
            print("\n" + "=" * 60)
            print(f"REPLACEMENT OPTIONS FOR: {player_name} - {player_team} ({player_pos}, £{player_cost}m, Rating: {player_rating})")
            print("=" * 60)
            # Print replacement players, if there are any
            if candidates:
                print_output.print_players(candidates)
                print_output.print_replacement_impact(player, candidates)
                player_replacement_options[player_name] = candidates
            else:
                print("No suitable replacements found within budget.")

        # Prepare the AI prompt for transfer mode (full data, no trimming)
        transfers_full = {
            player.get("web_name", ""): {
                "current": player,  # full current player dict
                "candidates": replacements  # list of full candidate dicts
            }
            for player, replacements in zip(sorted_current[:num_of_replacements], player_replacement_options.values())
        }

        AI_PROMPT = json.dumps(transfers_full, ensure_ascii=False, indent=2)
        return AI_PROMPT

    else:
        print("\n")
        print("=" * 60)
        print("NO REPLACEMENTS SELECTED")
        print("=" * 60)