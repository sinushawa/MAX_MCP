"""TagManager entity tools — list, look up, apply, and gather evidence for entity proposals.

Python-only: every call is a one-line MAXScript that invokes the static
``TagManager.TagApi`` facade of the TagManager plugin through ``dotNetClass``. The facade
takes handles as a comma separated string and answers JSON, so nothing but strings crosses
the bridge. When TagManager is not loaded in the running Max, the facade reports
``initialized=false`` and these tools return that with a hint instead of guessing.

Entity paths are branch names joined by underscores, e.g. ``Building_Floor1_Kitchen``.
Objects can be addressed by scene name or by node handle; names are resolved inside Max so
one round trip covers both.
"""

from __future__ import annotations

import json

from ..coerce import DictList, IntList, StrList
from ..helpers.maxscript import safe_string
from ..server import client, mcp

_API = '(dotNetClass "TagManager.TagApi")'
_MAXSCRIPT_ERROR_SENTINEL = "__MCP_MS_ERR__:"
_LOAD_HINT = (
    "TagManager is not loaded in this 3ds Max session. Install TagManager.dll into "
    "<3ds Max>\\bin\\assemblies, or in a development checkout run "
    'fileIn "<TagManager repo>/TagManager/dev_load.ms" through execute_maxscript.'
)

# MAXScript that resolves scene names to handles, appends them to __csv, calls the facade,
# and wraps the answer with the names that did not resolve. Filled in by _targeted_script.
_RESOLVE_TEMPLATE = """(
local __csv = {csv}
local __missing = #()
for __n in {names} do (
  local __o = getNodeByName __n
  if __o == undefined then append __missing __n
  else __csv += (if __csv == "" then "" else ",") + (__o.inode.handle as string)
)
local __r = {call}
local __mj = "["
for __i = 1 to __missing.count do (
  if __i > 1 do __mj += ","
  __mj += "\\"" + (substituteString (substituteString __missing[__i] "\\\\" "\\\\\\\\") "\\"" "\\\\\\"") + "\\""
)
"{\\"missingNames\\":" + __mj + "],\\"api\\":" + __r + "}"
)"""


# ---------------------------------------------------------------- script building

def _ms_str(value: str) -> str:
    return '"' + safe_string(value or "") + '"'


def _ms_bool(value: bool) -> str:
    return "true" if value else "false"


def _handles_csv(handles: list[int] | None) -> str:
    seen: list[str] = []
    for h in handles or []:
        try:
            n = int(h)
        except (TypeError, ValueError):
            continue
        if n > 0 and str(n) not in seen:
            seen.append(str(n))
    return ",".join(seen)


def _call_script(method: str, *args: str) -> str:
    """``((dotNetClass "TagManager.TagApi").Method arg1 arg2)`` with pre-rendered args."""
    rendered = " ".join(args)
    if rendered:
        return f"({_API}.{method} {rendered})"
    return f"({_API}.{method}())"


def _targeted_script(
    method: str,
    names: list[str] | None,
    handles: list[int] | None,
    leading: tuple[str, ...] = (),
    trailing: tuple[str, ...] = (),
) -> str:
    """Resolve names to handles inside Max, then call ``method(*leading, csv, *trailing)``.

    Without names the call is direct. With names the script also reports the ones that did
    not resolve, wrapped as ``{"missingNames":[...],"api":<facade json>}``.
    """
    csv = _handles_csv(handles)
    if not names:
        return _call_script(method, *leading, _ms_str(csv), *trailing)
    name_array = "#(" + ", ".join(_ms_str(n) for n in names) + ")"
    call = " ".join([f"{_API}.{method}", *leading, "__csv", *trailing])
    return (
        _RESOLVE_TEMPLATE.replace("{csv}", _ms_str(csv))
        .replace("{names}", name_array)
        .replace("{call}", call)
    )


# ---------------------------------------------------------------- responses

def _error(message: str, **extra: object) -> str:
    payload: dict[str, object] = {"status": "error", "error": message}
    payload.update(extra)
    return json.dumps(payload)


