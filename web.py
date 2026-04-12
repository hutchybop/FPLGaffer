import os
import sys
import json
import re
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fpl-gaffer-secret-key")
NAV_DEADLINE_CACHE_TTL = 300
_nav_deadline_cache = {
    "timestamp": 0,
    "data": {"nav_next_gw": None, "nav_deadline": None},
}

from config import constants, settings
from ai import ai_prompt, ai_advisor, wildcard_validator
from utils import file_handlers, format_date
from models import ratings, sort, replacements, wildcard_optimizer


@app.route("/health")
def health():
    return {"status": "ok", "service": "fplgaffer"}, 200


def get_reports():
    """Get list of reports sorted by modification time (newest first)"""
    reports = []
    folder = "reports"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith(".txt"):
                path = os.path.join(folder, f)
                reports.append(
                    {
                        "filename": f,
                        "name": format_report_name(f),
                        "modified": os.path.getmtime(path),
                    }
                )
    reports.sort(key=lambda x: x["modified"], reverse=True)
    return reports


def format_report_name(filename):
    """Format report filename into a readable label for the web app."""
    transfer_match = re.match(r"^GW_(\d+)_report(?:_(\d+))?\.txt$", filename)
    if transfer_match:
        gw = transfer_match.group(1)
        run = transfer_match.group(2)
        return (
            f"Transfer Report - GW {gw} (Run {run})"
            if run
            else f"Transfer Report - GW {gw}"
        )

    wildcard_match = re.match(r"^Wildcard_report(?:_(\d+))?\.txt$", filename)
    if wildcard_match:
        run = wildcard_match.group(1)
        return f"Wildcard Report (Run {run})" if run else "Wildcard Report"

    return filename.replace("_", " ").replace(".txt", "")


