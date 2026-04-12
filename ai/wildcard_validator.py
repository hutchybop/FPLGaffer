import json
import ast
import re
from collections import Counter

ID_LIST_KEYS = {
    "selected_player_ids",
    "player_ids",
    "selected_ids",
    "ids",
}

PLAYER_CONTAINER_KEYS = {
    "selected_players",
    "players",
    "squad",
    "lineup",
    "team",
    "selection",
}


def _safe_int(value):
    """Convert value to int when possible, otherwise return None."""
    try:
        return int(value)
    except Exception:
        return None


def _extract_ids_from_value(value):
    """Extract player IDs from nested dict/list payload structures."""
    if isinstance(value, list):
        ids = []
        for item in value:
            ids.extend(_extract_ids_from_value(item))
        return ids

    if isinstance(value, dict):
        ids = []

        # 1) Direct id list keys (preferred)
        for key in ID_LIST_KEYS:
            if key in value and isinstance(value[key], list):
                for item in value[key]:
                    if isinstance(item, dict):
                        item_id = _safe_int(item.get("id"))
                        if item_id is not None:
                            ids.append(item_id)
                    else:
                        item_id = _safe_int(item)
                        if item_id is not None:
                            ids.append(item_id)
                if ids:
                    return ids

        # 2) Direct player container keys (list of player objects)
        for key in PLAYER_CONTAINER_KEYS:
            if key in value:
                ids.extend(_extract_ids_from_value(value[key]))
        if ids:
            return ids

        # 3) Single player object
        if "id" in value:
            direct_id = _safe_int(value.get("id"))
            if direct_id is not None:
                ids.append(direct_id)

        # 4) Generic nested scan: recurse only into nested list/dict values
        for nested_value in value.values():
            if isinstance(nested_value, (list, dict)):
                ids.extend(_extract_ids_from_value(nested_value))

        return ids

    return []


def _extract_json_object(text):
    """
    Extract first JSON object or array from an AI response.
    Args:
        text: raw response text
    Returns:
        str: extracted JSON string or empty string
    """
    if not text:
        return ""

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")
    array_start = cleaned.find("[")
    array_end = cleaned.rfind("]")

    candidates = []
    if object_start != -1 and object_end != -1 and object_end > object_start:
        candidates.append((object_start, object_end))
    if array_start != -1 and array_end != -1 and array_end > array_start:
        candidates.append((array_start, array_end))

    if not candidates:
        return ""

    start, end = min(candidates, key=lambda x: x[0])
    return cleaned[start : end + 1]


def parse_selected_player_ids(response_text):
    """
    Parse selected player IDs from wildcard AI response.
    Args:
        response_text: AI response text expected to contain JSON
    Returns:
        tuple: (player_ids, error_message)
    """
    json_text = _extract_json_object(response_text)
    if not json_text:
        return [], "Response did not contain a JSON object"

    payload = None
    json_error = ""
    try:
        payload = json.loads(json_text)
    except Exception as exc:
        json_error = str(exc)

    if payload is None:
        # Fallback for Python-style dict output (single quotes)
        try:
            parsed_literal = ast.literal_eval(json_text)
            if isinstance(parsed_literal, dict):
                payload = parsed_literal
        except Exception:
            payload = None

    if payload is None:
        # Final fallback: pull ids from selected_player_ids array text
        match = re.search(
            r"selected_player_ids\s*[:=]\s*\[(.*?)\]", response_text, re.DOTALL
        )
        if match:
            nums = re.findall(r"\d+", match.group(1))
            if nums:
                return [int(n) for n in nums], ""

    if payload is None:
        return [], (
            "Invalid JSON response: "
            f"{json_error or 'Could not parse selected_player_ids'}"
        )

    if isinstance(payload, dict) and "error" in payload:
        return [], f"Model/API returned error payload: {payload.get('error')}"

    ids = _extract_ids_from_value(payload)
    if not ids:
        available_keys = []
        if isinstance(payload, dict):
            available_keys = list(payload.keys())
        return [], (
            "Response did not contain usable player IDs. "
            "Expected selected_player_ids or player objects with id fields. "
            f"Top-level keys: {available_keys}"
        )

    parsed_ids = []
    for pid in ids:
        try:
            parsed_ids.append(int(pid))
        except Exception:
            return [], f"Invalid player id value: {pid}"
    return parsed_ids, ""


