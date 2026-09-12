# 3dsmax-mcp tool reference

Generated from `tool_playground/catalog.json` (v2). 173 tools.

**Profile**: `core` tools are exposed in both the core and full profiles; `full` tools only in the full profile. **Risk**: `safe` and `read` do not change the scene, `changes_scene` mutates it, `advanced` runs arbitrary or destructive operations. **Routing**: `native` goes through the C++ bridge, `maxscript` sends generated MAXScript, `python` is handled server-side or composes other tools.

## Summary

| Group | Tools |
|---|---|
| Setup | 3 |
| Scene | 5 |
| Objects | 25 |
| Materials | 19 |
| Inspect | 17 |
| Animation | 9 |
| Viewport & Render | 6 |
| Files | 4 |
| Specialty | 44 |
| Advanced | 4 |
| Other | 37 |

By profile: core 101, full-only 72. By risk: advanced 57, safe 39, read 43, changes_scene 34.


## Setup


### Connection

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `get_bridge_status` | Ping the MCP bridge for protocol/transport metadata. | core | safe | python |
| `get_plugin_capabilities` | Get 3ds Max version, available renderers, installed plugins, and class counts. | core | safe | native |

### Session

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `get_session_context` | Bundle bridge, capabilities, scene overview, and selection in one call. | core | safe | python |

## Scene


### Scene

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `get_dependencies` | Trace the reference graph for an object using refs.dependents / refs.dependentnodes. | core | safe | native |
| `get_instances` | Get all instances (copies sharing the same base object) of a scene object. | core | safe | native |
| `manage_scene` | Manage the 3ds Max scene state. | core | read | native |
| `query_scene` | Unified scene query. action: overview | filter | class | property | selection | delta. | core | safe | python |
| `undo_last` | Undo the last 3ds Max scene operation. | core | read | native |

## Objects


### Modeling

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `curve_model` | Construct editable curves, swept profiles or matched quad lofts with saved controls. | core | changes_scene | python |
| `edit_curve` | Atomic world-space base-spline edits guarded by inspect_curve.curve_token. | core | changes_scene | python |
| `inspect_curve` | Read an editable spline's world knots/handles, QA, and stale-edit token. | core | safe | native |

### Modifiers

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `add_modifier` | Add a modifier to an object. | core | changes_scene | native |
| `collapse_modifier_stack` | Collapse the modifier stack on an object. | core | changes_scene | native |
| `make_modifier_unique` | Make an instanced modifier unique (de-instance it). | core | changes_scene | native |
| `remove_modifier` | Remove a modifier from an object by name. | core | changes_scene | native |
| `set_modifier_property` | Set a modifier parameter on one object or many. | core | changes_scene | native |
| `set_modifier_state` | Set the enable state of a modifier with viewport/render granularity. | core | changes_scene | native |

### Objects

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `analyze_node_orientation` | Inspect world-space orientation, pivots, bounding boxes, and local axes for scene nodes. | core | read | native |
| `batch_rename_objects` | Rename multiple objects in a single batch operation. | core | changes_scene | native |
| `clone_objects` | Clone (copy/instance/reference) objects in the scene. | core | changes_scene | native |
| `create_object` | Create a geometry object with spatial placement feedback. | core | changes_scene | native |
| `delete_objects` | Delete objects from the 3ds Max scene by name. | core | changes_scene | native |
| `get_hierarchy` | Get the hierarchy tree of an object (recursive children). | core | safe | native |
| `get_object_properties` | Get compact properties of a named object (transform, class, material name). | core | safe | native |
| `isolate_and_capture_selected` | Capture isolated viewport screenshots of each selected object (resolves to top-level parents). | core | advanced | native |
| `select_objects` | Select objects in the 3ds Max scene. An explicit names=[] clears selection. | core | read | native |
| `set_object_property` | Set a property on a named object in the 3ds Max scene. | core | changes_scene | native |
| `set_parent` | Parent or unparent objects in the 3ds Max scene. | core | changes_scene | native |
| `set_visibility` | Show, hide, freeze, or unfreeze objects. | core | changes_scene | native |
| `transform_object` | Move, rotate, and/or scale an object by world/local offsets. | core | changes_scene | native |

