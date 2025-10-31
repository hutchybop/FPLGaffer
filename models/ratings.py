def compute_generic_rating(players, ranges, attribute_weights):
    """
    Compute player rating (0-1000) based on attributes and weights.
    Args:
        player: dict (format_all_players)
        ranges: dict mapping attribute -> {"min": x, "max": y} (build_attribute_ranges)
        attribute_weights: dict of weights for each attribute (ATTRIBUTE_WEIGHTS)
    Returns: 
        rating: num (0..1000)
    """
    def safe_float(value, default=0.0):
        """Safely convert value to float."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def normalize(value, min_val, max_val):
        """Normalize value to 0-1 range."""
        val = safe_float(value)
        if max_val == min_val:
            # if no spread, treat as 0
            return 0.0
        return max(0.0, min(1.0, (val - min_val) / (max_val - min_val)))
    
    for player in players:
        # Calculate base score from attributes
        numerator = 0.0
        pos_weight_sum = 0.0
        neg_weight_sum = 0.0
        # Iterate over each attribute  in ranges
        for key, r in ranges.items():
            # skip anything explicitly non-numeric/meta if present
            weight = attribute_weights.get(key, 1.0)  # default 1.0 if not explicitly defined
            # skip attributes intended as multipliers
            if weight == 0.0:
                continue
            norm = normalize(player.get(key), r["min"], r["max"])
            numerator += norm * weight
            if weight > 0:
                pos_weight_sum += weight
            else:
                neg_weight_sum += abs(weight)
        # Calculate base score
        total_weight_span = pos_weight_sum + neg_weight_sum
        if total_weight_span == 0:
            base_score = 0.0
        else:
            min_possible = -neg_weight_sum
            max_possible = pos_weight_sum
            if max_possible - min_possible == 0:
                base_score = 0.0
            else:
                base_score = (numerator - min_possible) / (max_possible - min_possible)
                base_score = max(0.0, min(1.0, base_score))
        # Availability multiplier (use chance_of_playing_next_round as multiplier)
        availability = safe_float(player.get("chance_of_playing_next_round") or 100.0) / 100.0
        # Fixture difficulty adjustment (assume 1..5 where lower is easier)
        fix_dif = safe_float(player.get("team_fix_dif", 2.5))
        fixture_factor = 1.0 + (2.5 - fix_dif) * 0.05  # easier fixtures => small boost
        # Team strength adjustment (small boost)
        team_strength = safe_float(player.get("team_strength", 100.0))
        # Convert team_strength 1-5 scale to 100-based
        if team_strength <= 10:
            team_strength_scaled = 100.0 + (team_strength - 3.0) * 5.0  # small conversion heuristic
        else:
            team_strength_scaled = team_strength
        team_factor = 1.0 + (team_strength_scaled - 100.0) / 1000.0
        # Final rating scaled to 0..1000
        rating = base_score * availability * fixture_factor * team_factor * 1000.0
        # After calculating normalized_rating remove rating
        player["rating"] = round(rating, 2)
    return players


def compute_normalized_rating(players):
    # Normalize player ratings from 0 to 100 and add to player dicts
    min_rating = min(p["rating"] for p in players)
    max_rating = max(p["rating"] for p in players)
    for player in players:
        normalized = ((player["rating"] - min_rating) / (max_rating - min_rating)) * 100
        player["normalized_rating"] = round(normalized, 2)
        player.pop("rating", None)
    return players