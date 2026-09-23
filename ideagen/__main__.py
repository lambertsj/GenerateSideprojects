import argparse
import secrets
from datetime import datetime

from . import config, pipeline, report, store


def main():
    ap = argparse.ArgumentParser(
        prog="python -m ideagen",
        description="Side-project ideas: generate → kill gates → competition → markdown")
    ap.add_argument("--target", type=int, default=3, help="number of candidates that survive every step (default 3)")
    ap.add_argument("--per-round", type=int, default=6, help="ideas per generation round (default 6)")
    ap.add_argument("--max-rounds", type=int, default=5, help="maximum number of generation rounds (default 5)")
    ap.add_argument("--sector", default="", help="fixed sector instead of a random one")
    ap.add_argument("--market", default="", help="fixed target market instead of one from your profile")
    ap.add_argument("--language", default="", help="output language, overrides generation.output_language")
    ap.add_argument("--profile", default="profile.toml")
    ap.add_argument("--checklist", default="checklist.md")
    ap.add_argument("--db", default="data/ideas.db")
    ap.add_argument("--output", default="output")
    ap.add_argument("--all", action="store_true", help="only write a report of all previous runs")
    args = ap.parse_args()

    con = store.open_db(args.db)
    if args.all:
        profile = config.load_profile(args.profile)
        print(report.write(con, args.output, args.language or config.output_language(profile)))
        return

    settings = config.load_env()
    profile = config.load_profile(args.profile)
    language = args.language or config.output_language(profile)
    profile_text = config.profile_text(profile)
    checklist = config.load_checklist(args.checklist)

    from .llm import LLM
    llm = LLM()
    run = f"{datetime.now():%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"
    found = 0

    try:
        for rnd in range(1, args.max_rounds + 1):
            seed = pipeline.pick_seed(profile, args.sector, args.market)
            print(f"\n== Round {rnd}: {seed['target_market']} · {seed['sector']} · "
                  f"{seed['data_source']} · {seed['trigger']}")
            try:
                ideas = pipeline.generate(llm, settings, args.per_round, seed, profile_text,
                                          language, store.recent_titles(con))
            except RuntimeError as e:
                print(f"  ! generation failed: {e}")
                continue

            for raw in ideas:
                raw.setdefault("target_market", seed["target_market"])
                title = raw.get("title", "untitled")
                dup = store.similar_existing(con, raw)
                if dup:
                    print(f"  ≈ skipped (similar to '{dup}'): {title}")
                    continue
                try:
                    idea = pipeline.normalize(llm, settings, raw, language)
                except RuntimeError as e:
                    print(f"  ! normalisation failed: {title}: {e}")
                    continue
                rid = store.add(con, run, idea, seed)

                try:
                    gates = pipeline.check_gates(llm, settings, idea, checklist, profile_text, language)
                except RuntimeError as e:
                    print(f"  ! gate check failed: {title}: {e}")
                    continue
                store.update(con, rid, gates=gates)
                if reason := pipeline.gate_kill(gates):
                    store.update(con, rid, status="killed_gates", kill_reason=reason)
                    print(f"  ✗ {title} — {reason[:100]}")
                    continue

                try:
                    comp = pipeline.check_competition(llm, settings, idea, language)
                except RuntimeError as e:
                    print(f"  ! competition check failed: {title}: {e}")
                    continue
                store.update(con, rid, competition=comp)
                if reason := pipeline.competition_kill(comp):
                    store.update(con, rid, status="killed_competition", kill_reason=reason)
                    print(f"  ✗ {title} — {reason[:100]}")
                    continue

                store.update(con, rid, status="candidate", warning=pipeline.warning(gates))
                found += 1
                print(f"  ✓ {title}")
                if found >= args.target:
                    break
            if found >= args.target:
                break
    except KeyboardInterrupt:
        print("\nInterrupted; writing the report with what we have.")

    path = report.write(con, args.output, language, run, profile_text)
    print(f"\n{found} candidate(s). Report: {path}")
    if found < 2:
        print("Note: only choose once at least two candidates sit side by side. Run again.")


if __name__ == "__main__":
    main()
