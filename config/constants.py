import os


# --- Global Constants ---
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURE_URL = "https://fantasy.premierleague.com/api/fixtures/"
POS_MAP = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
STATUS_MAP = {
    "a": "available",
    "d": "doubtful",
    "i": "injured",
    "s": "suspended",
    "u": "unavailable",
    "n": "not in squad",
}
TEAM_ID = os.getenv("FPL_TEAM_ID")


# --- AI setup ---
FREE_API_KEY = os.getenv("GROQ_API_KEY_FREE")
PAID_API_KEY = os.getenv("GROQ_API_KEY_PAID")
BASE_URL = "https://api.groq.com/openai/v1"
# AI_MODEL = "qwen/qwen3-32b"
AI_MODEL = os.getenv("AI_MODEL") or "llama-3.3-70b-versatile"
AI_PROMPT = ""


# Global weights for all numeric keys in your player dict.
# Positive weights = increase rating when high.
# Negative weights = reduce rating when high (e.g. goals conceded).
# team/fixture/availability weights set to 0 to use them as multipliers.
WC_WEIGHTS = {
    "minutes": 2.5,
    "goals_scored": 3.5,
    "assists": 2.8,
    "bonus": 1.2,
    "bps": 0.8,
    "total_points": 2.2,
    "points_per_game": 3.0,
    "form": 1.8,         # lowered (too noisy)
    "ep_next": 1.2,
    "value_form": 2.2,
    "value_season": 2.3,
    "expected_goals": 3.0,
    "expected_assists": 2.4,
    "expected_goal_involvements": 3.1,
    "expected_goals_per_90": 1.6,
    "expected_assists_per_90": 1.3,
    "expected_goal_involvements_per_90": 1.5,
    "ict_index": 1.3,
    "influence": 0.6,
    "creativity": 0.7,
    "threat": 1.3,
    "clean_sheets": 2.4,
    "clean_sheets_per_90": 1.6,
    "saves": 1.8,
    "saves_per_90": 1.6,
    "penalties_saved": 0.5,
    "goals_conceded": -1.6,
    "goals_conceded_per_90": -1.6,
    "expected_goals_conceded": -1.2,
    "expected_goals_conceded_per_90": -1.2,
    # multipliers (keep at 0 or will cause nan ratings)
    "team_strength": 0.0,
    "team_fix_dif": 0.0,
    "chance_of_playing_next_round": 0.0
}
TRANSFER_WEIGHTS = {
    "minutes": 3.0,
    "goals_scored": 4.5,
    "assists": 3.4,
    "bonus": 2.0,
    "bps": 1.2,
    "total_points": 2.0,
    "points_per_game": 2.0,
    "form": 4.8,          # big increase
    "ep_next": 4.0,       # key for transfers
    "value_form": 0.8,
    "value_season": 0.5,
    "expected_goals": 3.4,
    "expected_assists": 2.6,
    "expected_goal_involvements": 3.5,
    "expected_goals_per_90": 1.2,
    "expected_assists_per_90": 1.0,
    "expected_goal_involvements_per_90": 1.2,
    "ict_index": 1.0,
    "influence": 0.5,
    "creativity": 0.6,
    "threat": 1.5,
    "clean_sheets": 3.4,
    "clean_sheets_per_90": 1.2,
    "saves": 2.4,
    "saves_per_90": 2.4,
    "penalties_saved": 0.5,
    "goals_conceded": -3.0,
    "goals_conceded_per_90": -3.0,
    "expected_goals_conceded": -2.4,
    "expected_goals_conceded_per_90": -2.4,
    # multipliers (keep at 0 or will cause nan ratings)
    "team_strength": 0.0,
    "team_fix_dif": 0.0,
    "chance_of_playing_next_round": 0.0
}

