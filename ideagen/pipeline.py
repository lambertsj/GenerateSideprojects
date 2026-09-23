import json
import random

from . import prompts, sources


def pick_seed(profile, fixed_sector="", fixed_market=""):
    gen = profile.get("generation", {})
    founder = profile.get("founder", {})
    market = fixed_market or random.choice(profile["preferences"]["target_markets"])
    expertise = founder.get("domain_expertise") or []
    if fixed_sector:
        sector = fixed_sector
    elif expertise and random.random() < 0.5:  # founder fit: half of the rounds in your own domain
        sector = random.choice(expertise)
    else:
        sector = random.choice(gen.get("sectors") or sources.SECTORS)
    return {
        "target_market": market,
        "sector": sector,
        "data_source": random.choice(gen.get("data_sources") or sources.sources_for(market)),
        "trigger": random.choice(sources.TRIGGERS),
    }


def generate(llm, settings, n, seed, profile_text, language, previous):
    prompt = f"""Generate {n} different side-project ideas.

Starting point (a direction, not a straitjacket; at least half should clearly lean on it):
- target market: {seed['target_market']}
- sector: {seed['sector']}
- possible input: {seed['data_source']}
- possible inflection point: {seed['trigger']}

Founder profile:
{profile_text}

Avoid these previously generated ideas and variations of them:
{json.dumps(previous, ensure_ascii=False)}

Answer only with JSON between <json> and </json>:
{prompts.GEN_SCHEMA}"""
    system = prompts.GEN_SYSTEM.format(language=language)
    res = llm.json(settings.model_gen, system, prompt)
    return res if isinstance(res, list) else res.get("ideas", [])


def normalize(llm, settings, raw, language):
    """Separate, non-judging step: free text → fixed fields, gaps stay visible.
    Sees neither the profile nor the checklist."""
    prompt = f"""Description:
{raw.get('description', '')}

JSON schema:
{prompts.NORM_SCHEMA}"""
    system = prompts.NORM_SYSTEM.format(language=language)
    fields = llm.json(settings.model_normalize, system, prompt)
    return {"title": raw.get("title", "untitled"), "description": raw.get("description", ""),
            "target_market": raw.get("target_market", ""), **fields}


# What each later step is allowed to see. The free-text description and title stay behind:
# they are the generator's own framing.
EVALUATION_FIELDS = ("customer", "job", "mechanism", "input", "target_market")
COMPETITION_FIELDS = EVALUATION_FIELDS + ("why_now",)


def view(idea, fields):
    return {k: idea.get(k, "not stated") for k in fields}


def check_gates(llm, settings, idea, checklist, profile_text, language):
    prompt = f"""Checklist:
{checklist}

Founder profile:
{profile_text}

Idea:
{json.dumps(view(idea, EVALUATION_FIELDS), ensure_ascii=False, indent=1)}

Evaluate this idea on Phase 0, Phase 1 and founder fit. JSON schema:
{prompts.GATE_SCHEMA}"""
    system = prompts.GATE_SYSTEM.format(language=language)
    res = llm.json(settings.model_eval, system, prompt)
    if not has_weak_point(res):
        prompt += ("\n\nA previous evaluation found no weak point anywhere. That is pitching, "
                   "not evaluating. Evaluate again, more strictly.")
        res = llm.json(settings.model_eval, system, prompt)
    return res


def has_weak_point(res):
    return any(g.get("verdict") in ("fail", "uncertain") for g in res.get("gates", []))


def gate_kill(res):
    """The code makes the stop decision, not the model."""
    for g in res.get("gates", []):
        if g.get("verdict") == "fail" and g.get("failure_type") == "structural":
            return f"Gate {g.get('nr')} failed structurally: {g.get('reason')}"
    if res.get("spend_signal") == "owner_time":
        return "Gate 3: the only spend is the owner's own time"
    fails = [g for g in res.get("gates", []) if g.get("verdict") == "fail"]
    if len(fails) >= 2:
        return "Multiple gates failed: " + "; ".join(f"{g.get('nr')}: {g.get('reason')}" for g in fails)
    ff = res.get("founder_fit", {})
    if ff.get("conflict_of_interest"):
        return f"Conflict of interest with employer: {ff.get('explanation')}"
    if ff.get("match") == "weak" and ff.get("fits_hours_and_budget") is False:
        return f"Weak founder fit and does not fit hours/budget: {ff.get('explanation')}"
    return None


def check_competition(llm, settings, idea, language):
    prompt = f"""Idea:
{json.dumps(view(idea, COMPETITION_FIELDS), ensure_ascii=False, indent=1)}

Run 4 to {settings.max_searches} targeted searches (local language of the target market and English,
including foreign variants and failure traces). JSON schema for your final answer:
{prompts.COMP_SCHEMA}"""
    tool = {"type": "web_search_20250305", "name": "web_search", "max_uses": settings.max_searches}
    system = prompts.COMP_SYSTEM.format(language=language)
    return llm.json(settings.model_eval, system, prompt, tools=[tool])


def competition_kill(res):
    if res.get("verdict") == "stop":
        return f"Competition: {res.get('reason')}"
    for c in res.get("competitors", []):
        if c.get("overlap") == "full" and c.get("price") == "free":
            return f"Free competitor with full overlap: {c.get('name')} ({c.get('url')})"
    return None


def warning(gates):
    if not has_weak_point(gates):
        return "no_weak_point"
    if gates.get("mechanism", {}).get("retro_validation") == 3:
        return "prospective_only"
    return None
