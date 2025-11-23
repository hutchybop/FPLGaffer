import sys
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Local imports
from config import constants, settings
from ai import ai_prompt, ai_advisor
from utils import file_handlers, print_output
from models import ratings, sort
from modes import transfer_mode, wildcard_mode


# Main script
if __name__ == "__main__":

    settings.validate_team_id()
    API_KEY, client_free, client_paid = settings.ai_client()

    # Fetch and process data
    bootstrap_data = settings.fetch_bootstrap_data()
    players = settings.format_all_players(bootstrap_data)
    ranges = settings.build_attribute_ranges(players)
    gw = settings.get_current_gameweek(bootstrap_data)
    bank, picks_pids = settings.my_picks(gw)

    # Ask user to choose wildcard mode or transfer mode
    mode = ""
    while mode not in ["t", "w"]:
        mode = input("Choose mode - Transfer (t) or Wildcard (w): ").lower().strip()
        if mode not in ["t", "w"]:
            print("Please enter 't' for Transfer mode or 'w' for Wildcard mode")
    
    # Setting player Attribute weights from user selected mode
    if mode == "t":
        weights, base_name = constants.TRANSFER_WEIGHTS, f"GW_{gw}_report"
    else:  # mode == "w"
        weights, base_name = constants.WC_WEIGHTS, "Wildcard_report"

    # Create an output txt file name
    filename = file_handlers.get_unique_filename(base_name)
    # Open the file and tee output
    f = open(filename, "w")
    original_stdout = sys.stdout
    sys.stdout = file_handlers.Tee(sys.stdout, f)

    # Calculate player ratings and add to player dicts
    players = ratings.compute_ml_ratings(players, weights)

    # Sort normalized rated players into a dic of GKP, DEF, MID, FWD
    sorted_players = sort.sort_players(players)

    # Create current team list and sort
    sorted_current = sort.sort_current_team(sorted_players, picks_pids)
    
    try:
        
        # --- Transfer Mode ---
        if mode == "t":
            AI_PROMPT = transfer_mode.transfer(bank, sorted_players, sorted_current)
            # --- Get and Print AI recommendations ---
            transfer_prompt = ai_prompt.ai_transfer_prompt()
            resp = ai_advisor.ai_fpl_helper(AI_PROMPT, transfer_prompt, client_free, client_paid, API_KEY)
            print_output.print_ai_response(API_KEY, resp)
        
        #  --- Wildcard Mode ---
        elif mode == "w":
            AI_PROMPT, total_team_cost = wildcard_mode.wildcard(sorted_players)
            # --- Get and Print AI recommendations ---
            wildcard_prompt = ai_prompt.ai_wildcard_prompt(total_team_cost)   
            resp = ai_advisor.ai_fpl_helper(AI_PROMPT, wildcard_prompt, client_free, client_paid, API_KEY)
            print_output.print_ai_response(API_KEY, resp)


    finally:
        # Restore stdout
        sys.stdout = original_stdout
