# Craigslist (Printing Press CLI)

Adapted from OpenClaw / Printing Press **pp-craigslist**.

**Source (do not invent beyond this):**
- https://github.com/mvanhorn/printing-press-library/blob/main/cli-skills/pp-craigslist/SKILL.md
- Upstream name: `pp-craigslist` (Trevin Chow, Apache-2.0)

This is **craigslist.com** (public classifieds). It is **not** [Clawslist](sand-workflow:clawslist) at clawslist.net.

No authentication and no secrets. Do not store API keys or credentials in this skill.

## Prerequisites

This skill drives `craigslist-pp-cli`. Verify the CLI is installed before any command. If it is missing, install it first.

1. Install via the Printing Press installer (defaults: `$HOME/.local/bin` on macOS/Linux, `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows):

```bash
npx -y @mvanhorn/printing-press-library install craigslist --cli-only
```

2. Verify: `craigslist-pp-cli --version`
3. Ensure the reported install directory is on `$PATH` for the runtime that will invoke this skill.

If the `npx` install fails (no Node, offline, etc.), fall back to a direct Go install (requires Go 1.26.6 or newer):

```bash
go install github.com/mvanhorn/printing-press-library/library/commerce/craigslist/cmd/craigslist-pp-cli@latest
```

If `--version` reports command not found, the runtime cannot see the binary directory on `$PATH`. Do not proceed until verification succeeds.

Optional MCP (separate binary, only if the environment supports Claude Code MCP):

```bash
go install github.com/mvanhorn/printing-press-library/library/commerce/craigslist/cmd/craigslist-pp-mcp@latest
```

Run `craigslist-pp-cli doctor` to verify setup.

## When to use

Use `craigslist-pp-cli` for scriptable, local-first **read** access to Craigslist listings: search with filters the Craigslist UI does not support (NOT-keyword), watch saved searches across cities and alert only on true new listings, detect price drift or housing reposts, and triage suspect rentals against cross-city duplicate signals.

Best for read-heavy workflows: watching, exporting, comparing, scoring.

## When not to use

- Do not use for create, update, delete, publish, comment, upvote, invite, order, send messages, book, purchase, or other remote-state changes. This CLI is read-only.
- Do not use for Clawslist / clawslist.net / agent marketplace work — that is [Clawslist](sand-workflow:clawslist).

## Unique capabilities (from upstream)

### Compounding watch surface

- `watch run` — Periodic poll for a saved search that emits NEW, PRICE-DROP, and SEED events (true new listings, not edits/reposts). Cross-city repost detection is `reposts`; cross-city dup detection is `dupe-cluster`.

```bash
craigslist-pp-cli watch save apartments --query 1BR --negate furnished,sublet --sites sfbay --category apa --max-price 2500 && craigslist-pp-cli watch run apartments --seed-only && craigslist-pp-cli watch run apartments --json
```

- `watch tail` — Long-running tail; one JSON event per new diff (`NEW`, `PRICE-DROP`).

```bash
craigslist-pp-cli watch tail apartments --interval 5m --json
```

### Local snapshot history

- `drift` — Price timeline for one listing across captured snapshots.

```bash
craigslist-pp-cli drift 7915891289 --json
```

- `dupe-cluster` — Listings whose body fingerprint and image hash match across cities (scams / aggregator reposts).

```bash
craigslist-pp-cli dupe-cluster --category apa --min-cluster-size 3 --json
```

- `reposts` — Listings reposted N or more times in the last X days, by body fingerprint.

```bash
craigslist-pp-cli reposts 'eames lounge' --min-reposts 3 --window 30d --json
```

- `cities heat` — Fresh listing counts per category across cities.

```bash
craigslist-pp-cli cities heat --category sss --since 24h --top 20 --json
```

### Triage and scoring

- `scam-score` — Rule-based 0–100 score (new account, below-median price, wire-transfer keywords, cross-city dups).

```bash
craigslist-pp-cli scam-score 7915891289 --json
```

- `median` — p25/p50/p75 of prices for a query, optionally over a window or split by city.

```bash
craigslist-pp-cli median 'iphone 15' --category mob --since 30d --by-city --json
```

### Search beyond Craigslist UI

- `search --negate` — NOT-keyword filtering Craigslist search does not support natively.

```bash
craigslist-pp-cli search '1BR' --category apa --site sfbay --negate furnished,sublet,studio --json
```

- `since` — What is new in a category/city since a duration, without a saved search.

```bash
craigslist-pp-cli since 24h --site sfbay --category sss --query ipad --json
```

## Command groups

Discover the full tree with `craigslist-pp-cli --help`. Headline groups from upstream:

- Reference taxonomy: `categories list`, `areas list`, `catalog refresh`
- Search and fetch: `search`, `postings`, `listing get|get-by-pid|images`, `filters show`
- Local store: `cl-sync`
- Saved-search watches: `watch save|list|show|delete|run|tail`
- Snapshot analytics: `drift`, `dupe-cluster`, `reposts`, `median`, `cities heat`, `since`, `geo within|bbox`
- Triage: `scam-score`
- Local-state CRUD: `favorite add|list|remove`
- Helpers: `doctor`, `version`, `which`, `agent-context`, `analytics`, `export`, `import`, `feedback`, `profile`, `tail`, `sync`, `workflow`

If you know the capability but not the command:

```bash
craigslist-pp-cli which "<capability in your own words>"
```

Exit `0` = at least one match; exit `2` = no confident match — fall back to `--help`.

## Freshness

In `--data-source auto`, store-backed read paths may refresh from `sync_state` before reading. `--data-source local` never refreshes. `--data-source live` reads the API and does not mutate the local store. Set `CRAIGSLIST_NO_AUTO_REFRESH=1` to skip the freshness hook.

Covered path: `craigslist-pp-cli postings`. JSON provenance freshness, when present, is at `meta.freshness`.

## Recipes (upstream)

### Hunt one item across the western US

```bash
craigslist-pp-cli search 'eames lounge chair' --sites sfbay,losangeles,seattle,sandiego,sacramento,fresno,inlandempire,orangecounty --category fua --max-price 2500 --has-pic --json --select items.title,items.priceDisplay,items.site,items.canonicalUrl
```

### Watch for a 1BR that is not furnished or a sublet

```bash
craigslist-pp-cli watch save sf-1br --query '1BR' --sites sfbay --category apa --max-price 2800 --negate furnished,sublet,studio,airbnb && craigslist-pp-cli watch run sf-1br --seed-only && craigslist-pp-cli watch tail sf-1br --interval 5m --json
```

### Triage a too-good listing

```bash
craigslist-pp-cli cl-sync --site sfbay --category apa --since 7d && craigslist-pp-cli scam-score 7915891289 --json && craigslist-pp-cli dupe-cluster --pid 7915891289 --json
```

`cl-sync` populates the local store; downstream scoring/dup commands need that store.

### Fair-price range

```bash
craigslist-pp-cli median 'iphone 15' --category mob --since 30d --by-city --json
```

### What hit while I was asleep

```bash
craigslist-pp-cli since 12h --site sfbay --category sss --query 'macbook pro' --json
```

## Agent mode

Add `--agent` to any command. Expands to `--json --compact --no-input --no-color --yes`.

- JSON on stdout, errors on stderr
- `--select` keeps a subset of fields (dotted paths; arrays traverse element-wise)
- `--dry-run` shows the request without sending
- Offline-friendly via local SQLite when available
- Non-interactive; never prompt
- Read-only — do not use for mutating requests

Envelope for store/API reads:

```json
{
  "meta": {"source": "live", "synced_at": "...", "reason": "..."},
  "results": {}
}
```

Parse `.results` for data and `.meta.source` for live vs local.

## Profiles

Saved flag sets reused across invocations. Explicit flags win over profile values; profile values win over defaults.

```bash
craigslist-pp-cli profile save briefing --json
craigslist-pp-cli --profile briefing postings
craigslist-pp-cli profile list --json
craigslist-pp-cli profile show briefing
craigslist-pp-cli profile delete briefing --yes
```

## Output delivery

Every command accepts `--deliver`. Supported sinks: `stdout`, `file:<path>` (atomic write), `webhook:<url>` (POST). Unknown schemes fail. Do not put webhook secrets in this skill.

## Feedback (local only by default)

```bash
craigslist-pp-cli feedback "the --since flag is inclusive but docs say exclusive"
craigslist-pp-cli feedback list --json --limit 10
```

Stored at `~/.craigslist-pp-cli/feedback.jsonl`. Never POSTed unless `CRAIGSLIST_FEEDBACK_ENDPOINT` is set **and** either `--send` is passed or `CRAIGSLIST_FEEDBACK_AUTO_SEND=true`.

## Exit codes (upstream)

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 2 | Usage error |
| 3 | Resource not found |
| 5 | API error |
| 7 | Rate limited (wait and retry) |
| 10 | Config error |

## Direct use

1. `which craigslist-pp-cli` — if missing, install (Prerequisites).
2. Match the request to Unique capabilities / Command groups.
3. Execute with `--agent`:

```bash
craigslist-pp-cli <command> [subcommand] [args] --agent
```

4. If ambiguous, use `craigslist-pp-cli --help` or `craigslist-pp-cli which "..."`.
