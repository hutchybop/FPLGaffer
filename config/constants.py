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
    "minutes": 2.2,                            # Slightly increased - reliability matters
    "goals_scored": 3.8,                       # Slightly reduced
    "assists": 3.0,           
    "bonus": 1.5,             
    "bps": 1.0,               
    "total_points": 3.0,                       # Reduced - historical less important
    "points_per_game": 2.8,                    # Slightly increased - consistency
    "form": 2.5,                               # Reduced - recent form less critical long-term
    "ep_next": 1.5,                            # Reduced - single gameweek less important
    "value_form": 2.0,                         # Increased - value matters
    "value_season": 2.0,                       # Increased
    "expected_goals": 2.5,    
    "expected_assists": 2.0,  
    "expected_goal_involvements": 2.5,  
    "expected_goals_per_90": 2.3,              # Slightly increased - efficiency
    "expected_assists_per_90": 1.8,            # Slightly increased
    "expected_goal_involvements_per_90": 2.2,  # Slightly increased
    "ict_index": 1.8,                          # Slightly increased - underlying metrics
    "influence": 1.0,         
    "creativity": 1.0,        
    "threat": 1.5,            
    "clean_sheets": 2.3,                       # Slightly reduced
    "clean_sheets_per_90": 1.7,                # Slightly increased
    "saves": 2.0,             
    "saves_per_90": 2.0,      
    "penalties_saved": 1.0,   
    "goals_conceded": -1.8,                    # Slightly reduced impact
    "goals_conceded_per_90": -1.8,             # Slightly reduced
    "expected_goals_conceded": -1.3,           # Slightly reduced
    "expected_goals_conceded_per_90": -1.3,    # Slightly reduced
    # multipliers (keep at 0)
    "team_strength": 0.0,
    "team_fix_dif": 0.0,
    "chance_of_playing_next_round": 0.0
}
TRANSFER_WEIGHTS = {
    "minutes": 2.8,                            # Increased - must play next games
    "goals_scored": 4.2,                       # Increased - immediate returns
    "assists": 3.2,                            # Slightly increased
    "bonus": 2.0,                              # Increased - bonus points valuable
    "bps": 1.2,                                # Slightly increased
    "total_points": 3.0,                       # Reduced - historical less important
    "points_per_game": 2.3,                    # Reduced
    "form": 3.8,                               # Highly increased - current form crucial
    "ep_next": 3.5,                            # Highly increased - next game expectation
    "value_form": 1.2,                         # Reduced - value less important
    "value_season": 1.0,                       # Reduced
    "expected_goals": 2.8,                     # Slightly increased
    "expected_assists": 2.3,                   # Slightly increased
    "expected_goal_involvements": 2.8,         # Slightly increased
    "expected_goals_per_90": 1.7,              # Reduced - per90 less relevant
    "expected_assists_per_90": 1.3,            # Reduced
    "expected_goal_involvements_per_90": 1.7,  # Reduced
    "ict_index": 1.2,                          # Reduced - underlying stats less predictive
    "influence": 0.8,                          # Reduced
    "creativity": 0.8,                         # Reduced
    "threat": 1.2,                             # Reduced
    "clean_sheets": 3.0,                       # Increased - fixture-dependent
    "clean_sheets_per_90": 1.3,                # Reduced
    "saves": 2.3,                              # Slightly increased - GK returns
    "saves_per_90": 2.3,                       # Slightly increased
    "penalties_saved": 1.0,   
    "goals_conceded": -2.5,                    # Increased - avoid bad fixtures
    "goals_conceded_per_90": -2.5,             # Increased
    "expected_goals_conceded": -2.0,           # Increased - fixture difficulty
    "expected_goals_conceded_per_90": -2.0,    # Increased
    # multipliers (keep at 0)
    "team_strength": 0.0,
    "team_fix_dif": 0.0,
    "chance_of_playing_next_round": 0.0
}

