# Entity suggestions: implementation and operation

Requires the TagManager plugin with TagApi 1.2 and the `entities` MCP module.

## Use

1. Load the rebuilt TagManager DLL in a fresh Max session. Development loading:
   `fileIn "D:/github/TagManager/TagManager/dev_load.ms"`.
2. Create an object and open FastTag. Its existing autocomplete dropdown offers architectural
   paths immediately, with the text field still empty. No separate panel or button is used.
   No existing tags or example objects are required. With no objects selected, it shows
   starter paths for browsing; there is nothing to classify until an object exists.
3. Use Down/Up to choose a suggestion and Enter (or `/`) to apply it. Enter on untouched
   empty input accepts the first suggestion. Missing hierarchy branches are created in the
   same undo step. Escape dismisses FastTag. Once typing begins, the original filtering,
   Enter-to-select and slash-to-tag behaviour remains in use.
4. Start semantic ranking with `entity_automation(action="start", model="ministral-3:3b")`,
   using an installed Ollama chat model. The default embedding model is `nomic-embed-text`.
   `status` reports work and errors; `stop` prevents delivery of further results.
5. For existing untagged objects use `request_entity_proposals(handles=[...])`.

The worker belongs to the MCP server process. Reconnects require starting it again.
For a standalone worker: `uv run python -m maxmcp.entity_proposals --model ministral-3:3b`.
Run only one worker for a Max session. No service, scheduled task or global startup entry
is installed by this change.

## Flow

Creation notifications only queue handles. A background-priority Max dispatcher timer
waits at least 750 ms and prepares bounded batches. It skips tagged objects, waits during
merge/undo holds, and excludes target/camera/helper class names from automatic suggestions.
Class-name exclusions are a first-pass filter, not an exhaustive SDK superclass classifier.

Architectural geometry priors, spatial and nearest-neighbour candidates are merged by path. Semantic candidates can
enter without spatial overlap. Neighbours compare original name, class, material and
numerical proportions; only human-confirmed examples from the current scene session are
used. Automatic decisions and old records without evidence are excluded. Undoing an
assignment retracts its learning example. Redo does not silently re-train it.

The local model ranks at most twelve candidates into three suggestions. Output paths,
confidence bounds and duplicate entries are validated. Model failure leaves the provisional
shape/spatial result visible. Model confidence does not authorize a scene edit. Proposed
new paths must be present in the object's evidence ticket, and always require confirmation.

## Architecture without training examples

World bounding dimensions are converted from Max system units to metres. Broad thin forms
offer slabs/floors/paving; thin upright forms offer walls/partitions/glazing; slender upright
forms offer columns; elongated horizontal forms offer beams; large masses offer building
volumes/halls/concourses/galleries. Compact forms offer furniture and museum display elements.
Paths such as `Building_Structure_Slabs` become real nested branches only on acceptance.
An existing entity with the same leaf name is preferred over creating a parallel default path.

These are deliberately tentative geometry priors, not semantic recognition. The reported
`boundsVolumeM3` is bounding-box volume, not solid mesh volume. World-axis-aligned boxes
can be distorted by rotation. An LLM can refine ordering with names/materials and confirmed
examples, but cannot reliably distinguish a museum from an office using a box alone.

FastTag reuses the bundled dragonz.actb popup via a small reflection adapter because that
library exposes no public empty-input opening method. Updating that dependency requires
retesting `PopulatePopupList` and `_listBox`. Model updates never replace text after typing
or arrow navigation has begun. Multi-selection offers only candidates shared by all selected
objects and prevalidates the complete selection before one undoable apply.

## Lifecycle and review

- Review is the default. `AutoApplyEnabled` is false. Existing callers of `Present` must
  now send the session and per-object tokens returned by `RequestEvidence`/`ProposalBatch`.
- Tokens identify the latest request. Before presenting or accepting, the plugin checks
  scene identity, a two-minute expiry, entity tree and freshly collected evidence.
- Scene reset/open clears pending work and bounds; node deletion removes its pending work.
- Tag membership, layer/name changes and newly created branches participate in undo.
- Decision records include the evidence captured before applying the label, plus session
  and decision kind. Ignoring a suggestion invalidates its token.

## Optional zones

`set_entity_zone(path="Building_Kitchen", handles=[...])` uses explicit volume nodes for
that entity's world axis-aligned bounds. Empty handles restores inferred member bounds.
This is an AABB approximation, not a point-in-solid room test. Bindings currently last for
the scene session only; reconfigure them after reset/open. Nodes are not retagged or hidden.

## Performance and current limits

- No model or embedding work runs on Max's main thread. Bridge calls from the worker
  are serialized, with 500 ms polling and one outstanding ranking job.
- Chat requests explicitly use a 4,096-token context. This machine's 131,072-token
  default allocated about 13 GB of KV cache for the 3B model and timed out during loading.
  Separate warmup allows 60 seconds; ranking requests allow 20 seconds. A successful
  synthetic test with `ministral-3:3b` took 3.1 seconds initially and 475 ms on repeat.
- Embeddings are batched and cached by feature text for the worker lifetime. At most
  2,000 confirmed examples are retained; the log reloads only when its file changes.
- Fresh evidence deliberately bypasses the old five-second cache between requests.
  Boxes are reused within a batch. This prioritizes correct move/time handling; large
  scenes still need measured, event-driven invalidation and a spatial index.
- Ranking is sequential per object within a batch; cold model startup and large imports
  can outlive the ticket. Expired answers are rejected. Use smaller batches and inspect
  worker latency before scaling up.
- Learning is scoped to the current scene session. Cross-session learning needs persistent
  object/project identity and versioned storage; it is not inferred from reused handles.
- The existing BinaryFormatter persistence format is unchanged.

## Verification

Offline tests cover semantic candidates outside spatial bounds, invalid model output,
exclusion of unconfirmed examples, avoidance of generated-layer leakage and model outages.
Live checks should additionally cover a moved object, an ignored ticket, reset/load,
accept/undo/redo, creation batches and inline FastTag on a representative scene.

On 2026-09-12 the API 1.2 plugin built successfully and 444 offline tests passed, including
empty-tree architectural ranking and metric evidence propagation. The earlier API 1.1 explicit
live smoke passed review-only delivery, moved/ignored ticket rejection, membership and
branch undo/redo, creation callbacks and opening the review window. Running it with
`ministral-3:3b` also delivered ranked proposals through the background worker (last batch
788 ms). Tests removed their temporary objects and entity branches. Reset/open handling
and large production scenes still need dedicated live coverage.

API 1.2 verification status: the standalone geometry regression passes six shape families,
XY-axis invariance and invalid/zero dimensions. On this machine, 100,000 geometry-prior
classifications took 37–38 ms; this excludes SDK bounds collection, serialization and UI work.
The installed API 1.1 DLL could not be replaced because Windows administrator consent was
canceled. Consequently API 1.2 live UI/acceptance tests have not yet run; an API 1.1 session
cannot validate the new autocomplete behaviour.

After installing the rebuilt DLL and restarting Max into an empty test session:

```powershell
./tests/build_tagmanager_probes.ps1
uv run python tests/live_fasttag.py
uv run python tests/live_entity_proposals.py ministral-3:3b
```

The first live test checks the empty-scene starter list, a metric slab with no prior tags,
blank-input popup, arrow/Enter acceptance, hierarchy undo/redo and typed filtering. It refuses
to run on a populated scene or entity tree. Probe binaries and screenshots stay under ignored
`local/tagmanager-tests`. Windows installation backup for this attempt is in
`%TEMP%/TagManager_before_inline_20260912_160136/TagManager.dll`.
