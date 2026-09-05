# CLAUDE.md — working notes for this fork

This is a personal fork of [cl0nazepamm/3dsmax-mcp](https://github.com/cl0nazepamm/3dsmax-mcp)
(MIT, forked at v1.5.5), an MCP server that lets AI clients control Autodesk 3ds Max.
Read `README.md` for the upstream feature set and `docs/ADVANCED.md` for configuration.
This file records what the fork adds, how the owner's machines are set up, and how to
continue the work.

## Remotes and branches

- `origin` = `https://github.com/sinushawa/MAX_MCP.git` (this fork). Work happens on `main`.
- `upstream` = `https://github.com/cl0nazepamm/3dsmax-mcp.git`. Local `master` tracks
  `upstream/master` and carries no fork changes; use it to merge upstream updates into `main`.
- `feature/module-filter` is the historical branch the fork work started on; `main` supersedes it.

## What the fork adds on top of upstream

| Area | Files | Notes |
|---|---|---|
| Per-module tool filter | `maxmcp/server.py` (`filter_tool_modules`, `active_tool_modules`), `maxmcp/tool_discovery.py` (`restrict_toolsets`) | `[mcp] disabled_modules` / `enabled_modules` in the user ini, or `MCP_DISABLED_MODULES` / `MCP_ENABLED_MODULES` env vars. Works in core, full, and progressive profiles. |
| In-Max settings window | `maxscript/mcp_settings.ms` | Macro **MCP Settings** (category MCP): checkbox per module, profile, safe mode. Its module tables must list every module in `CORE_TOOL_MODULES` + `SPECIALTY_TOOL_MODULES` (a test enforces this). Bundled by `install.py`. |
| Local MAXScript reference retrieval | `maxmcp/docsearch/` (index, proxy, CLI), `maxmcp/tools/docs_search.py`, `Docs Proxy.bat` | Indexes `skills/3dsmax-mcp-dev/*.md` with Ollama embeddings. `search_maxscript_docs` tool for external clients; an OpenAI-compatible proxy on port 11435 injects retrieved chunks into the in-Max chat's system prompt (that chat can only call native tools, never Python ones). |
| V-Ray 7 reference | `skills/3dsmax-mcp-dev/maxscript-vray.md` | Property names harvested from V-Ray 7.40.04 with `getPropNames` in 3ds Max 2025. Re-harvest when V-Ray updates (script pattern: run `getPropNames` per class under `3dsmaxbatch.exe`). |
| Error hints / descriptions | `maxmcp/helpers/error_hints.py`, `maxmcp/tools/execute.py` | Edit Poly / sub-object scripts that fail now suggest `search_maxscript_docs` and introspection instead of retrying. |
| Installer fix | `install.py` (`sync_tree`) | Bundle is synced file by file. Upstream deleted the whole package first; a running Max locks `mcp_bridge_<year>.gup`, and the failed delete left the package without its scripts. |
| Tool reference | `docs/TOOLS.md` | Generated from `tool_playground/catalog.json`; regenerate with `scripts/gen_tool_catalog.py` then the snippet in git history of that doc. |

## Owner's environment (primary machine)

- Windows 11, 3ds Max 2025 is the working version (2026 and 2027 also installed).
- Renderer: V-Ray 7 update 4 hotfix 2 (CPU and GPU). Forest Pack, RailClone, tyFlow are
  installed but their tool modules are disabled by choice.
- Python 3.12, `uv`, Ollama 0.33 with `qwen3.8:latest` (chat), `ornith-1.5:9b`,
  `nomic-embed-text` (embeddings). No `gh` CLI; git uses the Windows credential manager.
- Claude Code registration: `claude mcp add --scope user 3dsmax-mcp -- uv run --directory <repo> 3dsmax-mcp`.

Chosen runtime config in `%LOCALAPPDATA%\3dsmax-mcp\mcp_config.ini` (not in git):

```ini
[mcp]
safe_mode = true
tool_profile = full
disabled_modules = chat, tyflow, tyflow_graph, tyflow_patch, tyflow_manifest, tyflow_census, railclone, scattering, floor_plan, data_channel, mcg
enabled_modules =

[llm]                     ; in-Max chat window only
base_url = http://localhost:11435/v1   ; the docs proxy; Ollama itself is 11434
model = qwen3.8:latest
prompt_mode = full
tool_profile = core
```

`%LOCALAPPDATA%\3dsmax-mcp\.env` holds `LLM_API_KEY=ollama` (placeholder: the native chat
refuses to start without a key, Ollama ignores it). Never commit real keys.

## Setting up on a new machine

```powershell
git clone https://github.com/sinushawa/MAX_MCP.git MaxMCP
cd MaxMCP
git remote add upstream https://github.com/cl0nazepamm/3dsmax-mcp.git
uv sync
uv run python install.py --tool-profile full      # answer "1" (project) at the skills prompt
# then edit %LOCALAPPDATA%\3dsmax-mcp\mcp_config.ini as above, restart 3ds Max
uv run python -m maxmcp.docsearch build           # needs Ollama + nomic-embed-text
"Docs Proxy.bat"                                  # keep running while using MCP Chat
```

Run tests with `uv run --with pytest python -m pytest tests -q`. Tests are offline; nothing
touches a real Max scene. Launch tests spawn the server, so keep the module-filter env vars
pinned as the existing tests do.

## Operational facts that cost time to rediscover

- With several Max windows open the server refuses to guess: run **MCP Claim This Max** in
  the target window. The claim dies with that process.
- After any change to `maxscript/*.ms` or the bundle, run `install.deploy_application_package()`
  (or `install.py`) and restart Max; scripts load at startup only.
- The in-Max chat exposes only tools with a native C++ handler. Python-only tools are
  skipped by `scripts/gen_tool_registry.py`, so knowledge for that chat has to come through
  the prompt or the proxy, not through new Python tools.
- Retrieval fixes API knowledge (wrong property names) but not planning; small local models
  still loop on errors. Prefer Claude Code through the same bridge for mesh editing.
- `execute_maxscript` code is un-escaped once in transit: use forward slashes in paths.
- 3ds Max scene units on the owner's files are meters; "20 cm" is 0.2 units.

## Conventions

- Keep changes mergeable with upstream: additive modules, no renames of upstream files.
- Every behaviour change gets a test next to the existing ones in `tests/`.
- Commit messages: imperative summary line, body explaining why, ending with
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` when Claude wrote the change.
- Do not commit `.agents/`, `AGENTS.md`, `.env`, or anything under `%LOCALAPPDATA%`.

## Open ideas, in rough priority

1. A `poly_operation` tool wrapping Edit Poly extrude / bevel / inset / chamfer, so small
   models never need MAXScript for common mesh edits.
2. A V-Ray render-settings tool (sampler, GI, output, render elements) on top of
   `maxscript-vray.md`.
3. Extend `MODULE_CATEGORY` in `scripts/gen_tool_catalog.py`: 18 newer modules fall into
   "Other" and their risk labels default to "read" even when they mutate.
4. Add own V-Ray / archviz notes to the index with `docsearch build --extra <folder>`.