### Organization

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `manage_groups` | Manage object groups — create, ungroup, open, close, attach, detach. | core | read | native |
| `manage_layers` | Manage scene layers — create, delete, list, set properties, move objects. | core | read | native |
| `manage_selection_sets` | Manage named selection sets — create, delete, list, select, replace. | core | read | native |

## Materials


### Material Network

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `inspect_material_network` | Inspect a material graph: wired slots, nested maps, file manifest, and health issues. | core | safe | native |
| `replicate_material` | Preview or apply a structure-preserving material clone/remap through native C++. | core | advanced | native |

### Materials

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `assign_material` | Create a material, or share an existing object's material with targets. | core | changes_scene | native |
| `backup_material_library` | Save material-library scratchpads to .mat files without changing the scene. | core | read | native |
| `batch_replace_materials` | Replace multiple materials in a single operation. | core | advanced | native |
| `create_material_from_textures` | Create a fully-wired PBR material from a folder of texture maps. | core | advanced | maxscript |
| `create_shell_material` | Wrap render + export materials in a Shell Material (dual pipeline). | core | advanced | native |
| `create_texture_map` | Create a texture map and store it as a MAXScript global variable. | core | changes_scene | native |
| `get_material_library` | Inspect the active material library scratchpad and Material Editor slots. | core | safe | native |
| `get_material_slots` | Get compact material slot/property info without schema caches. | core | safe | native |
| `get_materials` | List all materials assigned to objects in the current 3ds Max scene. | core | safe | native |
| `palette_laydown` | Lay down folder textures into Compact Material Editor palette slots. | core | advanced | python |
| `replace_material` | Replace one material with another across all objects that use it. | core | advanced | native |
| `set_material_properties` | Set multiple properties on an object's material in a single call. | core | changes_scene | native |
| `set_material_property` | Set a property on an object's material (or sub-material). | core | changes_scene | native |
| `set_sub_material` | Create or assign a sub-material in a Multi/Sub-Object material slot. | core | changes_scene | native |
| `set_texture_map_properties` | Set properties on a texture map stored as a MAXScript global variable. | core | changes_scene | native |
| `write_osl_shader` | Write an OSL shader to disk and create an OSLMap from it. | core | changes_scene | native |

### Smart Import

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `smart_import` | Batch-import 3D meshes from a folder, auto-assigning materials by stem matching. | core | changes_scene | maxscript |

## Inspect


### Analysis

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `learn_scene_patterns` | Analyze the current scene to learn real-world class usage patterns. | core | advanced | native |
| `map_class_relationships` | Map which classes can reference which types via their ParamBlock2 params. | core | advanced | native |
| `walk_references` | Walk the full reference dependency graph of a scene object. | core | read | native |
| `watch_scene` | Live scene event watcher — track what happens in 3ds Max in real-time. | core | advanced | native |

### Inspect

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `inspect_object` | Get a deep exploratory object summary (props, modifiers, material, instances). | core | safe | native |
| `inspect_properties` | Deep-inspect all properties of an object, modifier, base object, or material. | core | safe | native |
| `introspect_osl` | Inspect the API surface of any material, texturemap, or modifier class. | core | safe | maxscript |

### Plugins

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `discover_plugin_classes` | Enumerate ALL registered classes in 3ds Max's DLL directory via native C++ SDK. | core | advanced | native |
| `discover_plugin_surface` | Discover plugin-related classes and summarize likely entry points. | core | safe | python |
| `get_plugin_manifest` | Return a structured plugin manifest derived from live runtime data plus curated hints. | core | safe | python |
| `inspect_plugin_class` | Inspect a plugin class using runtime class scans plus showClass reflection. | core | safe | python |
| `inspect_plugin_constructor` | Return likely creation notes for a plugin class. | core | safe | python |
| `inspect_plugin_instance` | Inspect a live scene instance with plugin-aware summarization. | core | safe | python |
| `introspect_class` | Deep C++ SDK introspection of a class — returns the COMPLETE API surface. | core | safe | native |
| `introspect_instance` | Deep C++ SDK introspection of a live scene object with actual values. | core | safe | native |
| `list_plugin_classes` | List classes likely tied to a plugin or superclass family. | core | safe | native |
| `refresh_plugin_manifest` | Refresh and return the plugin manifest. | core | read | python |