def validate_wildcard_selection(player_ids, wildcard_pool, budget_limit):
    """
    Validate wildcard squad constraints and return structured results.
    Args:
        player_ids: list of selected player ids
        wildcard_pool: dict of available players grouped by position
        budget_limit: float budget cap
    Returns:
        dict: validation result including errors, squad, and total cost
    """
    all_players = [p for players in wildcard_pool.values() for p in players]
    by_id = {int(p["id"]): p for p in all_players}

    errors = []
    if len(player_ids) != 15:
        errors.append(f"Expected 15 players, got {len(player_ids)}")

    duplicates = [pid for pid, count in Counter(player_ids).items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate player ids found: {duplicates}")

    missing = [pid for pid in player_ids if pid not in by_id]
    if missing:
        errors.append(f"Player ids not in candidate pool: {missing}")

    squad = [by_id[pid] for pid in player_ids if pid in by_id]
    if len(squad) != 15:
        return {
            "valid": False,
            "errors": errors or ["Could not map all selected ids to players"],
            "squad": squad,
            "total_cost": 0.0,
        }

    pos_counts = Counter(p.get("pos", "") for p in squad)
    expected = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
    for pos, expected_count in expected.items():
        if pos_counts.get(pos, 0) != expected_count:
            errors.append(
                f"Position count invalid for {pos}: expected {expected_count}, "
                f"got {pos_counts.get(pos, 0)}"
            )

    team_counts = Counter(p.get("team_name", "") for p in squad)
    over_team_limit = [
        f"{team}={count}" for team, count in team_counts.items() if count > 3
    ]
    if over_team_limit:
        errors.append(f"Team limit exceeded: {', '.join(over_team_limit)}")

    total_cost = round(sum(float(p.get("now_cost(m)", 0.0)) for p in squad), 1)
    if total_cost > float(budget_limit):
        errors.append(
            f"Budget exceeded: total £{total_cost}m > "
            f"budget £{float(budget_limit):.1f}m"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "squad": squad,
        "total_cost": total_cost,
    }


def format_validated_wildcard_response(squad, total_cost, budget_limit):
    """
    Format validated wildcard squad as plain text for reports/UI.
    Args:
        squad: list of validated player dicts
        total_cost: float total squad cost
        budget_limit: float budget cap
    Returns:
        str: formatted wildcard recommendation text
    """
    by_pos = {"GKP": [], "DEF": [], "MID": [], "FWD": []}
    for player in squad:
        by_pos[player.get("pos", "")].append(player)

    for pos in by_pos:
        by_pos[pos] = sorted(
            by_pos[pos], key=lambda p: p.get("rating", 0), reverse=True
        )

    lines = [
        f"Total cost: £{total_cost:.1f}m (Budget: £{float(budget_limit):.1f}m)",
        "",
        "Squad:",
    ]

    for pos, expected in [("GKP", 2), ("DEF", 5), ("MID", 5), ("FWD", 3)]:
        for idx, player in enumerate(by_pos[pos], start=1):
            try:
                rating_text = f"{float(player.get('rating', 0.0)):.2f}"
            except Exception:
                rating_text = "0.00"
            lines.append(
                f"{pos}({idx}/{expected}) {player.get('web_name', '')} "
                f"({player.get('team_name', '')}, £{player.get('now_cost(m)', 0)}m, "
                f"{rating_text})"
            )

    return "\n".join(lines)


def build_repair_prompt(original_prompt, previous_response, validation_errors):
    """
    Build a repair prompt when wildcard output fails validation.
    Args:
        original_prompt: original wildcard JSON prompt
        previous_response: previous invalid model response
        validation_errors: list of validation error strings
    Returns:
        str: retry prompt requesting corrected JSON
    """
    joined_errors = "\n".join(f"- {err}" for err in validation_errors)
    return (
        "Your previous response was invalid. "
        "Fix it and respond with valid JSON only.\n\n"
        "Validation errors:\n"
        f"{joined_errors}\n\n"
        "Return this exact schema:\n"
        '{"selected_player_ids": [15 unique player ids]}\n\n'
        "Previous invalid response:\n"
        f"{previous_response}\n\n"
        "Candidate data:\n"
        f"{original_prompt}"
    )
