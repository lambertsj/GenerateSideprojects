import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    model_gen: str
    model_eval: str
    model_normalize: str
    max_searches: int


def load_env() -> Settings:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is missing. Copy .env.example to .env and add your key.")
    return Settings(
        model_gen=os.environ.get("IDEAGEN_MODEL_GEN", "claude-sonnet-5"),
        model_eval=os.environ.get("IDEAGEN_MODEL_EVAL", "claude-opus-5-5"),
        model_normalize=os.environ.get("IDEAGEN_MODEL_NORMALIZE",
                                       os.environ.get("IDEAGEN_MODEL_GEN", "claude-sonnet-5")),
        max_searches=int(os.environ.get("IDEAGEN_MAX_SEARCHES", "8")),
    )


def load_profile(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        sys.exit(f"{path} not found. Copy profile.example.toml to profile.toml and fill it in.")
    with p.open("rb") as fh:
        profile = tomllib.load(fh)
    founder = profile.setdefault("founder", {})
    prefs = profile.setdefault("preferences", {})
    if not founder.get("country"):
        sys.exit("founder.country is required in profile.toml.")
    if not prefs.get("target_markets"):
        prefs["target_markets"] = [founder["country"]]
    return profile


def load_checklist(path: str) -> str:
    p = Path(path)
    if not p.exists():
        sys.exit(f"{path} not found. The evaluation step needs a checklist.")
    return p.read_text(encoding="utf-8")


def output_language(profile: dict) -> str:
    return profile.get("generation", {}).get("output_language") or "English"


def profile_text(profile: dict) -> str:
    """Readable summary of the profile; empty fields and the generation section are dropped."""
    lines = []
    for section, fields in profile.items():
        if section == "generation" or not isinstance(fields, dict):
            continue
        for key, value in fields.items():
            if value in ("", [], None):
                continue
            if isinstance(value, list):
                value = ", ".join(map(str, value))
            lines.append(f"- {section}.{key}: {value}")
    return "\n".join(lines) or "- (no profile filled in)"