def run_analysis(mode, team_id=None, num_replacements=4, team_cost=100):
    """Run the FPL analysis and return results"""
    if team_id:
        os.environ["FPL_TEAM_ID"] = team_id

    import io
    from contextlib import redirect_stdout

    captured = io.StringIO()
    with redirect_stdout(captured):
        API_KEY, client = settings.ai_client()

    bootstrap_data = settings.fetch_bootstrap_data()
    players = settings.format_all_players(bootstrap_data)
    gw_current = settings.get_current_gameweek(bootstrap_data)
    next_event = settings.get_next_gameweek_event(bootstrap_data)
    transfer_target_gw = next_event.get("id", gw_current + 1)
    bank, picks_pids = settings.my_picks(gw_current)

    if mode == "transfer":
        weights, base_name = (
            constants.TRANSFER_WEIGHTS,
            f"GW_{transfer_target_gw}_report",
        )
        report_gw = transfer_target_gw
    else:
        weights, base_name = constants.WC_WEIGHTS, "Wildcard_report"
        report_gw = gw_current

    filename = file_handlers.get_unique_filename(base_name)
    f = open(filename, "w")
    original_stdout = sys.stdout
    sys.stdout = file_handlers.Tee(sys.stdout, f)

    players = ratings.compute_ml_ratings(players, weights, mode)
    sorted_players = sort.sort_players(players)
    sorted_current = sort.sort_current_team(sorted_players, picks_pids)

    # Print analysis output to report file
    from utils import print_output

    if mode == "transfer":
        print(f"\n{'=' * 60}")
        print(f"TRANSFER MODE ({format_date.format_date_with_ordinal()})")
        print(f"{'=' * 60}")
        print(f"\n{'=' * 60}")
        print("FPL TEAM ASSESSMENT")
        print(f"{'=' * 60}")
        print("Players sorted by performance score (lowest to highest)")
        print(f"BANK: £{bank}m\n")
        print_output.print_players(sorted_current)

        if num_replacements > 0:
            print(f"\n{'=' * 60}")
            print(f"REPLACEMENT SUGGESTIONS FOR {num_replacements} PLAYERS")
            print(f"{'=' * 60}")
            for player in sorted_current[:num_replacements]:
                candidates = replacements.find_replacements(
                    player, bank, sorted_players, sorted_current
                )
                player_name = player.get("web_name", "")
                player_pos = player.get("pos", "")
                player_cost = player.get("now_cost(m)", "")
                player_rating = player.get("rating", "")
                player_team = player.get("team_name", "")
                print(f"\n{'=' * 60}")
                print(
                    f"REPLACEMENT OPTIONS FOR: {player_name} - {player_team} "
                    f"({player_pos}, £{player_cost}m, Rating: {player_rating})"
                )
                print(f"{'=' * 60}")
                if candidates:
                    print_output.print_players(candidates)
                    print_output.print_replacement_impact(player, candidates)
    else:
        print(f"\n{'=' * 60}")
        print(f"WILDCARD MODE ({format_date.format_date_with_ordinal()})")
        print(f"{'=' * 60}")
        print(f"Total Team Value: £{team_cost}m\n")

        wildcard_trimmed = {
            "GKP": sorted_players["GKP"][: constants.WILDCARD_POOL_GKP],
            "DEF": sorted_players["DEF"][: constants.WILDCARD_POOL_DEF],
            "MID": sorted_players["MID"][: constants.WILDCARD_POOL_MID],
            "FWD": sorted_players["FWD"][: constants.WILDCARD_POOL_FWD],
        }

        positions = [
            ("TOP GOALKEEPERS", "GKP"),
            ("TOP DEFENDERS", "DEF"),
            ("TOP MIDFIELDERS", "MID"),
            ("TOP FORWARDS", "FWD"),
        ]

        for title, position in positions:
            print(f"\n{'=' * 60}")
            print(title)
            print(f"{'=' * 60}")
            print_output.print_players(wildcard_trimmed[position])

    print(f"\n{'=' * 60}")
    print("AI Response")
    print(f"{'=' * 60}")

    AI_PROMPT = ""
    ai_response = ""
    ai_error = None

    try:
        if mode == "transfer":
            AI_PROMPT = process_transfers(bank, sorted_players, sorted_current)
            transfer_prompt = ai_prompt.ai_transfer_prompt()
            ai_response = ai_advisor.ai_fpl_helper(
                AI_PROMPT, transfer_prompt, client, API_KEY
            )
        else:
            AI_PROMPT, wildcard_pool = process_wildcard(sorted_players)
            optimization = wildcard_optimizer.optimize_wildcard_squad(
                wildcard_pool,
                team_cost,
                constants.WILDCARD_MIN_SPEND_GAP,
            )

            if not optimization.get("valid"):
                joined_errors = "\n".join(optimization.get("errors", []))
                ai_response = (
                    "AI Error: Could not build a valid wildcard squad with optimizer.\n"
                    f"{joined_errors}"
                )
            else:
                base_output = wildcard_validator.format_validated_wildcard_response(
                    optimization["squad"],
                    optimization["total_cost"],
                    team_cost,
                )
                diagnostics = wildcard_optimizer.format_optimizer_diagnostics(
                    optimization,
                    team_cost,
                )
                ai_response = f"{base_output}\n\nDiagnostics:\n{diagnostics}"

                if API_KEY and client:
                    explain_prompt = ai_prompt.ai_wildcard_explain_prompt(team_cost)
                    explain_payload = {
                        "budget_limit": team_cost,
                        "selected_squad": [
                            {
                                "id": p.get("id"),
                                "name": p.get("web_name"),
                                "team": p.get("team_name"),
                                "pos": p.get("pos"),
                                "cost": p.get("now_cost(m)"),
                                "rating": p.get("rating"),
                                "form": p.get("form"),
                                "ep_next": p.get("ep_next"),
                                "minutes": p.get("minutes"),
                            }
                            for p in optimization["squad"]
                        ],
                        "diagnostics": {
                            "total_cost": optimization.get("total_cost"),
                            "budget_left": optimization.get("budget_left"),
                            "objective_score": optimization.get("objective_score"),
                        },
                        "top_excluded": optimization.get("top_excluded", []),
                    }
                    explain_input = json.dumps(
                        explain_payload,
                        ensure_ascii=False,
                        indent=2,
                    )
                    explanation = ai_advisor.ai_fpl_helper(
                        explain_input,
                        explain_prompt,
                        client,
                        API_KEY,
                    )
                    if explanation and not explanation.startswith("AI Error:"):
                        ai_response = f"{ai_response}\n\nAI Notes:\n{explanation}"
                    else:
                        ai_response = (
                            f"{ai_response}\n\nAI Notes:\n"
                            "AI explanation unavailable for this run."
                        )
    except Exception as e:
        ai_error = str(e)
        ai_response = f"AI Error: {ai_error}"
    finally:
        if ai_response:
            print(ai_response)
        sys.stdout = original_stdout
        f.close()

    return {
        "filename": os.path.basename(filename),
        "mode": mode,
        "gw": report_gw,
        "bank": bank,
        "ai_response": ai_response,
    }


