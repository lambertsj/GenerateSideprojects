import json
from datetime import datetime
from pathlib import Path

LABELS = {
    "en": {
        "title_run": "Side-project ideas — run {run}", "title_all": "Side-project ideas — all runs",
        "counts": "Generated: {n} · candidates: {c} · killed: {k}",
        "intro": "Candidates are hypotheses. Gates 4 and 5 require real conversations and a real payment.\n"
                 "Put at least two candidates side by side before choosing.",
        "profile": "Founder profile", "candidates": "Candidates", "none": "_No candidates in this run._",
        "killed": "Killed", "unfinished": "Unfinished",
        "description": "Description", "customer": "Customer", "job": "Job", "mechanism": "Mechanism", "why_now": "Why now",
        "market": "Target market", "gates": "Gates", "verdict": "Verdict", "reason": "Reason",
        "spend": "Spend signal", "not_in_data": "Not in the data", "coverage": "Coverage",
        "latency": "Feedback latency", "retro": "retrospective validation", "omission": "Omission risk",
        "fit": "Founder fit", "daily": "Daily work in year 2", "weakest": "Weakest point",
        "riskiest": "Riskiest assumption", "experiment": "Cheapest experiment", "guesswork": "Guesswork",
        "field": "Field test (gates 4 and 5)", "channel": "Channel",
        "attempts": "Attempts for 10 conversations", "give_up": "Customer must give up",
        "competition": "Competition", "feature_risk": "feature risk", "angle": "Open angle",
        "failure": "Failure trace",
        "no_weak_point": "No weak point found, even after re-evaluation: distrust this verdict.",
        "prospective_only": "Only prospectively verifiable: the most important fact about this idea.",
    },
    "nl": {
        "title_run": "Sideproject-ideeën — run {run}", "title_all": "Sideproject-ideeën — alle runs",
        "counts": "Gegenereerd: {n} · kandidaten: {c} · gesneuveld: {k}",
        "intro": "Kandidaten zijn hypotheses. Gates 4 en 5 vragen echte gesprekken en een echte betaling.\n"
                 "Zet minimaal twee kandidaten naast elkaar voordat je kiest.",
        "profile": "Founderprofiel", "candidates": "Kandidaten", "none": "_Geen kandidaten in deze run._",
        "killed": "Gesneuveld", "unfinished": "Onafgerond",
        "description": "Beschrijving", "customer": "Klant", "job": "Klus", "mechanism": "Mechanisme", "why_now": "Waarom nu",
        "market": "Doelmarkt", "gates": "Gates", "verdict": "Oordeel", "reason": "Reden",
        "spend": "Bestedingssignaal", "not_in_data": "Niet in de data", "coverage": "Dekkingsgraad",
        "latency": "Feedback-latentie", "retro": "retro-valideerbaar", "omission": "Omissierisico",
        "fit": "Founder fit", "daily": "Dagtaak in jaar 2", "weakest": "Zwakste punt",
        "riskiest": "Riskiest assumption", "experiment": "Goedkoopste experiment", "guesswork": "Gokwerk",
        "field": "Veldtoets (gates 4 en 5)", "channel": "Kanaal",
        "attempts": "Pogingen voor 10 gesprekken", "give_up": "Klant moet afstaan",
        "competition": "Concurrentie", "feature_risk": "feature-risico", "angle": "Open hoek",
        "failure": "Faalspoor",
        "no_weak_point": "Geen enkel zwak punt gevonden, ook na herbeoordeling: wantrouw dit oordeel.",
        "prospective_only": "Alleen prospectief valideerbaar: het belangrijkste feit over dit idee.",
    },
}
LANG_CODES = {"english": "en", "dutch": "nl", "nederlands": "nl", "en": "en", "nl": "nl"}


def labels_for(language: str) -> dict:
    """Report headings exist in English and Dutch; other languages get English headings."""
    return LABELS[LANG_CODES.get(language.strip().lower(), "en")]


def _j(s):
    return json.loads(s) if s else {}


def _d(x):
    """Show missing values as a dash."""
    return "—" if x in (None, "", [], {}) else x


def _cell(x):
    return str(_d(x)).replace("|", "/").replace("\n", " ")


