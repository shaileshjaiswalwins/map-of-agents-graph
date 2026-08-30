#!/usr/bin/env python3
"""Shape docs/raw_live_data.json into a NODE-LINK graph (docs/data.json) for the
force-directed "Map of Agents" — nodes are projects, edges are real relationships
between them, not a synthetic layout:

  - shared-topic edges: two repos that both carry the same GitHub topic tag
    (excluding generic topics that would connect almost everything)
  - shared-owner edges: two repos published by the same org/user (e.g. the
    LangChain org's repos cluster together even across categories)

Also computes the same maintenance/traction signals as build_data.py so the
Engineering/Product lenses carry over.
"""
import itertools
import json
from collections import defaultdict
from datetime import datetime, timezone

CATEGORY_LABELS = {
    "agent-frameworks": "Agent Frameworks & SDKs",
    "autonomous-agents": "Autonomous & General-Purpose Agents",
    "agent-protocols-infra": "Protocols, Orchestration & Infrastructure",
    "agent-memory-tools": "Memory, RAG & Retrieval",
    "agent-eval-observability": "Evaluation & Observability",
    "coding-agents": "Coding Agents & Dev Tools",
    "multi-agent-simulation": "Multi-Agent Simulation & Research",
}

# Topics too generic to be a meaningful connection (would blob the whole graph
# into one cluster). Anything left after this filter is a real shared signal.
GENERIC_TOPICS = {
    "python", "javascript", "typescript", "ai", "artificial-intelligence",
    "machine-learning", "deep-learning", "llm", "llms", "openai", "gpt",
    "chatgpt", "nlp", "ml", "hacktoberfest", "awesome", "awesome-list",
    "docker", "go", "rust", "java", "cli", "api", "framework", "opensource",
    "open-source", "gpt-4", "chatbot", "generative-ai",
}

# Cap how many edges one shared topic can create so a single huge tag
# (e.g. "agents") doesn't produce a complete graph — sample the top-N by
# combined stars instead of connecting every pair.
MAX_PAIRS_PER_TOPIC = 40
MAX_EDGES_PER_NODE_TARGET = 12  # soft target used for final pruning

SNAPSHOT_DATE = datetime(2026, 8, 30, tzinfo=timezone.utc)


def maintenance_status(p):
    if p["archived"]:
        return "archived"
    d = p["days_since_push"]
    if d is None:
        return "unknown"
    if d < 0:
        d = 0
    if d <= 90:
        return "active"
    if d <= 365:
        return "moderate"
    return "stale"


def traction_score(p):
    created = p.get("created_at")
    if not created:
        return 0.0
    dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    age_days = max((SNAPSHOT_DATE - dt).days, 1)
    return round(p["stars"] / age_days, 2)


def build():
    raw = json.load(open("docs/raw_live_data.json"))
    raw.sort(key=lambda p: -p["stars"])

    nodes = []
    id_of = {}
    for i, p in enumerate(raw):
        status = maintenance_status(p)
        node = {
            "id": i,
            "name": p["name"],
            "full_name": p["full_name"],
            "owner": p["full_name"].split("/")[0],
            "description": p["description"] or "No description provided.",
            "url": p["url"],
            "stars": p["stars"],
            "forks": p["forks"],
            "open_issues": p["open_issues"],
            "language": p["language"],
            "license": p["license"],
            "archived": p["archived"],
            "pushed_at": p["pushed_at"],
            "days_since_push": max(p["days_since_push"], 0) if p["days_since_push"] is not None else None,
            "maintenance": status,
            "traction": traction_score(p),
            "topics": p.get("topics", []),
            "category": p["category"],
            "category_label": CATEGORY_LABELS[p["category"]],
        }
        nodes.append(node)
        id_of[p["full_name"]] = i

    edge_weight = defaultdict(float)
    edge_reason = {}

    # shared-topic edges
    topic_to_ids = defaultdict(list)
    for n in nodes:
        for t in n["topics"]:
            if t in GENERIC_TOPICS:
                continue
            topic_to_ids[t].append(n["id"])

    for topic, ids in topic_to_ids.items():
        if len(ids) < 2 or len(ids) > 60:
            continue  # too rare to matter, or too common to be meaningful
        ids_sorted = sorted(ids, key=lambda i: -nodes[i]["stars"])[:MAX_PAIRS_PER_TOPIC]
        for a, b in itertools.combinations(sorted(ids_sorted), 2):
            key = (a, b)
            edge_weight[key] += 1.0
            edge_reason.setdefault(key, set()).add(f"#{topic}")

    # shared-owner edges (org clustering) — strong signal, weight it higher
    owner_to_ids = defaultdict(list)
    for n in nodes:
        owner_to_ids[n["owner"]].append(n["id"])
    for owner, ids in owner_to_ids.items():
        if len(ids) < 2 or len(ids) > 25:
            continue
        for a, b in itertools.combinations(sorted(ids), 2):
            key = (a, b)
            edge_weight[key] += 2.5
            edge_reason.setdefault(key, set()).add(f"@{owner}")

    edges_raw = [
        {"source": a, "target": b, "weight": round(w, 2), "reasons": sorted(edge_reason[(a, b)])}
        for (a, b), w in edge_weight.items()
    ]

    # Prune: keep the strongest MAX_EDGES_PER_NODE_TARGET edges touching each
    # node so hub nodes (e.g. a huge shared topic) don't overwhelm layout,
    # while still keeping the graph connected via each node's best links.
    edges_raw.sort(key=lambda e: -e["weight"])
    keep_count = defaultdict(int)
    edges = []
    for e in edges_raw:
        a, b = e["source"], e["target"]
        if keep_count[a] >= MAX_EDGES_PER_NODE_TARGET and keep_count[b] >= MAX_EDGES_PER_NODE_TARGET:
            continue
        edges.append(e)
        keep_count[a] += 1
        keep_count[b] += 1

    connected = set()
    for e in edges:
        connected.add(e["source"])
        connected.add(e["target"])

    categories = sorted({n["category"] for n in nodes})
    meta = {
        "total_projects": len(nodes),
        "connected_projects": len(connected),
        "total_edges": len(edges),
        "total_stars": sum(n["stars"] for n in nodes),
        "categories": len(categories),
        "snapshot_date": "2026-08-30",
        "category_labels": CATEGORY_LABELS,
    }

    print(
        f"nodes={len(nodes)} edges={len(edges)} connected={len(connected)} "
        f"categories={len(categories)} total_stars={meta['total_stars']:,}"
    )
    with open("docs/data.json", "w") as f:
        json.dump({"nodes": nodes, "edges": edges, "meta": meta}, f)


if __name__ == "__main__":
    build()