@app.context_processor
def inject_next_deadline():
    """Inject next gameweek and transfer deadline into all templates."""
    now = time.time()
    if now - _nav_deadline_cache["timestamp"] < NAV_DEADLINE_CACHE_TTL:
        return _nav_deadline_cache["data"]

    try:
        bootstrap_data = settings.fetch_bootstrap_data()
        next_event = settings.get_next_gameweek_event(bootstrap_data)
        next_gw = next_event.get("id")
        deadline = format_date.format_uk_deadline(next_event.get("deadline_time"))
        data = {
            "nav_next_gw": next_gw,
            "nav_deadline": deadline,
        }
        _nav_deadline_cache["timestamp"] = now
        _nav_deadline_cache["data"] = data
        return data
    except Exception:
        data = {
            "nav_next_gw": None,
            "nav_deadline": None,
        }
        _nav_deadline_cache["timestamp"] = now
        _nav_deadline_cache["data"] = data
        return data


def process_transfers(bank, sorted_players, sorted_current):
    """Process transfer mode and return AI prompt"""
    transfers_full = {}
    for player in sorted_current:
        candidates = replacements.find_replacements(
            player, bank, sorted_players, sorted_current
        )
        transfers_full[player.get("web_name", "")] = {
            "current": player,
            "candidates": candidates,
        }
    return json.dumps(transfers_full, ensure_ascii=False, indent=2)


def process_wildcard(sorted_players):
    """Build wildcard candidate pool and serialized payload."""
    wildcard_trimmed = {
        "GKP": sorted_players["GKP"][: constants.WILDCARD_POOL_GKP],
        "DEF": sorted_players["DEF"][: constants.WILDCARD_POOL_DEF],
        "MID": sorted_players["MID"][: constants.WILDCARD_POOL_MID],
        "FWD": sorted_players["FWD"][: constants.WILDCARD_POOL_FWD],
    }
    return json.dumps(wildcard_trimmed, ensure_ascii=False, indent=2), wildcard_trimmed


