#!/usr/bin/env python3
"""Pull LIVE GitHub data for the AI agent ecosystem map.

Two sources, merged and deduped by full_name:
  1. Topic/keyword search per category (breadth) via GET /search/repositories
  2. The hand-curated flagship list (accuracy for well-known projects) via GET /repos/{full}

Every project gets real, current metrics: stars, forks, open issues, language,
license, last-push date -> derived maintenance status and a simple momentum signal.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone

CATEGORIES = {
    "agent-frameworks": {
        "label": "Agent Frameworks & SDKs",
        "queries": [
            "topic:llm-agent", "topic:agent-framework", "topic:ai-agents",
            "topic:multi-agent", "topic:llm-framework", "agent framework in:name,description",
        ],
        "curated": [
            "langchain-ai/langchain", "langchain-ai/langgraph", "crewAIInc/crewAI",
            "microsoft/autogen", "microsoft/semantic-kernel", "run-llama/llama_index",
            "deepset-ai/haystack", "RasaHQ/rasa", "anthropics/claude-agent-sdk-python",
            "openai/openai-agents-python", "google/adk-python", "pydantic/pydantic-ai",
            "agno-agi/agno", "huggingface/smolagents", "stanfordnlp/dspy",
            "griptape-ai/griptape", "letta-ai/letta", "ag2ai/ag2", "OpenBMB/XAgent",
            "openai/swarm",
        ],
    },
    "autonomous-agents": {
        "label": "Autonomous & General-Purpose Agents",
        "queries": [
            "topic:autonomous-agents", "topic:autogpt", "topic:ai-agent",
            "topic:coding-assistant", "autonomous agent in:name,description",
        ],
        "curated": [
            "Significant-Gravitas/AutoGPT", "yoheinakajima/babyagi", "reworkd/AgentGPT",
            "TransformerOptimus/SuperAGI", "All-Hands-AI/OpenHands", "AntonOsika/gpt-engineer",
            "geekan/MetaGPT", "OpenBMB/ChatDev", "Aider-AI/aider", "SWE-agent/SWE-agent",
            "OpenInterpreter/open-interpreter", "browser-use/browser-use", "Skyvern-AI/skyvern",
            "stitionai/devika", "Pythagora-io/gpt-pilot", "Josh-XT/AGiXT",
            "openai/codex", "cline/cline",
        ],
    },
    "agent-protocols-infra": {
        "label": "Protocols, Orchestration & Infrastructure",
        "queries": [
            "topic:mcp", "topic:model-context-protocol", "topic:agent-orchestration",
            "topic:mcp-server", "topic:workflow-orchestration",
        ],
        "curated": [
            "modelcontextprotocol/servers", "modelcontextprotocol/python-sdk",
            "google-a2a/A2A", "langchain-ai/langserve", "ray-project/ray",
            "temporalio/temporal", "e2b-dev/e2b", "CopilotKit/CopilotKit",
            "ComposioHQ/composio",
        ],
    },
    "agent-memory-tools": {
        "label": "Memory, RAG & Retrieval",
        "queries": [
            "topic:rag", "topic:vector-database", "topic:retrieval-augmented-generation",
            "topic:vector-search", "topic:embeddings",
        ],
        "curated": [
            "mem0ai/mem0", "getzep/zep", "chroma-core/chroma", "weaviate/weaviate",
            "qdrant/qdrant", "milvus-io/milvus", "neuml/txtai", "jxnl/instructor",
            "guardrails-ai/guardrails", "facebookresearch/faiss", "BerriAI/litellm",
        ],
    },
    "agent-eval-observability": {
        "label": "Evaluation & Observability",
        "queries": [
            "topic:llm-evaluation", "topic:llmops", "topic:ai-observability",
            "topic:prompt-engineering", "topic:llm-observability",
        ],
        "curated": [
            "langfuse/langfuse", "Helicone/helicone", "promptfoo/promptfoo",
            "confident-ai/deepeval", "explodinggradients/ragas", "THUDM/AgentBench",
            "Arize-ai/phoenix", "truera/trulens", "openai/evals", "AgentOps-AI/agentops",
            "traceloop/openllmetry", "Giskard-AI/giskard",
        ],
    },
    "coding-agents": {
        "label": "Coding Agents & Dev Tools",
        "queries": [
            "topic:ai-coding-assistant", "topic:coding-agent", "topic:code-generation",
            "topic:developer-tools topic:llm", "topic:ai-code-review",
        ],
        "curated": [
            "anthropics/claude-code", "continuedev/continue", "sweepai/sweep",
            "plandex-ai/plandex", "stackblitz/bolt.new", "sst/opencode",
        ],
    },
    "multi-agent-simulation": {
        "label": "Multi-Agent Simulation & Research",
        "queries": [
            "topic:multi-agent-systems", "topic:generative-agents",
            "topic:reinforcement-learning topic:agents", "topic:agent-simulation",
        ],
        "curated": [
            "joonspk-research/generative_agents", "camel-ai/camel", "OpenBMB/AgentVerse",
            "microsoft/JARVIS", "MineDojo/Voyager", "Farama-Foundation/chatarena",
            "google-deepmind/concordia", "py499372727/AgentSims", "cuijiaxun/MindAgent",
        ],
    },
}


def gh_api(path, params=None, retries=4):
    args = ["gh", "api", "--method", "GET", path]
    if params:
        for k, v in params.items():
            args += ["-f", f"{k}={v}"]
    for attempt in range(retries):
        try:
            out = subprocess.run(args, capture_output=True, text=True, timeout=30)
            if out.returncode == 0:
                return json.loads(out.stdout)
            sys.stderr.write(f"  attempt {attempt+1} failed: {out.stderr[:200]}\n")
        except Exception as e:
            sys.stderr.write(f"  attempt {attempt+1} exception: {e}\n")
        time.sleep(2 + attempt * 2)
    return None


def shape_repo(r):
    if not r or r.get("message") == "Not Found":
        return None
    pushed = r.get("pushed_at")
    days_since_push = None
    if pushed:
        dt = datetime.strptime(pushed, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        days_since_push = (datetime(2026, 8, 30, tzinfo=timezone.utc) - dt).days
    license_info = r.get("license") or {}
    return {
        "name": r["name"],
        "full_name": r["full_name"],
        "description": (r.get("description") or "").strip(),
        "url": r["html_url"],
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "open_issues": r.get("open_issues_count", 0),
        "watchers": r.get("subscribers_count", r.get("watchers_count", 0)),
        "language": r.get("language"),
        "license": license_info.get("spdx_id") if license_info.get("spdx_id") not in (None, "NOASSERTION") else None,
        "archived": bool(r.get("archived")),
        "created_at": r.get("created_at"),
        "pushed_at": pushed,
        "days_since_push": days_since_push,
        "topics": r.get("topics", []),
    }


def main():
    seen = {}
    for key, cat in CATEGORIES.items():
        print(f"=== {key} ===", file=sys.stderr)

        # 1) curated flagships - authoritative live data
        for full in cat["curated"]:
            if full in seen:
                continue
            print(f"  curated: {full}", file=sys.stderr)
            r = gh_api(f"repos/{full}")
            shaped = shape_repo(r)
            if shaped:
                shaped["category"] = key
                seen[full] = shaped
            time.sleep(0.3)

        # 2) topic search - breadth
        for q in cat["queries"]:
            print(f"  search: {q}", file=sys.stderr)
            res = gh_api("search/repositories", {"q": q, "sort": "stars", "order": "desc", "per_page": 100})
            time.sleep(2.2)  # search API: 30 req/min
            if not res or "items" not in res:
                continue
            for r in res["items"]:
                full = r["full_name"]
                if full in seen:
                    continue
                shaped = shape_repo(r)
                if shaped and shaped["stars"] >= 80:
                    shaped["category"] = key
                    seen[full] = shaped

    projects = list(seen.values())
    print(f"\nTotal unique projects: {len(projects)}", file=sys.stderr)
    with open("docs/raw_live_data.json", "w") as f:
        json.dump(projects, f, indent=2)


if __name__ == "__main__":
    main()
