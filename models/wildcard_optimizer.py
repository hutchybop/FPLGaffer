from collections import Counter

try:
    from pulp import (
        LpBinary,
        LpMaximize,
        LpProblem,
        LpStatus,
        LpVariable,
        PULP_CBC_CMD,
        lpSum,
    )

    HAS_PULP = True
except Exception:
    HAS_PULP = False


def _safe_float(value):
    """Convert value to float safely."""
    try:
        return float(value)
    except Exception:
        return 0.0


def _objective_score(player):
    """Composite wildcard objective score for optimization."""
    rating = _safe_float(player.get("rating", 0.0))
    ep_next = _safe_float(player.get("ep_next", 0.0))
    form = _safe_float(player.get("form", 0.0))
    points_per_game = _safe_float(player.get("points_per_game", 0.0))
    return rating + (1.2 * ep_next) + (0.8 * form) + (0.3 * points_per_game)


def _solve_wildcard(players, budget_limit, min_spend):
    """Solve a single wildcard optimization run with a spend floor."""
    if not players:
        return None

    budget_units = int(round(_safe_float(budget_limit) * 10))
    min_spend_units = int(round(max(0.0, _safe_float(min_spend)) * 10))

    problem = LpProblem("wildcard_squad", LpMaximize)

    x = {
        p["id"]: LpVariable(f"x_{p['id']}", lowBound=0, upBound=1, cat=LpBinary)
        for p in players
    }

    problem += lpSum(x[p["id"]] * p["objective_score"] for p in players)

    problem += lpSum(x[p["id"]] for p in players) == 15

    for pos, expected_count in {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}.items():
        problem += (
            lpSum(x[p["id"]] for p in players if p.get("pos") == pos) == expected_count
        )

    teams = sorted({p.get("team_name", "") for p in players})
    for team in teams:
        if not team:
            continue
        problem += lpSum(x[p["id"]] for p in players if p.get("team_name") == team) <= 3

    problem += lpSum(x[p["id"]] * p["cost_units"] for p in players) <= budget_units
    if min_spend_units > 0:
        problem += (
            lpSum(x[p["id"]] * p["cost_units"] for p in players) >= min_spend_units
        )

    status_code = problem.solve(PULP_CBC_CMD(msg=False))
    status = LpStatus.get(status_code, "Unknown")
    if status != "Optimal":
        return None

    selected = [p for p in players if x[p["id"]].value() == 1]
    total_cost = round(sum(p["cost_units"] for p in selected) / 10.0, 1)
    total_objective = round(sum(p["objective_score"] for p in selected), 2)

    return {
        "squad": selected,
        "total_cost": total_cost,
        "budget_left": round(_safe_float(budget_limit) - total_cost, 1),
        "objective_score": total_objective,
        "min_spend_used": round(min_spend_units / 10.0, 1),
    }


def _exclusion_reason(player, selected, selected_team_counts):
    """Heuristic reason why an excluded player is not in selected squad."""
    team = player.get("team_name", "")
    pos = player.get("pos", "")

    if selected_team_counts.get(team, 0) >= 3:
        return f"team cap reached for {team}"

    selected_same_pos = [p for p in selected if p.get("pos") == pos]
    if selected_same_pos:
        min_score = min(p.get("objective_score", 0.0) for p in selected_same_pos)
        if player.get("objective_score", 0.0) <= min_score:
            return f"lower objective score than selected {pos} players"

    return "excluded by combined budget/formation constraints"


def _top_excluded(players, selected, count=5):
    """Return top excluded players by objective score with heuristic reasons."""
    selected_ids = {p["id"] for p in selected}
    selected_team_counts = Counter(p.get("team_name", "") for p in selected)

    excluded = [p for p in players if p["id"] not in selected_ids]
    excluded.sort(key=lambda p: p.get("objective_score", 0.0), reverse=True)

    top = []
    for player in excluded[:count]:
        top.append(
            {
                "name": player.get("web_name", ""),
                "team": player.get("team_name", ""),
                "pos": player.get("pos", ""),
                "cost": player.get("now_cost(m)", 0.0),
                "rating": round(_safe_float(player.get("rating", 0.0)), 2),
                "objective_score": round(player.get("objective_score", 0.0), 2),
                "reason": _exclusion_reason(player, selected, selected_team_counts),
            }
        )
    return top


