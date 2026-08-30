# Map of Agents — Graph

A **force-directed map of the AI agent ecosystem** — 2,040 real projects pulled live from
the GitHub API, connected by 17,000+ edges built from relationships that actually exist
between them: shared topic tags and shared owning orgs. Where [Map of Agents](https://github.com/shaileshjaiswalwins/map-of-agents)
groups projects into a treemap by category, this one shows the *network* — which projects
cluster together, which ecosystems (LangChain, MCP, AutoGPT-likes) are hubs, and which
projects are outliers with few connections.

Inspired by [anvaka/map-of-reddit](https://github.com/anvaka/map-of-reddit)
([live demo](https://anvaka.github.io/map-of-reddit/)), which maps subreddits as a
force-directed graph where proximity comes from shared user activity. Here, proximity comes
from shared GitHub topics and shared organizations — a genuine structural signal, not a
layout trick.

**[Live demo →](https://shaileshjaiswalwins.github.io/map-of-agents-graph/)**

## Screenshots

### Category lens — the ecosystem's actual shape
Each dot is a project; lines are shared topics or shared owning orgs. Dense clusters are
crowded sub-spaces; the loose strands reaching outward are the outliers.
![Map of Agents — category lens](assets/screenshot-overview.jpg)

### Engineering lens — maintenance health
Green = active, amber = moderate, orange = stale, grey = archived/unknown. Spot risk in the
crowd before you depend on something.
![Map of Agents — engineering lens](assets/screenshot-engineering-lens.jpg)

### Click any project — connections and why
Every detail panel shows real metrics, an abnormal-growth warning where relevant, and its
strongest connections — click one to jump straight there.
![Map of Agents — project detail panel](assets/screenshot-detail.jpg)

> Screenshots above reflect the core map/lens/detail experience. A few newer additions —
> the maintenance filter chips, the reset-view button, and the mobile filter drawer — aren't
> pictured yet; see [Features](#features) below for the full current list.

## Features

**Explore**
- Live force-directed layout (d3-force + Canvas) of 2,040 real GitHub repos — no
  precomputed coordinates, the graph physically settles in your browser.
- Scroll/pinch to zoom (labels fade in as you get close), drag to pan, click a node for
  full details.
- Three lenses, one click to switch: **Category** (what kind of project), **Engineering**
  (maintenance health — active/moderate/stale/archived), **Product** (traction — stars
  gained per day since creation, a momentum signal independent of raw star count).

**Filter and find**
- **Category filtering is multi-select**: click a category's dot to solo/restore it, click
  its name to toggle it in or out of the active set — compare two adjacent categories side
  by side.
- **Maintenance filter chips** — show only active repos, or only stale/archived ones, as an
  actual filter, not just a recolor.
- **Suspicious-only toggle** — isolate the 26 repos currently flagged for abnormal star
  growth (see below) in one click.
- **Search that goes somewhere**: type, then hit `Enter` — a single match gets a smooth
  zoom-in and its detail panel opens; multiple matches get framed together in view.
- **Reset view** (⌂ button) — clears every filter and search term and recenters the camera
  in one click, no reload needed.

**Share**
- Opening any project updates the URL (`?node=owner/repo`) automatically — copy the address
  bar, or hit "Copy link" in the detail panel, to send someone straight to that project,
  pre-selected and pre-zoomed with onboarding skipped.
- Open Graph / Twitter Card meta tags so shared links render a real preview card instead of
  a bare URL.

**Trust the data, but verify it**
- **Abnormal-growth flagging**: any repo sustaining ≥250 stars/day since creation with
  ≥3,000+ total stars gets a dashed red ring on the map, a ⚠ in its tooltip, and an explicit
  caveat in its detail panel — surfaced for you to check, not hidden or silently excluded.
  26 of 2,040 tracked repos are currently flagged.
- Every "connected to" reason is real and inspectable — click through to confirm it before
  trusting it.

**Everywhere**
- Onboarding: a short 4-step spotlight tour on first visit, replayable via the `?` button.
- Mobile: category/maintenance filters live in a slide-up drawer (not hidden), with
  safe-area padding for notched devices.
- Keyboard: `/` focuses search, `Enter` jumps to a match, `Esc` closes/clears, in that
  priority order.
- Resilient loading: a failed data fetch shows a retry screen instead of hanging forever on
  a spinner.
- No build step — a static `docs/index.html` + `docs/data.json`, styled with Tailwind (CDN)
  and rendered with D3, hosted directly from GitHub Pages.

## What it's for

- **See the ecosystem's real shape**, not a flat list. Dense clusters mean a crowded
  sub-space (e.g. everything built around MCP); sparse, loosely-connected nodes are the
  outliers worth a second look.
- **An engineering lead** can filter to Active maintenance, isolate the suspicious-flagged
  set to see if anything they depend on is in it, and check a project's real connections
  before adopting something adjacent.
- **A product lead** can switch to the Product lens to see which categories and projects
  have real momentum (traction) rather than just cumulative size, which rewards age over
  relevance — then click through connected projects to map out a competitive cluster fast.

## How it works

- **Data**: `scripts/fetch_live_data.py` pulls live metrics for hundreds of projects via the
  GitHub REST API — broad topic search (`GET /search/repositories`) across 7 categories,
  merged with a curated flagship list, deduped by `full_name`.
- **Graph construction**: `scripts/build_graph_data.py` builds edges from two real signals —
  shared GitHub topics (excluding generic tags like `python` or `llm` that would connect
  everything) and shared owning org/user, which is weighted higher (2.5x) as the stronger
  signal. Each edge keeps only its single strongest reason (by signal weight, not
  alphabetical order); each node keeps only its strongest ~12 edges so a handful of huge hub
  topics don't collapse the whole graph into one blob.
- **Abnormal-growth detection**: any repo with sustained traction ≥250 stars/day and ≥3,000
  total stars gets flagged — a heuristic tuned against known organic growth patterns (a
  typical viral launch runs 50–150/day for its first week; even Linux's lifetime average is
  ~50/day), not proof of fraud, and surfaced rather than filtered out.
- **Layout**: a live [d3-force](https://d3js.org/d3-force) simulation (charge + link +
  collide) runs client-side and settles in the browser.
- **Rendering**: HTML5 Canvas (not SVG) with a dirty-flag render loop — redraws only happen
  when something actually changes, so a settled 2,040-node graph sits idle at 0% instead of
  redrawing 2,040 nodes × 17,034 edges every frame for nothing.
- **Payload**: `data.json` ships fields the client actually reads and edges as compact
  `[source, target, weight, reason]` tuples rather than keyed objects — 1.86MB uncompressed
  (~416KB gzipped) for the full 2,040-node, 17,034-edge graph.

## A note on data honesty

Star counts come straight from the GitHub API with no fraud-filtering — like Map of GitHub,
this reflects GitHub as it actually reports itself, including any repos with anomalously
fast star growth (a known, unsolved problem across the ecosystem). Node size is stars but
under a square-root scale specifically so one outlier can't visually dominate a category.
Repos matching the abnormal-growth heuristic above are flagged directly in the UI — if a
bubble looks implausibly large for how known the project is, check the flag before treating
its star count as a popularity signal.

## Running locally

```bash
cd docs
python3 -m http.server 8080
# open http://localhost:8080
```

## Refreshing the data

Requires the [GitHub CLI](https://cli.github.com/) authenticated (`gh auth login`).

```bash
python3 scripts/fetch_live_data.py     # pulls live metrics into docs/raw_live_data.json (gitignored)
python3 scripts/build_graph_data.py    # builds nodes + edges into docs/data.json
```

`fetch_live_data.py` takes several minutes — GitHub's search endpoint is rate-limited to 30
requests/minute. Edit the `CATEGORIES` dict to add flagship repos or broaden topic-search
queries per category. Edit `SUSPICIOUS_TRACTION` / `SUSPICIOUS_MIN_STARS` in
`build_graph_data.py` to tune the abnormal-growth threshold.

## Project structure

```
map-of-agents-graph/
├── docs/
│   ├── index.html            # the visualization (canvas force graph, filters, lenses)
│   ├── data.json             # generated dataset (nodes + compact weighted edges)
│   ├── robots.txt / sitemap.xml
│   └── assets/og-preview.jpg # social share preview image
├── scripts/
│   ├── fetch_live_data.py    # pulls live GitHub metrics (search + per-repo lookups)
│   └── build_graph_data.py   # builds the node-link graph, computes derived signals
└── assets/                   # README screenshots
```

## Credits

- Concept and force-directed approach inspired by [anvaka/map-of-reddit](https://github.com/anvaka/map-of-reddit).
- Companion project: [Map of Agents](https://github.com/shaileshjaiswalwins/map-of-agents) (treemap view).
- Built with [D3.js](https://d3js.org/) and the [GitHub REST API](https://docs.github.com/en/rest).