## Animation


### Controllers

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `add_controller_target` | Add a node variable or constraint target to an existing controller. | core | advanced | maxscript |
| `assign_controller` | Create and assign a controller to a sub-anim track. | core | advanced | native |
| `get_wired_params` | Show existing wire connections on an object. | full | safe | native |
| `inspect_controller` | Inspect the controller on a specific sub-anim track. | core | safe | native |
| `inspect_track_view` | Inspect an object's controller/track tree in a Track View-style hierarchy. | core | safe | native |
| `list_wireable_params` | Discover sub-anim parameters on an object that can be wired. | full | safe | native |
| `set_controller_props` | Modify script text or properties on an existing controller. | core | advanced | native |
| `unwire_params` | Disconnect a wired parameter. | full | advanced | native |
| `wire_params` | Connect parameters between objects with a wire expression. | full | advanced | native |

## Viewport & Render


### Render

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `render_scene` | Render the current viewport in 3ds Max. | full | advanced | native |

### Viewport

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `agent_viewport` | Own a shaded floating AGENT VIEWPORT without moving the user's view. | core | read | native |
| `capture_multi_view` | Capture multiple viewport angles to a stitched file and return compact metadata. | core | advanced | native |
| `capture_screen` | Capture visible desktop pixels, optionally cropped to the V-Ray frame buffer. | core | advanced | native |
| `capture_viewport` | Capture AGENT VIEWPORT when open, otherwise the active view, to a saved file. | core | advanced | native |
| `set_viewport` | Set the agent modeling view when open, otherwise the active viewport. | core | read | native |

## Files


### Files

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `batch_file_info` | Read metadata from multiple .max files in a single call. | core | advanced | native |
| `inspect_max_file` | Inspect an external .max file without opening it. | core | advanced | native |
| `merge_from_file` | Merge objects from an external .max file into the current scene. | core | advanced | native |
| `search_max_files` | Search .max files in a folder for objects matching a name pattern. | core | advanced | python |

## Specialty


### Data Channel

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `add_data_channel` | Append operators to a Data Channel modifier's internal stack. | full | advanced | maxscript |
| `add_dc_script_operator` | Add the legacy MAXScript input operator with explicit executable authorization. | full | advanced | python |
| `inspect_data_channel` | Inspect the active Data Channel stack in processing order. | full | safe | maxscript |
| `list_dc_operators` | Discover the live Data Channel operator catalog. | full | safe | maxscript |
| `list_dc_presets` | List available Data Channel presets without creating a scene object. | full | safe | maxscript |
| `load_dc_preset` | Load a Data Channel preset into the object's DC modifier internal stack. | full | advanced | maxscript |
| `manage_data_channel_stack` | Safely edit a Data Channel stack. | full | read | maxscript |
| `set_data_channel_operator` | Set properties on a 1-based visible stack operator with rollback on error. | full | advanced | maxscript |

### Effects

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `delete_effect` | Delete an atmospheric or render effect by index. | full | advanced | native |
| `get_effects` | List all atmospheric effects and render effects in the scene. | full | safe | native |
| `toggle_effect` | Enable or disable an atmospheric or render effect by index. | full | advanced | native |

### Max Creation Graph

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `mcg_apply_modifier` | Compile and safely apply a temp MCG modifier using typed node references. | full | changes_scene | native |
| `mcg_apply_patch` | Patch a temp graph transactionally, then compile/test and roll back on failure. | full | advanced | python |
| `mcg_cleanup_workspace` | Delete one temp graph family or the entire process-scoped MCG workspace. | full | advanced | python |
| `mcg_compile_graph` | Validate, compile, and optionally test one temp MCG graph. | full | advanced | python |
| `mcg_create_graph` | Fork an Autodesk/source template into temp storage and optionally compile/test it. | full | advanced | python |
| `mcg_get_context` | Return the live MCG compiler, temp workspace, templates, and safety context. | full | read | python |
| `mcg_inspect_graph` | Inspect a session graph or read-only source as normalized graph data. | full | read | python |
| `mcg_inspect_instance` | Inspect one MCG modifier after proving its class ID and graph identity. | full | read | native |
| `mcg_list_graphs` | List session graphs or read-only installed/sample graph sources. | full | read | python |
| `mcg_reload_operators` | Explicitly refresh the global MCG depot; not used by the normal per-graph loop. | full | advanced | maxscript |
| `mcg_resolve_class` | Compile a temp modifier graph and resolve its exact native class descriptor. | full | advanced | native |
| `mcg_restore_checkpoint` | Transactionally restore an opaque checkpoint, then optionally compile/test it. | full | advanced | python |
| `mcg_search_operators` | Search typed inputs plus value(0)/function(1) outputs; fall back to XML offline. | full | read | python |
| `mcg_set_node_parameter` | Safely retarget one scalar node parameter on a compiled MCG modifier. | full | changes_scene | native |
| `mcg_test_tool` | Compile the current hash, then create/inspect/delete one disposable instance. | full | advanced | python |

