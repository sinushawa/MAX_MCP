"""Render docs/TOOLS.md from tool_playground/catalog.json.

Run scripts/gen_tool_catalog.py first, then:

    uv run python scripts/gen_tools_doc.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tool_playground" / "catalog.json"
OUT = ROOT / "docs" / "TOOLS.md"

sys.path.insert(0, str(ROOT))
from maxmcp.server import CORE_TOOL_MODULES  # noqa: E402

RISK_ORDER = ("advanced", "safe", "read", "changes_scene")

HEADER = """# 3dsmax-mcp tool reference

Generated from `tool_playground/catalog.json` (v{version}). {count} tools.

**Profile**: `core` tools are exposed in both the core and full profiles; `full` tools only in the full profile. **Risk**: `safe` and `read` do not change the scene, `changes_scene` mutates it, `advanced` runs arbitrary or destructive operations. **Routing**: `native` goes through the C++ bridge, `maxscript` sends generated MAXScript, `python` is handled server-side or composes other tools.

## Summary

| Group | Tools |
|---|---|
"""


def profile_of(tool: dict) -> str:
    return "core" if tool["module"] in CORE_TOOL_MODULES else "full"


def routing_of(tool: dict) -> str:
    return str(tool.get("routing", "python")).split(":", 1)[0]


def table(tools: list[dict]) -> str:
    lines = ["| Tool | Description | Profile | Risk | Routing |", "|---|---|---|---|---|"]
    for tool in tools:
        desc = " ".join(str(tool.get("description", "")).split())
        lines.append(
            f"| `{tool['name']}` | {desc} | {profile_of(tool)} | {tool['risk']} | {routing_of(tool)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    catalog = json.loads(CATALOG.read_text("utf-8"))
    by_name = {tool["name"]: tool for tool in catalog["tools"]}
    placed: set[str] = set()

    sections: list[tuple[str, list[tuple[str, list[dict]]]]] = []
    for group in catalog["groups"]:
        categories = []
        for category in group["categories"]:
            tools = [by_name[name] for name in category["tools"] if name in by_name]
            placed.update(tool["name"] for tool in tools)
            if tools:
                categories.append((category["name"], tools))
        if categories:
            sections.append((group["name"], categories))

    other = [tool for name, tool in by_name.items() if name not in placed]
    if other:
        categories: dict[str, list[dict]] = {}
        for tool in other:
            categories.setdefault(tool.get("category", "Other"), []).append(tool)
        sections.append(
            ("Other", [(name, sorted(tools, key=lambda t: t["name"])) for name, tools in sorted(categories.items())])
        )

    out = HEADER.format(version=catalog["version"], count=len(by_name))
    for name, categories in sections:
        out += f"| {name} | {sum(len(tools) for _, tools in categories)} |\n"

    profiles = Counter(profile_of(tool) for tool in by_name.values())
    risks = Counter(tool["risk"] for tool in by_name.values())
    risk_text = ", ".join(f"{risk} {risks[risk]}" for risk in RISK_ORDER if risks.get(risk))
    out += f"\nBy profile: core {profiles['core']}, full-only {profiles['full']}. By risk: {risk_text}.\n\n"

    for name, categories in sections:
        out += f"\n## {name}\n\n"
        for category, tools in categories:
            out += f"\n### {category}\n\n{table(tools)}"

    OUT.write_text(out, "utf-8")
    print(f"[gen_tools_doc] wrote {len(by_name)} tools -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
