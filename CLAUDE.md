# CLAUDE.md — working notes for this fork

This is a personal fork of [cl0nazepamm/3dsmax-mcp](https://github.com/cl0nazepamm/3dsmax-mcp)
(MIT, forked at v1.5.5, upstream v1.6.6 merged on 2026-09-05), an MCP server that lets AI clients control Autodesk 3ds Max.
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
| Local MAXScript reference retrieval | `maxmcp/docsearch/` (index, proxy, CLI), `maxmcp/tools/docs_search.py`, `Docs Proxy.bat` | Indexes `skills/3dsmax-mcp-dev/*.md` with Ollama embeddings. `search_maxscript_docs` tool for external clients. The OpenAI-compatible proxy on port 11435 was built for the in-Max chat, which upstream removed in 1.6.6; it still works for any local OpenAI-compatible client but nothing in Max uses it now. |
| V-Ray 7 reference | `skills/3dsmax-mcp-dev/maxscript-vray.md` | Property names harvested from V-Ray 7.40.04 with `getPropNames` in 3ds Max 2025. Re-harvest when V-Ray updates (script pattern: run `getPropNames` per class under `3dsmaxbatch.exe`). |
| Error hints / descriptions | `maxmcp/helpers/error_hints.py`, `maxmcp/tools/execute.py` | Edit Poly / sub-object scripts that fail now suggest `search_maxscript_docs` and introspection instead of retrying. |
| Installer fix | `install.py` (`sync_tree`) | Bundle is synced file by file. Upstream deleted the whole package first; a running Max locks `mcp_bridge_<year>.gup`, and the failed delete left the package without its scripts. |
| Tool reference | `docs/TOOLS.md`, `scripts/gen_tools_doc.py` | Generated from `tool_playground/catalog.json`; regenerate with `scripts/gen_tool_catalog.py` then `scripts/gen_tools_doc.py`. |
| Tracked tests | `tests/` | Upstream stopped tracking its tests in 1.6.6 (`/tests/` gitignored). The fork keeps them tracked and removed only the ones for features upstream deleted (chat, builder). |

## Owner's environment (primary machine)

- Windows 11, 3ds Max 2025 is the working version (2026 and 2027 also installed).
- Renderer: V-Ray 7 update 4 hotfix 2 (CPU and GPU). Forest Pack, RailClone, tyFlow are
  installed but their tool modules are disabled by choice.
- Python 3.12, `uv`, Ollama 0.33 with `qwen3.8:latest` (chat), `ornith-1.5:9b`,
  `nomic-embed-text` (embeddings). No `gh` CLI; git uses the Windows credential manager.
- Claude Code registration: `claude mcp add --scope user 3dsmax-mcp -- uv run --directory <repo> 3dsmax-mcp`.

Chosen runtime config in `%LOCALAPPDATA%dsmax-mcp\mcp_config.ini` (not in git):

```ini
[mcp]
safe_mode = true
tool_profile = full
disabled_modules = tyflow, tyflow_graph, tyflow_patch, tyflow_manifest, tyflow_census, railclone, scattering, data_channel, mcg
enabled_modules =
```

The `[llm]` section and `.env` key that the in-Max chat used are gone with upstream 1.6.6;
leftovers in an existing ini are ignored. Never commit real keys.

## Setting up on a new machine

```powershell
git clone https://github.com/sinushawa/MAX_MCP.git MaxMCP
cd MaxMCP
git remote add upstream https://github.com/cl0nazepamm/3dsmax-mcp.git
uv sync
uv run python install.py --tool-profile full      # answer "1" (project) at the skills prompt
# then edit %LOCALAPPDATA%\3dsmax-mcp\mcp_config.ini as above, restart 3ds Max
uv run python -m maxmcp.docsearch build           # needs Ollama + nomic-embed-text
```

Run tests with `uv run --with pytest python -m pytest tests -q`. Tests are offline; nothing
touches a real Max scene. Launch tests spawn the server, so keep the module-filter env vars
pinned as the existing tests do.

## Operational facts that cost time to rediscover

- With several Max windows open the server refuses to guess: run **MCP Claim This Max** in
  the target window. The claim dies with that process.
- After any change to `maxscript/*.ms` or the bundle, run `install.deploy_application_package()`
  (or `install.py`) and restart Max; scripts load at startup only.
- Upstream 1.6.6 removed the standalone in-Max chat (native `chat_ui`, `llm_client`, the
  `chat` tool module) and the `build_floor_plan` tool, and added curve/mesh modeling tools plus
  an agent viewport. The rebuilt `.gup` binaries ship with it; redeploy the bundle after merging.
- Retrieval fixes API knowledge (wrong property names) but not planning; small local models
  still loop on errors. Prefer Claude Code through the bridge for mesh editing.
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
   models never need MAXScript for common mesh edits. Check upstream's new `mesh_edit` and
   `poly_edit` first; 1.6.6 may already cover part of this.
2. A V-Ray render-settings tool (sampler, GI, output, render elements) on top of
   `maxscript-vray.md`.
3. Extend `MODULE_CATEGORY` in `scripts/gen_tool_catalog.py`: 18 newer modules fall into
   "Other" and their risk labels default to "read" even when they mutate.
4. Add own V-Ray / archviz notes to the index with `docsearch build --extra <folder>`.