### RailClone

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `get_railclone_style_graph` | Read RailClone style-editor graph data from exposed arrays/interfaces. | full | advanced | maxscript |

### Scattering

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `scatter_forest_pack` | Create a Forest Pack scatter object and wire surfaces + source geometry. | full | advanced | maxscript |

### State Sets

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `get_camera_sequence` | Get only the camera-assigned State Sets, sorted by start frame. | full | safe | native |
| `get_state_sets` | Get all State Sets with their camera assignments and frame ranges. | full | safe | native |

### tyFlow

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `add_tyflow_collision` | Add/configure Collision operator and wire collider node list. | full | advanced | python |
| `add_tyflow_event` | Add one event to an existing tyFlow object. | full | advanced | python |
| `connect_tyflow_events` | Connect events via Send Out using tyFlow's documented connect API. | full | advanced | python |
| `create_tyflow` | Create tyFlow with one event and a configurable operator list. | full | advanced | python |
| `create_tyflow_preset` | Create common tyFlow presets: rain, snow, fountain, burst, debris. | full | advanced | python |
| `get_tyflow_info` | Inspect a tyFlow object with deep flow/event/operator/property readback. | full | advanced | maxscript |
| `get_tyflow_particle_count` | Return tyFlow particle count at current frame or supplied frame. | full | advanced | python |
| `get_tyflow_particles` | Return particle data rows from tyFlow read-only APIs. | full | advanced | python |
| `list_tyflow_operator_types` | Return available and unavailable tyFlow operator names for this installation. | full | advanced | python |
| `modify_tyflow_operator` | Set operator properties on an existing tyFlow event/operator pair. | full | advanced | python |
| `remove_tyflow_element` | Remove operator from an event, or remove event when operator_name is empty. | full | advanced | python |
| `reset_tyflow_simulation` | Reset simulation for one tyFlow object or for all tyFlow objects. | full | advanced | python |
| `set_tyflow_physx` | Set object-level PhysX settings from tyFlow object properties. | full | advanced | python |
| `set_tyflow_shape` | Set Shape operator with validated 3D shape IDs. | full | advanced | python |

## Advanced


### Advanced

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `execute_maxscript` | Execute arbitrary MAXScript in 3ds Max and return the result. | core | advanced | maxscript |
| `search_maxscript_docs` | Search the local MAXScript / 3ds Max reference index for API names, signatures, and patterns. | core | read | python |

### Tool Test

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `invoke_tool` | Invoke any registered MCP tool inside 3ds Max via the native bridge. | core | advanced | native |
| `run_tool_smoke` | Run generated live smoke cases against the native bridge inside 3ds Max. | core | advanced | native |

## Other


### Booleans

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `boolean_operation` | Boolean modeling on a base object via the Boolean modifier (BooleanMod). | core | read | python |

### Component Pick

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `pick_component` | Target Editable Poly base-cage IDs from an AGENT VIEWPORT capture. | core | read | python |