def _candidate(L, title, idea, gates, comp, warn):
    i, g, c = _j(idea), _j(gates), _j(comp)
    m, f, ff = g.get("mechanism", {}), g.get("field_test_plan", {}), g.get("founder_fit", {})
    out = [
        f"### {title}\n",
        f"_{_d(i.get('description'))}_\n",
        f"**{L['customer']}:** {_d(i.get('customer'))}  ",
        f"**{L['job']}:** {_d(i.get('job'))}  ",
        f"**{L['mechanism']}:** {_d(m.get('sentence') or i.get('mechanism'))}  ",
        f"**{L['market']}:** {_d(i.get('target_market'))}  ",
        f"**{L['why_now']}:** {_d(i.get('why_now'))}\n",
    ]
    if warn:
        out.append(f"> ⚠ {L.get(warn, warn)}\n")
    out += [f"**{L['gates']}**\n", f"| # | {L['verdict']} | {L['reason']} |", "|---|---|---|"]
    for gate in g.get("gates", []):
        out.append(f"| {_cell(gate.get('nr'))} | {_cell(gate.get('verdict'))} | {_cell(gate.get('reason'))} |")
    out += [
        "",
        f"- **{L['spend']}:** {_d(g.get('spend_signal'))}",
        f"- **{L['not_in_data']}:** {_d(m.get('not_in_data'))}",
        f"- **{L['coverage']}:** {_d(m.get('coverage'))}",
        f"- **{L['latency']}:** {_d(m.get('feedback_latency'))} · {L['retro']}: {_d(m.get('retro_validation'))}",
        f"- **{L['omission']}:** {_d(m.get('omission_risk'))}",
        f"- **{L['fit']}:** {_d(ff.get('match'))} — {_d(ff.get('explanation'))}",
        f"- **{L['daily']}:** {_d(ff.get('daily_work_year_2'))}",
        f"- **{L['weakest']}:** {_d(g.get('weakest_point'))}",
        f"- **{L['riskiest']}:** {_d(g.get('riskiest_assumption'))}",
        f"- **{L['experiment']}:** {_d(g.get('cheapest_experiment'))}",
        f"- **{L['guesswork']}:** {', '.join(g.get('guesswork', [])) or '—'}",
        "",
        f"**{L['field']}**\n",
        f"- {L['channel']}: {_d(f.get('channel'))}",
        f"- {L['attempts']}: {_d(f.get('attempts_for_10_conversations'))}",
        f"- {L['give_up']}: {_d(f.get('customer_must_give_up'))}",
        "",
        f"**{L['competition']}:** {_d(c.get('diagnosis'))} · {L['feature_risk']} {_d(c.get('feature_risk'))}  ",
        f"**{L['angle']}:** {_d(c.get('angle'))}\n",
    ]
    for k in c.get("competitors", [])[:8]:
        out.append(f"- [{_d(k.get('name'))}]({_d(k.get('url'))}) — {_d(k.get('overlap'))}, "
                   f"{_d(k.get('price'))}: {_d(k.get('note'))}")
    for t in c.get("failure_traces", [])[:4]:
        out.append(f"- {L['failure']}: [{_d(t.get('what'))}]({_d(t.get('url'))}) — {_d(t.get('lesson'))}")
    out.append("\n---\n")
    return out


def write(con, folder, language="English", run=None, profile_summary=""):
    L = labels_for(language)
    Path(folder).mkdir(parents=True, exist_ok=True)
    where, param = ("WHERE run=?", (run,)) if run else ("", ())
    name = f"ideas_{run}.md" if run else f"ideas_all_{datetime.now():%Y%m%d_%H%M}.md"
    path = Path(folder) / name

    rows = con.execute(f"SELECT title, idea, gates, competition, warning, status, kill_reason "
                       f"FROM ideas {where} ORDER BY id", param).fetchall()
    cands = [r for r in rows if r[5] == "candidate"]
    killed = [r for r in rows if (r[5] or "").startswith("killed")]
    rest = [r for r in rows if r[5] == "generated"]

    out = [
        "# " + (L["title_run"].format(run=run) if run else L["title_all"]) + "\n",
        L["counts"].format(n=len(rows), c=len(cands), k=len(killed)) + "\n",
        L["intro"] + "\n",
    ]
    if profile_summary:
        out += [f"<details><summary>{L['profile']}</summary>\n", profile_summary, "\n</details>\n"]
    out.append(f"## {L['candidates']} ({len(cands)})\n")
    for title, idea, gates, comp, warn, *_ in cands:
        out += _candidate(L, title, idea, gates, comp, warn)
    if not cands:
        out.append(L["none"] + "\n")
    out.append(f"## {L['killed']} ({len(killed)})\n")
    for title, idea, *_, status, reason in killed:
        stage = status.replace("killed_", "")
        out.append(f"- **{title}** ({stage}): {reason}  \n  _{_j(idea).get('mechanism', '')}_")
    if rest:
        out.append(f"\n## {L['unfinished']} ({len(rest)})\n")
        out += [f"- {r[0]}" for r in rest]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path