def _run(script: str) -> str:
    response = client.send_command(script, cmd_type="maxscript")
    result = response.get("result", "")
    if isinstance(result, str) and result.startswith(_MAXSCRIPT_ERROR_SENTINEL):
        message = result[len(_MAXSCRIPT_ERROR_SENTINEL):].strip()
        extra: dict[str, object] = {"error_type": "MAXScriptError"}
        if "TagManager" in message or "dotNetClass" in message:
            extra["hint"] = _LOAD_HINT
        return _error(message, **extra)
    if not isinstance(result, str):
        result = json.dumps(result)
    try:
        data = json.loads(result)
    except ValueError:
        return _error("unexpected result from TagApi", raw=result[:500])
    if isinstance(data, dict) and "api" in data and "missingNames" in data:
        api = data["api"] if isinstance(data["api"], dict) else {"ok": False, "error": str(data["api"])}
        if data["missingNames"]:
            api["missingNames"] = data["missingNames"]
        data = api
    if isinstance(data, dict) and data.get("ok") is False:
        error = str(data.get("error", ""))
        if "not initialized" in error:
            data["hint"] = _LOAD_HINT
    return json.dumps(data)


def _require_targets(names: list[str] | None, handles: list[int] | None) -> str | None:
    if not names and not _handles_csv(handles):
        return _error("provide object names and/or handles")
    return None


# ---------------------------------------------------------------- tools

@mcp.tool()
def entity_status() -> str:
    """Report whether TagManager is loaded and how its facade is configured.

    Use when: an entity tool returned initialized=false, or before a batch of entity work.
    Not when: you only need the entity list — call list_entities directly.
    """
    return _run(_call_script("Version"))


@mcp.tool()
def list_entities() -> str:
    """List every TagManager entity below Project: path, depth, member and child counts.

    Use when: you need the existing entity paths before applying, proposing, or naming.
    Not when: you want the objects of one entity — use get_object_entities on candidates,
    or query_scene with the entity's layer.
    """
    return _run(_call_script("ListEntities"))


@mcp.tool()
def get_object_entities(names: StrList | None = None, handles: IntList | None = None) -> str:
    """Entity paths that own each given object (by scene name and/or node handle).

    Use when: checking whether objects are tagged, or which entity a selection belongs to.
    Not when: you want containment guesses for untagged objects — use entity_evidence.
    """
    missing = _require_targets(names, handles)
    if missing:
        return missing
    return _run(_targeted_script("GetEntities", names, handles))


@mcp.tool()
def entity_bounds() -> str:
    """World bounding box of every entity's branch (its objects plus descendants).

    Use when: building context for a ranker, or placing new geometry inside an entity.
    Not when: you need per-object boxes — inspect_object or entity_evidence carry those.
    """
    return _run(_call_script("EntityBounds"))


@mcp.tool()
def entity_evidence(names: StrList | None = None, handles: IntList | None = None) -> str:
    """Features and containment candidates for objects, the plugin half of an entity proposal.

    Per object: name, class, material, layer, parent, bbox, size, current entities, and
    candidates with overlap, depth, sizeRatio and centerInside. Candidates are ordered
    deepest and best contained first. Combine with neighbour votes and rank before applying.

    Use when: new objects appeared and you want to propose entities for them.
    Not when: the object is already tagged and you only need its path — get_object_entities.
    """
    missing = _require_targets(names, handles)
    if missing:
        return missing
    return _run(_targeted_script("Evidence", names, handles))


@mcp.tool()
def present_proposals(proposals: DictList, session: str = "", threshold: float | None = None) -> str:
    """Hand a ranked candidate list per object to TagManager.

    Each proposal is {"handle": 1943, "ranked": [{"path": "A_B", "confidence": 0.93, "reason": "..."}]}.
    Use session and each object's token from request_entity_proposals. Suggestions wait
    for review by default. Automatic application requires an explicit plugin opt-in.

    Use when: a ranker has ordered the candidates from entity_evidence.
    Not when: the user already told you the path — use apply_entity directly.
    """
    if not proposals:
        return _error("provide at least one proposal")
    if not session or any(not p.get("token") for p in proposals):
        return _error("provide session and proposal tokens from request_entity_proposals")
    payload: dict[str, object] = {"session": session, "proposals": list(proposals)}
    if threshold is not None:
        payload["threshold"] = float(threshold)
    return _run(_call_script("Present", _ms_str(json.dumps(payload))))


