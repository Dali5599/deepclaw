#!/usr/bin/env python3
"""
DeepClaw CLI - Autonomous Deep Research Terminal Client
"""
import sys
import argparse
import asyncio
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api.streaming import generate_research_stream
from backend.core import settings, get_llm_router

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner():
    print(f"{CYAN}")
    print(" ╔═══════════════════════════════════════════════════════════════╗")
    print(" ║   🦈 DEEPCLAW — Autonomous Deep Research Terminal Engine      ║")
    print(" ╚═══════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

async def run_cli_research(topic: str, depth: int = 2, output_file: str = None):
    print_banner()
    router = get_llm_router()
    providers = router.get_available_providers()
    prov_str = ", ".join(providers) if providers else "Fallback Mock Engine"

    print(f"[{GREEN}INFO{RESET}] Topic          : {BOLD}{topic}{RESET}")
    print(f"[{GREEN}INFO{RESET}] Research Depth : {depth}")
    print(f"[{GREEN}INFO{RESET}] Active LLMs    : {prov_str}")
    print(f"[{YELLOW}LIVE{RESET}] Launching multi-source recursive investigation...\n")

    events = []
    sources = []
    facts = []

    async for event in generate_research_stream(topic, max_depth=depth):
        events.append(event)
        etype = event.get("type")

        if etype == "research_started":
            print(f" {CYAN}▶{RESET} Research Session Initialized (ID: {event.get('session_id')})")
        elif etype == "search_level":
            print(f"\n{BOLD}━━━ Depth Level {event.get('level')} Investigation ━━━{RESET}")
            print(f"  Query: {event.get('query')}")
        elif etype == "source_collected":
            sources.append(event)
            print(f"  {GREEN}✓{RESET} Source [{event.get('relevance')}]: {event.get('title')} ({event.get('url')})")
        elif etype == "fact_extracted":
            facts.append(event)
            print(f"    {YELLOW}•{RESET} Fact Extracted: {event.get('content')} (Conf: {event.get('confidence')})")
        elif etype == "contradiction_found":
            print(f"    {RED}⚠{RESET} Contradiction: {event.get('description')}")
        elif etype == "synthesis_complete":
            print(f"\n{BOLD}{GREEN}═══ FINAL SYNTHESIS COMPLETED ═══{RESET}")
            print(f"{event.get('summary')}\n")
            print(f"{BOLD}Key Findings:{RESET}")
            for k in event.get("key_findings", []):
                print(f"  • {k}")

    print(f"\n[{GREEN}COMPLETE{RESET}] Indexed {len(sources)} sources, extracted {len(facts)} sovereign facts.")

    if output_file:
        out_path = Path(output_file)
        report_data = {
            "topic": topic,
            "depth": depth,
            "sources_count": len(sources),
            "facts_count": len(facts),
            "sources": sources,
            "facts": facts,
            "events": events
        }
        out_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"[{GREEN}SAVED{RESET}] Report written to {out_path.resolve()}")

def main():
    parser = argparse.ArgumentParser(description="DeepClaw Autonomous Deep Research Engine CLI")
    parser.add_argument("topic", type=str, help="Research topic or thesis statement")
    parser.add_argument("--depth", "-d", type=int, default=2, help="Research depth level (1-3, default: 2)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output JSON/Markdown report path")
    args = parser.parse_args()

    asyncio.run(run_cli_research(args.topic, depth=args.depth, output_file=args.output))

if __name__ == "__main__":
    main()
