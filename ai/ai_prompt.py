def ai_transfer_prompt():
    """
    Generate AI prompt for transfer mode recommendations.
    Args:
        None
    Returns:
        str: formatted prompt string for AI transfer analysis
    """
    transfer_prompt = """
        You are an expert Fantasy Premier League (FPL) assistant.
        You will receive a JSON object.
        Never include <think> or hidden reasoning steps.
        ONLY ever return the suggested transfer and the reason.

        Each key in the JSON represents a player currently in the user's team
        (a potential transfer OUT).
        Each value contains:
        - "current": the full player data for that team player.
        - "candidates": a list of full player data dicts representing
          possible replacements.

        Your task:
        - Review **all** possible transfers (OUT → IN) across the dataset.
        - Choose **only one** transfer that would provide the greatest overall
          improvement for the team.
        - Only recommend a transfer if it clearly improves the team.
        - Base your decision solely on the provided player data.
        - Explain your reasoning briefly and clearly in plain language.

        Output format (plain text only, no JSON):
        OUT → IN (Team, £price) — short reasoning.
        Example:
        Baleba → Palmer (Chelsea, £6.7m) — higher xGI and better upcoming fixtures.
        Example:
        No transfer required — current team players outperform all candidates.
    """
    return transfer_prompt


def ai_wildcard_prompt(total_team_cost):
    """
    Generate AI prompt for wildcard mode squad building.
    Args:
        total_team_cost: float representing maximum team budget
    Returns:
        str: formatted prompt string for AI wildcard squad selection
    """
    wildcard_prompt = f"""
        You are an expert Fantasy Premier League (FPL) squad builder.
        Never include <think> or hidden reasoning.

        You will receive a JSON object with keys GKP, DEF, MID, FWD.
        Every player object includes a unique `id`.

        Build the best possible valid 15-player squad using only the provided players
        and return JSON only.

        Optimization goal:
        - Maximize squad quality within constraints using player rating as the primary
          signal, while also considering supporting stats (form, expected points,
          minutes, and other provided attributes).

        Hard constraints:
        - Exactly 2 GKP, 5 DEF, 5 MID, 3 FWD
        - Max 3 players from any one team
        - Total cost must be <= £{total_team_cost}m
        - No duplicate players

        Output schema (JSON only, no markdown, no extra text):
        {{
          "selected_player_ids": [<15 unique ids>]
        }}

        Example:
        {{
          "selected_player_ids": [45, 71, 103, 112, 118, 127, 131,
          149, 166, 177, 188, 194, 205, 216, 230]
        }}

        Do not return player names, positions, explanations, or any keys other than
        selected_player_ids.
    """
    return wildcard_prompt
