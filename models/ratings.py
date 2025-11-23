import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, QuantileTransformer, RobustScaler
from pprint import pprint


def compute_ml_ratings(players, attribute_weights):
    """
    Compute player ratings using ML scaling + weighted sum.
    Returns players with player["rating"] (0–100 float).
    """

    # ----- Helper functions -----
    def safe_float(v):
        try:
            return float(v)
        except:
            return 0.0

    # ----- Convert to DataFrame -----
    df = pd.DataFrame(players)

    # Keep only attributes that appear in weights that are not 0.0
    numeric_attrs = [
        a for a, w in attribute_weights.items()
        if a in df.columns and float(w) != 0.0
    ]

    # Convert numeric columns safely
    for col in numeric_attrs:
        df[col] = df[col].apply(safe_float)

    # ----- QuantileTransformer -----
    # Add small noise to separate same values
    df[numeric_attrs] += np.random.normal(0, 1e-5, df[numeric_attrs].shape)
    # Choose smooth quantile resolution
    n_quantiles = min(200, len(players))
    scaler = QuantileTransformer(
        output_distribution="uniform",
        n_quantiles=n_quantiles,
        subsample=50000,
        random_state=0
    )
    scaled_values = scaler.fit_transform(df[numeric_attrs])
    scaled_df = pd.DataFrame(scaled_values, columns=numeric_attrs)


    # ----- Apply weights -----
    weighted_scores = np.zeros(len(df))
    total_positive_weight = sum(w for w in attribute_weights.values() if w > 0)
    total_negative_weight = sum(abs(w) for w in attribute_weights.values() if w < 0)

    for attr in numeric_attrs:
        w = attribute_weights.get(attr, 0)
        if w != 0:
            weighted_scores += scaled_df[attr] * w

    # Normalize weighted sum to 0–1 range
    if (total_positive_weight + total_negative_weight) > 0:
        min_possible = -total_negative_weight
        max_possible = total_positive_weight
        normalized = (weighted_scores - min_possible) / (max_possible - min_possible)
        normalized = np.clip(normalized, 0, 1)
    else:
        normalized = np.zeros(len(df))

    # ----- Apply multipliers -----
    availability = df["chance_of_playing_next_round"].apply(
        lambda v: safe_float(v) / 100 if v not in ("", None) else 1.0
    ).values

    df["team_fix_dif"] = df["team_fix_dif"].apply(safe_float)
    fix_factor = 1.0 + (2.5 - df["team_fix_dif"]) * 0.05
    strength = df["team_strength"].apply(safe_float)

    # Convert FPL team strength numbers (1–5) to 100 baseline
    strength_scaled = 1.0 + ((strength - 100) / 1000.0)

    # Calculated final score
    final_scores = normalized * availability * fix_factor.values * strength_scaled.values
    
    # ----- Final rating 0–100 -----
    mini = final_scores.min()
    maxi = final_scores.max()
    final_scores = (final_scores - mini) / (maxi - mini)
    final_scores = np.clip(final_scores * 100, 0, 100)

    # Insert rating back into players dict
    for p, score in zip(players, final_scores):
        p["rating"] = round(float(score), 2)

    return players