def parse_report_content(content):
    """Parse report text content into structured data for display"""
    lines = content.split("\n")
    sections = []

    # Detect mode
    is_wildcard = "WILDCARD MODE" in content

    if is_wildcard:
        # Wildcard mode parsing
        current_section = {"title": "", "tables": [], "ai_response": ""}
        table_data = []
        headers = []
        in_table = False

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped or "+" in line_stripped:
                continue

            # Top players sections
            if any(
                x in line_stripped
                for x in [
                    "TOP GOALKEEPERS",
                    "TOP DEFENDERS",
                    "TOP MIDFIELDERS",
                    "TOP FORWARDS",
                ]
            ):
                if table_data and headers:
                    current_section["tables"].append(
                        {"headers": headers, "rows": table_data}
                    )
                    sections.append(current_section)
                current_section = {
                    "title": line_stripped,
                    "tables": [],
                    "ai_response": "",
                }
                table_data = []
                headers = []
                in_table = False
            # AI Response
            elif "AI Response" in line_stripped:
                if table_data and headers:
                    current_section["tables"].append(
                        {"headers": headers, "rows": table_data}
                    )
                    table_data = []
                    headers = []
                if current_section.get("tables"):
                    sections.append(current_section)
                current_section = {
                    "title": "AI Recommendations",
                    "tables": [],
                    "ai_response": "",
                }
                in_table = False
            # Parse table rows
            elif "|" in line_stripped:
                parts = [p.strip() for p in line_stripped.split("|") if p.strip()]
                if parts and len(parts) > 1:
                    if "Name" in parts:
                        headers = parts
                        in_table = True
                    elif in_table:
                        table_data.append(parts)
            # AI response text
            elif current_section.get("title") == "AI Recommendations":
                current_section["ai_response"] += line_stripped + "\n"

        # Add last section
        if table_data and headers:
            current_section["tables"].append({"headers": headers, "rows": table_data})
        if current_section.get("tables") or current_section.get("ai_response"):
            sections.append(current_section)

    else:
        # Transfer mode parsing (original logic)
        current_team = {"title": "My Team", "tables": [], "replacements": []}
        ai_response = ""

        in_current_team = False
        in_ai_section = False
        current_replacement = None
        table_data = []
        headers = []

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped or "+" in line_stripped:
                continue

            if "TRANSFER MODE" in line_stripped:
                in_current_team = True
                in_ai_section = False
            elif "FPL TEAM ASSESSMENT" in line_stripped:
                in_current_team = True
                in_ai_section = False
                table_data = []
                headers = []
            elif "REPLACEMENT SUGGESTIONS" in line_stripped:
                if table_data and headers:
                    current_team["tables"].append(
                        {"headers": headers, "rows": table_data}
                    )
                    table_data = []
                    headers = []
                in_current_team = False
            elif "REPLACEMENT OPTIONS FOR" in line_stripped:
                if current_replacement and current_replacement.get("tables"):
                    sections.append(current_replacement)

                player_name = line_stripped.replace(
                    "REPLACEMENT OPTIONS FOR:", ""
                ).strip()
                current_replacement = {
                    "title": f"Replace: {player_name}",
                    "tables": [],
                    "recommendations": "",
                    "type": "replacement",
                }
                table_data = []
                headers = []
                in_ai_section = False
            elif "AI Response" in line_stripped:
                if current_replacement and current_replacement.get("tables"):
                    sections.append(current_replacement)
                    current_replacement = None
                in_ai_section = True
                in_current_team = False
            elif "|" in line_stripped:
                parts = [p.strip() for p in line_stripped.split("|") if p.strip()]
                if parts and len(parts) > 1:
                    if "Name" in parts:
                        headers = parts
                    else:
                        if current_replacement is not None:
                            current_replacement["tables"].append(
                                {"headers": headers, "rows": [parts]}
                            )
                        elif in_current_team:
                            table_data.append(parts)
            elif (
                line_stripped
                and len(line_stripped) > 2
                and line_stripped[0].isdigit()
                and "." in line_stripped[:3]
            ):
                if current_replacement:
                    current_replacement["recommendations"] += line_stripped + "\n"
            elif in_ai_section:
                ai_response += line_stripped + "\n"

        if current_team.get("tables"):
            sections.insert(0, current_team)

        if current_replacement and current_replacement.get("tables"):
            sections.append(current_replacement)

    # Add AI response for transfer mode
    if not is_wildcard:
        ai_clean = "\n".join(
            line
            for line in ai_response.strip().split("\n")
            if not line.strip().startswith("=")
        )
        if ai_clean.strip():
            sections.append(
                {
                    "title": "AI Recommendations",
                    "tables": [],
                    "ai_response": ai_clean.strip(),
                }
            )

    # Handle case where report has no sections
    if not sections:
        sections = [{"title": "Report", "tables": [], "ai_response": content}]

    return sections


@app.route("/")
def index():
    reports = get_reports()
    team_id = constants.TEAM_ID or ""
    return render_template("index.html", reports=reports, team_id=team_id)


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="favicons/favicon.ico"))


@app.route("/analyze", methods=["POST"])
def analyze():
    mode = request.form.get("mode", "transfer")
    team_id = request.form.get("team_id", "")
    num_replacements = int(request.form.get("num_replacements", 4))
    team_cost = float(request.form.get("team_cost", 100))

    try:
        result = run_analysis(
            mode, team_id if team_id else None, num_replacements, team_cost
        )
        session["current_result"] = result
        # Redirect directly to view the new report
        return redirect(url_for("view_report", filename=result["filename"]))
    except Exception as e:
        flash(f"Error running analysis: {str(e)}", "danger")
        return redirect(url_for("index"))


@app.route("/results")
def results():
    result = session.get("current_result")
    if not result:
        flash("No analysis results found. Please run an analysis first.", "warning")
        return redirect(url_for("index"))
    result["display_name"] = format_report_name(result["filename"])
    return render_template("results.html", result=result)


@app.route("/report/<filename>")
def view_report(filename):
    folder = "reports"
    filepath = os.path.join(folder, filename)
    if not os.path.exists(filepath):
        flash("Report not found", "danger")
        return redirect(url_for("index"))

    with open(filepath, "r") as f:
        content = f.read()

    sections = parse_report_content(content)
    display_name = format_report_name(filename)
    return render_template(
        "view_report.html",
        filename=filename,
        display_name=display_name,
        sections=sections,
    )


@app.route("/delete/<filename>")
def delete_report(filename):
    folder = "reports"
    filepath = os.path.join(folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Report {filename} deleted successfully", "success")
    else:
        flash("Report not found", "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3006")), debug=True)