@mcp.tool()
def request_entity_proposals(handles: IntList) -> str:
    """Gather fresh evidence and request reviewable suggestions; returns session and tokens.

    The local worker adds neighbour evidence and LLM ranking when entity_automation is running.
    Tagged objects are skipped. Does not change membership, names or layers.
    """
    if not _handles_csv(handles):
        return _error("provide positive handles")
    return _run(_call_script("RequestEvidence", _ms_str(_handles_csv(handles))))


@mcp.tool()
def review_entity_proposals() -> str:
    """Open FastTag with inline suggestions for the current selection, before typing."""
    return _run(_call_script("ReviewProposals"))


@mcp.tool()
def set_entity_zone(path: str, handles: IntList | None = None) -> str:
    """Use explicit volume nodes for an entity's containment bounds in this session.

    Empty handles restores bounds inferred from member objects. Configure again after
    loading/resetting a scene. No geometry or tag membership is changed.
    """
    return _run(_call_script("SetEntityZone", _ms_str(path), _ms_str(_handles_csv(handles))))


@mcp.tool()
def entity_automation(action: str = "status", model: str = "", embedding_model: str = "nomic-embed-text") -> str:
    """Start, stop or inspect the session's background entity ranker using local Ollama.

    Start requires an installed chat model name. Plugin proposals remain review-only by
    default. Stop ends polling; an in-flight model request may finish but will not apply.
    """
    from ..entity_proposals import control
    return json.dumps(control(action, model, embedding_model))


@mcp.tool()
def pending_proposals(
    action: str = "list",
    handle: int = 0,
    index: int = 0,
    handles: IntList | None = None,
) -> str:
    """Proposals waiting for confirmation in TagManager.

    action:
      - "list" (default) — pending proposals with their ranked candidates
      - "accept" — apply candidate `index` (0 = top) of the proposal for `handle` and log it
      - "clear" — drop pending proposals for `handles`, or all when none are given

    Use when: reviewing or resolving what present_proposals left below the threshold.
    Not when: applying a path you already know — apply_entity.
    """
    action = (action or "list").strip().lower()
    if action == "list":
        return _run(_call_script("Pending"))
    if action == "accept":
        if int(handle) <= 0:
            return _error("accept needs a positive handle")
        return _run(_call_script("AcceptPending", str(int(handle)), str(int(index))))
    if action == "clear":
        return _run(_call_script("ClearPending", _ms_str(_handles_csv(handles))))
    return _error(f"unknown action: {action}", actions=["list", "accept", "clear"])


@mcp.tool()
def apply_entity(
    path: str,
    names: StrList | None = None,
    handles: IntList | None = None,
    layer: bool = True,
    rename: bool = True,
) -> str:
    """Put objects into an entity path, creating missing branches. One undo step in Max.

    layer moves the objects into the matching layer branch; rename applies TagManager's
    auto-rename (path prefix plus a unique suffix). Both follow the plugin's conventions.

    Use when: the entity for new or agent-created geometry is known.
    Not when: you are guessing — gather entity_evidence and rank first.
    """
    path = (path or "").strip()
    if not path:
        return _error("provide an entity path such as Building_Floor1_Kitchen")
    missing = _require_targets(names, handles)
    if missing:
        return missing
    return _run(
        _targeted_script(
            "Apply",
            names,
            handles,
            leading=(_ms_str(path),),
            trailing=(_ms_bool(layer), _ms_bool(rename)),
        )
    )


@mcp.tool()
def remove_from_entity(path: str, names: StrList | None = None, handles: IntList | None = None) -> str:
    """Take objects out of one entity path. One undo step in Max.

    Use when: an object was tagged into the wrong entity.
    Not when: you want to move it — apply_entity to the right path, then remove here.
    """
    path = (path or "").strip()
    if not path:
        return _error("provide an entity path")
    missing = _require_targets(names, handles)
    if missing:
        return missing
    return _run(_targeted_script("Remove", names, handles, leading=(_ms_str(path),)))
