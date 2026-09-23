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

All options:

| Option | Default | Effect |
|---|---|---|
| `--target N` | `3` | Stop once N ideas have passed every step |
| `--per-round N` | `6` | Ideas per generation round |
| `--max-rounds N` | `5` | Upper limit on generation rounds, so a run always ends |
| `--sector TEXT` | random | Fixed sector for every round instead of a random one |
| `--market TEXT` | from profile | Fixed target market instead of one from `preferences.target_markets` |
| `--language TEXT` | from profile | Output language, overrides `generation.output_language` |
| `--profile PATH` | `profile.toml` | Founder profile to use |
| `--checklist PATH` | `checklist.md` | Checklist for the evaluation step |
| `--db PATH` | `data/ideas.db` | SQLite database with every idea and its verdict |
| `--output DIR` | `output` | Where the markdown reports go |
| `--all` | off | Only write a report of all previous runs; no API calls |

Examples for the founder in the [example profile](#example-profile) below:

```bash
# A cheap first run: at most 2 rounds of 4 ideas, stop at 2 candidates
python -m ideagen --target 2 --per-round 4 --max-rounds 2

# Stay in your own domain and aim at the Belgian market
python -m ideagen --sector "road transport" --market Belgium

# Same profile, report in Dutch, separate database and output folder for this experiment
python -m ideagen --language Dutch --db data/transport.db --output output/transport

# Try a second profile side by side
python -m ideagen --profile profiles/warehousing.toml
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

### Example profile

A complete, consistent example: a Dutch backend developer who works for a logistics software company and wants a small B2B side project. The same profile is in `profile.example.toml`.

```toml
[founder]
country = "Netherlands"
background = "Backend developer, 8 years in logistics software; before that 2 years as a transport planner"
technical_skills = ["Python", "SQL", "scraping", "LLM integrations"]
domain_expertise = ["road transport", "warehousing"]
network = "Can reach ~20 planners and transport company owners directly via former colleagues"
own_frustrations = [
    "carriers send delivery confirmations as scanned PDFs that someone retypes",
    "customs and emission-zone rules change and planners find out after a fine",
]
unfair_advantage = "Knows how small carriers actually plan: in Excel and WhatsApp, not in a TMS"

[time_and_money]
hours_per_week = 8
starting_budget = 500
currency = "EUR"
months_until_first_revenue = 6

[preferences]
target_markets = ["Netherlands", "Belgium"]
sales = "limited"          # none | limited | fine
support = "limited"        # none | limited | fine
customer_type = "B2B"
revenue_ceiling = "Solo, max ~10k MRR, no employees"
enjoyable_work = "Cleaning and analysing data, writing"
disliked_work = "Cold calling"
avoid = ["medical data", "two-sided marketplaces", "enterprise sales"]

[employer]
employer_sector = "Logistics software (TMS vendor for mid-size carriers)"
excluded = ["the employer's customers", "TMS or route-planning software"]
side_activity_policy = "Allowed after notifying my manager; no competing activities"

[generation]
output_language = "English"
sectors = []
data_sources = []
```

Tips for filling it in:

- **Be concrete.** "Can reach ~20 planners via former colleagues" helps the evaluator judge gate 4; "good network" does not.
- **`own_frustrations` and `unfair_advantage`** steer the generator toward problems you have seen yourself. Leave them empty if you have nothing specific; do not invent them.
- **`employer`** does not stop ideas. The evaluator flags possible conflicts in the founder-fit explanation, so you can check them against your contract before you start.
- **`generation.sectors` and `generation.data_sources`** replace the built-in lists. Use them to narrow a run, for example for the founder above:

  ```toml
  [generation]
  output_language = "Dutch"
  sectors = ["road transport", "warehousing", "construction subcontracting"]
  data_sources = ["RDW open data", "TenderNed / TED", "emails and PDFs in the customer's inbox"]
  ```

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

Example `.env`: only the key is required; the other lines show the defaults.

```bash
ANTHROPIC_API_KEY=sk-ant-...

IDEAGEN_MODEL_GEN=claude-sonnet-5
IDEAGEN_MODEL_EVAL=claude-opus-5-5
IDEAGEN_MODEL_NORMALIZE=claude-sonnet-5
IDEAGEN_MAX_SEARCHES=8      # lower this, e.g. to 4, to make competition checks cheaper
```

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