def optimize_wildcard_squad(wildcard_pool, budget_limit, min_spend_gap=2.0):
    """
    Optimize wildcard squad deterministically with hard FPL constraints.
    Args:
        wildcard_pool: dict containing candidate players per position
        budget_limit: float budget cap
        min_spend_gap: float max budget left unused (budget - spend floor)
    Returns:
        dict: optimization result with squad, costs, and diagnostics
    """
    if not HAS_PULP:
        return {
            "valid": False,
            "errors": [
                "PuLP is not installed. "
                "Add 'pulp' dependency to enable wildcard optimizer."
            ],
        }

    raw_players = [p for players in wildcard_pool.values() for p in players]
    players = []
    seen_ids = set()
    for player in raw_players:
        pid = player.get("id")
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        prepared = player.copy()
        prepared["objective_score"] = _objective_score(prepared)
        prepared["cost_units"] = int(
            round(_safe_float(prepared.get("now_cost(m)", 0.0)) * 10)
        )
        players.append(prepared)

    if len(players) < 15:
        return {
            "valid": False,
            "errors": [
                f"Candidate pool too small: only {len(players)} unique players."
            ],
        }

    budget_limit = _safe_float(budget_limit)
    min_spend_floor = max(0.0, budget_limit - _safe_float(min_spend_gap))

    best = _solve_wildcard(players, budget_limit, min_spend_floor)

    if not best:
        relaxed = _solve_wildcard(players, budget_limit, 0.0)
        if not relaxed:
            return {
                "valid": False,
                "errors": [
                    "No feasible wildcard squad found for "
                    "this budget and candidate pool."
                ],
            }
        best = relaxed
        best["fallback"] = "spend_floor_relaxed"

    if best["budget_left"] > 4.0:
        tighter_floor = max(0.0, budget_limit - 1.5)
        tighter = _solve_wildcard(players, budget_limit, tighter_floor)
        if tighter:
            best = tighter
            best["fallback"] = "tightened_spend_floor"

    selected = best["squad"]
    top_excluded = _top_excluded(players, selected, count=5)

    return {
        "valid": True,
        "errors": [],
        "squad": selected,
        "selected_ids": [p["id"] for p in selected],
        "total_cost": best["total_cost"],
        "budget_left": best["budget_left"],
        "objective_score": best["objective_score"],
        "min_spend_used": best.get("min_spend_used", 0.0),
        "fallback": best.get("fallback", ""),
        "top_excluded": top_excluded,
    }


def format_optimizer_diagnostics(result, budget_limit):
    """Format deterministic optimizer diagnostics for report output."""
    lines = [
        f"Budget used: £{result.get('total_cost', 0.0):.1f}m / "
        f"£{_safe_float(budget_limit):.1f}m",
        f"Budget remaining: £{result.get('budget_left', 0.0):.1f}m",
        f"Optimizer objective score: {result.get('objective_score', 0.0):.2f}",
    ]

    min_spend_used = result.get("min_spend_used", 0.0)
    if min_spend_used:
        lines.append(f"Spend floor used: £{min_spend_used:.1f}m")

    fallback = result.get("fallback")
    if fallback:
        lines.append(f"Optimizer adjustment: {fallback}")

    top_excluded = result.get("top_excluded", [])
    if top_excluded:
        lines.append("")
        lines.append("Top excluded candidates:")
        for idx, player in enumerate(top_excluded, start=1):
            lines.append(
                f"{idx}. {player['name']} ({player['pos']}, {player['team']}, "
                f"£{player['cost']}m, {player['rating']:.2f}) - {player['reason']}"
            )

    return "\n".join(lines)
