# GenerateSideprojects

A generator that comes up with side-project ideas, evaluates them strictly, and writes the survivors to a markdown file.

The design follows one principle: **generating and evaluating are separate.** The model that comes up with ideas never sees the checklist. Otherwise ideas get designed towards the test and everything passes.

## How it works

```
generate ──► normalise ──► kill gates ──► competition check ──► output/ideas_<run>.md
 (Sonnet)     (Sonnet)       (Opus)         (Opus + web search)
```

1. **Generate.** The generator describes each idea freely in a few sentences, without any checklist format. Each round gets a random combination of target market, sector, data source and inflection point. Data sources are country-specific: built-in lists exist for the Netherlands, Belgium, Germany, the United Kingdom and the United States, and other countries get a generic prompt. In half of the rounds the sector comes from your own domain expertise. The generator receives all previous titles, and ideas too similar to earlier ones are skipped, so every run explores new directions.
2. **Normalise.** A separate step that does not judge. It converts the free text into fixed fields (customer, job, mechanism, input, why now) and strips selling language. Anything the description does not say becomes `not stated` instead of being filled in, because gaps are exactly what the evaluator needs to see.
3. **Kill gates.** A separate, sceptical evaluation on Phase 0, Phase 1 and founder fit, judged against the regulation of the target market. If it finds no weak point anywhere, it re-evaluates once more strictly. The code makes the stop decision, not the model. An idea is killed when:
   - a gate fails structurally,
   - the only spend is the owner's own time,
   - two or more gates fail,
   - founder fit is weak and the idea does not fit your hours and budget.
4. **Competition.** Only for survivors, because web search costs money. The check searches in the local language and in English for direct competitors, workarounds, foreign variants and failure traces. An idea is killed by a free competitor with full overlap, or when the check itself concludes "stop".

Every idea goes into `data/ideas.db`, including the killed ones with their reason.

### What each step sees

Each step is a separate API call with an empty context. Nothing carries over except the fields below.

| Step | Sees | Does not see |
|---|---|---|
| Generate | profile, seed, previous titles | checklist, evaluations, kill reasons |
| Normalise | the free-text description | profile, checklist, title |
| Kill gates | checklist, profile, customer, job, mechanism, input, target market | title, description, why now |
| Competition | customer, job, mechanism, input, target market, why now | title, description, gate results |

The title and description are the generator's own framing, so they never reach an evaluating step. "Why now" goes only to the competition check, where the inflection point belongs. The competition check does not know how an idea scored on the gates.

One limitation remains: generator and evaluator are both Claude models and may share blind spots.

## Installation

Requires Python 3.11 or newer and an [Anthropic API key](https://console.anthropic.com/).

```bash
git clone https://github.com/lambertsj/GenerateSideprojects.git
cd GenerateSideprojects
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                 # add ANTHROPIC_API_KEY
cp profile.example.toml profile.toml # fill in your founder profile
```

Optionally replace `checklist.md` with your full checklist, in any language. The evaluation step reads that file.

## Usage

```bash
python -m ideagen                            # up to 3 candidates, max 5 rounds of 6 ideas
python -m ideagen --target 5 --per-round 8   # more candidates
python -m ideagen --sector "dental practices"
python -m ideagen --market Germany           # fixed target market
python -m ideagen --language Dutch           # override the output language
python -m ideagen --all                      # report of all previous runs
```

Each run writes `output/ideas_<date_time>.md` with:

- **Candidates.** For each one: customer, job, mechanism, target market, a gate table, coverage, feedback latency, founder fit, daily work in year 2, riskiest assumption, cheapest experiment, a field-test plan, and competitors with links.
- **Killed.** For each idea, the reason it stopped. This is often the most instructive part.

If you interrupt a run with Ctrl+C, the report is still written.

## Founder profile

`profile.toml` steers both generation and the founder-fit evaluation.

| Section | Fields | Used for |
|---|---|---|
| `founder` | country, background, technical skills, domain expertise, network, own frustrations, unfair advantage | Direction for generation; employment rules of your country; gate 4 (can you reach 10 customers?) |
| `time_and_money` | hours per week, starting budget, currency, months until first revenue | Whether the smallest paid version is feasible |
| `preferences` | target markets, sales, support, customer type, revenue ceiling, enjoyable and disliked work, avoid | Market choice, daily work in year 2, structural traps |
| `employer` | sector, excluded categories, side-activity policy | Conflicts of interest are noted in the founder-fit explanation, not a kill reason |
| `generation` | output language, custom sectors and data sources | Language of the report; overriding built-in lists |

`founder.country` is required. `preferences.target_markets` defaults to that country. The two are separate on purpose: where you live determines your employment rules and legal setup, while your customers may be elsewhere.

`profile.toml` and `.env` are in `.gitignore`. Do not commit them.

## Output language

Ideas, evaluations and reasons are written in `generation.output_language`, or in the language passed with `--language`. Report headings exist in English and Dutch; other languages get English headings with the content in the chosen language. Adding a language means adding a block to `LABELS` in `ideagen/report.py`.

## Configuration in `.env`

| Variable | Default |
|---|---|
| `ANTHROPIC_API_KEY` | required |
| `IDEAGEN_MODEL_GEN` | `claude-sonnet-5` |
| `IDEAGEN_MODEL_EVAL` | `claude-opus-5-5` |
| `IDEAGEN_MODEL_NORMALIZE` | same as `IDEAGEN_MODEL_GEN` |
| `IDEAGEN_MAX_SEARCHES` | `8` per competition check |

## Limitations

- **A candidate is a hypothesis, not a viable idea.** A model cannot test gate 4 (talking to 10 customers within two weeks) or gate 5 (someone paying upfront for a manual version). Those gates get the status `field_test` with a concrete plan. Only those conversations tell you anything.
- **Competition can be missed.** The check only sees what web search finds. Spreadsheet and freelance workarounds are often invisible online.
- **Costs.** Each candidate costs a share of one generation call, one normalisation call, one or two gate calls, and a competition check with up to 8 searches. Start with a small `--target`.
- **Never choose based on one candidate.** Put at least two side by side.

## Structure

```
ideagen/
  __main__.py   CLI and the run loop
  pipeline.py   generation, normalisation, gates, competition, stop rules,
                and which fields each step may see
  sources.py    sectors, triggers and data sources per country
  prompts.py    system prompts and JSON schemas
  llm.py        Anthropic client, pause_turn handling, JSON parsing
  store.py      SQLite and deduplication
  report.py     markdown output, headings in English and Dutch
  config.py     loading .env, profile and checklist
checklist.md           read by the evaluation step
profile.example.toml
.env.example
```

## License

MIT