### Entities

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `apply_entity` | Put objects into an entity path, creating missing branches. One undo step in Max. | full | changes_scene | python |
| `entity_automation` | Start, stop or inspect the session's background entity ranker using local Ollama. | full | changes_scene | python |
| `entity_bounds` | World bounding box of every entity's branch (its objects plus descendants). | full | read | python |
| `entity_evidence` | Features and containment candidates for objects, the plugin half of an entity proposal. | full | read | python |
| `entity_status` | Report whether TagManager is loaded and how its facade is configured. | full | read | python |
| `get_object_entities` | Entity paths that own each given object (by scene name and/or node handle). | full | safe | python |
| `list_entities` | List every TagManager entity below Project: path, depth, member and child counts. | full | safe | python |
| `pending_proposals` | Proposals waiting for confirmation in TagManager. | full | changes_scene | python |
| `present_proposals` | Hand a ranked candidate list per object to TagManager. | full | changes_scene | python |
| `remove_from_entity` | Take objects out of one entity path. One undo step in Max. | full | changes_scene | python |
| `request_entity_proposals` | Gather fresh evidence and request reviewable suggestions; returns session and tokens. | full | changes_scene | python |
| `review_entity_proposals` | Open FastTag with inline suggestions for the current selection, before typing. | full | changes_scene | python |
| `set_entity_zone` | Use explicit volume nodes for an entity's containment bounds in this session. | full | changes_scene | python |

### Geometry Qa

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `geometry_qa` | Check evaluated mesh topology without changing the scene or collapsing its stack. | core | read | maxscript |

### Keyframes

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `keyframe_tracks` | Deterministic native animation edits. Actions: timeline; list/set; delete_keys/move_keys/scale_keys; resample or bake; normalize_tangents/style; match/loop; ort. Key-time edits use time/times or from_time/to_time. bake replaces keys in its sample window by default; resample preserves them unless rep | core | read | native |

### Loft

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `loft_mesh` | Create/read/update a parameterized quad loft stored on its mesh node in the .max file. | core | read | python |

### Mainthread

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `main_thread` | Inspect or clean up what runs on the Max main/UI thread. | core | read | native |

### Mesh Ops

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `create_mesh` | Create an Editable Poly from explicit WORLD vertices and ordered polygon faces. | core | read | python |
| `inspect_mesh` | Inspect an Editable Poly BASE cage with actionable component IDs and optional labeled capture. | core | safe | native |
| `mesh_edit` | Edit vertices, edges, and faces as one undoable batch, rolling back on failure. | core | read | python |

### Poly Edit

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `edit_vertices` | Read and manipulate Editable_Poly vertices in world space. | core | read | python |

### Render Automations

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `render_automations` | Arm a done-signal for the NEXT render, then report when it finishes. | full | read | native |

### Scene Patch

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `resolve_node_refs` | Resolve NodeRefs to canonical identities plus mutation sceneSeq. | core | read | native |
| `scene_patch` | Preflight and atomically apply mechanical node edits in one native undo step. | core | read | native |

### Scene Qa

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `scene_qa` | Scan or repair non-mesh scene hygiene using the native SDK. | core | read | maxscript |

### Splines

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `draw_spline` | Draw and edit spline shapes from explicit points (world-space). | core | read | python |

### Tyflow Census

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `capture_tyflow_editor` | Open the tyFlow editor and capture the screen for visual wire inspection. | full | read | maxscript |
| `tyflow_event_census` | Per-event particle counts at probe frames via temporary instrumentation. | full | read | maxscript |

### Tyflow Graph

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `connect_tyflow_operator` | Connect a test/Send Out operator's output to a target event (documented API). | full | read | python |
| `disconnect_tyflow_operator` | Disconnect an operator's output and drop its ledger edge. | full | read | python |
| `get_tyflow_graph` | Full tyFlow graph view: events, operators, properties, ledger edges, staleness. | full | safe | python |
| `set_tyflow_wiring_ledger` | Reconcile the wiring ledger by hand (e.g. after reading an editor capture). | full | read | python |

### Tyflow Manifest

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `harvest_tyflow_manifest` | Probe-harvest the tyFlow operator manifest and cache it per tyFlow version. | full | read | python |
| `list_tyflow_operators` | Query the cached tyFlow operator manifest (no Max traffic). | full | safe | python |

### Tyflow Patch

| Tool | Description | Profile | Risk | Routing |
|---|---|---|---|---|
| `tyflow_apply_patch` | Apply a batch of tyFlow graph operations as one transaction. | full | read | python |
