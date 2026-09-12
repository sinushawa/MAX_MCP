# TagManager entities: tagging objects by entity path

TagManager is a .NET utility plugin for 3ds Max that groups scene objects into a tree of
entities under `Root > Project`. Objects are tagged by an entity **path**: the branch names
joined with underscores, deepest last.

```
Building
Building_Floor1
Building_Floor1_Kitchen
Building_Floor1_Dining
```

Conventions the plugin enforces when its automations are on (they are on by default):

- **Auto-rename**: a tagged object is renamed to the path plus a unique suffix, e.g.
  `Building_Floor1_Kitchen_003`. Do not fight this by renaming afterwards.
- **Auto-layer**: a layer branch mirroring the entity branch is created and the object moves
  into the deepest layer, e.g. layer `Building_Floor1_Kitchen` under `Building_Floor1`.
- **Clone inheritance**: clones of a tagged object inherit its entities.
- Entities remember members by node handle for the session and by GUID in the .max file.

Prefer the MCP tools over raw MAXScript for entity work. Both go through the same facade.

## MCP tools (module `entities`)

```
entity_status                                    -- is TagManager loaded, thresholds, cache
list_entities                                    -- every path with depth and member counts
get_object_entities names:[...] handles:[...]    -- which entities own these objects
entity_bounds                                    -- world bbox per entity branch
entity_evidence names:[...] handles:[...]        -- features + containment candidates per object
request_entity_proposals handles:[...]           -- fresh evidence, session and per-object tokens
present_proposals proposals:[...] session:"..."   -- ranked candidates with tokens; review by default
review_entity_proposals                          -- open FastTag's inline suggestions
entity_automation action:start model:"..."        -- local Ollama ranking; stop/status also available
set_entity_zone path:"A_B" handles:[...]          -- optional volume bounds, current session only
pending_proposals action:list|accept|clear       -- what waits for confirmation in Max
apply_entity path:"A_B" names:[...] layer:true rename:true
remove_from_entity path:"A_B" names:[...]
```

Workflow for geometry the agent creates: create the object, then `apply_entity` with the path
the user works in. Read `list_entities` first so you extend the existing tree instead of
inventing a parallel one. A path that does not exist yet is created branch by branch.

Workflow for objects the user created: call `request_entity_proposals` on the new handles.
Use its session and per-object tokens when presenting ranked candidates. The background
worker can combine spatial evidence and confirmed neighbours and rank them with a local
model. Suggestions appear inside FastTag before typing and wait for confirmation by default.
Existing paths and new architectural paths issued in that object's evidence are accepted.
No prior entities are needed: geometry supplies provisional candidates for the first object.
Accepting a new path creates its hierarchy in one undo step. Bounds are axis-aligned and
`boundsVolumeM3` is bounding-box volume, not solid mesh volume; treat shape-only guesses as tentative.
After a stale-result rejection, request fresh evidence before presenting again.

## Evidence record

```json
{"handle":1943,"name":"Box001","class":"Box","mtl":"","layer":"0","parent":"",
 "bbox":[[2.175,1.975,0.2],[2.625,2.425,1.1]],"size":[0.45,0.45,0.9],"entities":[],
 "candidates":[
   {"path":"Building_Floor1_Kitchen","overlap":1,"depth":3,"sizeRatio":0.0337,"centerInside":true},
   {"path":"Building_Floor1","overlap":1,"depth":2,"sizeRatio":0.0017,"centerInside":true}]}
```

`overlap` is the fraction of the object's box inside the entity's branch box, `depth` the
path length, `sizeRatio` the object volume over the entity volume. Candidates come deepest
and best contained first. A large flat object such as a slab is never offered to a room it
would fill (`sizeRatio` above 0.5 is dropped).

## MAXScript facade, when a tool does not cover the case

```maxscript
api = dotNetClass "TagManager.TagApi"     -- static class, all methods return JSON strings
api.Version()
api.ListEntities()
api.GetEntities "1943,1950"               -- handles as a comma separated string
api.Evidence "1943"
api.Apply "Building_Floor1_Kitchen" "1943" true true    -- path, handles, layer, rename
api.Remove "Building_Floor1_Kitchen" "1943"
api.RequestEvidence "1943"                -- returns session and token for Present
api.ReviewProposals()
api.Pending(); api.AcceptPending 1943 0; api.ClearPending ""
api.InvalidateCache()                     -- after a scripted burst of transforms
```

Handles come from `$.inode.handle` or `(getNodeByName "Box001").inode.handle`. Every call
runs on the main thread and never throws; a failure is `{"ok":false,"error":"..."}`. Applies
and removes are one undo step each, including the entity membership itself.

If `api.Version()` reports `"initialized":false`, TagManager is not loaded in this session:
install `TagManager.dll` into `<3ds Max>\bin\assemblies`, or from a development checkout run
`fileIn "<repo>/TagManager/dev_load.ms"`.
