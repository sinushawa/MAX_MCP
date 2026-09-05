-- mcp_settings.ms — simple settings window for 3dsmax-mcp.
--
-- Customize UI -> MCP -> "MCP Settings" (or search the macro globally).
-- Edits %LOCALAPPDATA%\3dsmax-mcp\mcp_config.ini, section [mcp]:
--   tool_profile      full | core | progressive
--   safe_mode         true | false
--   disabled_modules  comma-separated maxmcp/tools module names
-- The Python MCP server reads these keys when it starts, so changes apply the
-- next time your MCP client (Claude Code, Cursor, ...) launches the server.

global MCPSettingsRollout

-- Module tables. Keep in sync with CORE_TOOL_MODULES / SPECIALTY_TOOL_MODULES in
-- maxmcp/server.py (tests/test_module_filter.py checks that every module is listed).
global mcpSettings_specialtyModules = #(
	#("render", "Render"),
	#("render_automations", "Render automations"),
	#("state_sets", "State sets"),
	#("effects", "Effects"),
	#("wire_params", "Parameter wiring"),
	#("data_channel", "Data Channel"),
	#("mcg", "Max Creation Graph"),
	#("railclone", "RailClone (WIP)"),
	#("scattering", "Scattering / Forest Pack (WIP)"),
	#("tyflow", "tyFlow"),
	#("tyflow_graph", "tyFlow graph"),
	#("tyflow_patch", "tyFlow patch"),
	#("tyflow_manifest", "tyFlow manifest"),
	#("tyflow_census", "tyFlow census")
)

global mcpSettings_coreModules = #(
	#("bridge", "Bridge status"),
	#("capabilities", "Plugin capabilities"),
	#("session_context", "Session context"),
	#("mainthread", "Main thread"),
	#("execute", "Execute MAXScript"),
	#("docs_search", "MAXScript docs search"),
	#("tool_test", "Tool self-test"),
	#("query_scene", "Query scene"),
	#("scene_query", "Scene query"),
	#("scene_manage", "Scene manage"),
	#("scene_patch", "Scene patch"),
	#("scene_qa", "Scene QA"),
	#("objects", "Objects"),
	#("identify", "Identify"),
	#("transform", "Transform"),
	#("orientation", "Orientation"),
	#("hierarchy", "Hierarchy"),
	#("selection", "Selection"),
	#("visibility", "Visibility"),
	#("clone", "Clone"),
	#("organize", "Layers / groups / sets"),
	#("modifiers", "Modifiers"),
	#("booleans", "Booleans"),
	#("splines", "Splines"),
	#("poly_edit", "Poly edit"),
	#("mesh_ops", "Mesh ops"),
	#("geometry_qa", "Geometry QA"),
	#("component_pick", "Component pick"),
	#("loft", "Loft"),
	#("curve_model", "Curve model"),
	#("curve_edit", "Curve edit"),
	#("materials", "Materials"),
	#("material_ops", "Material ops"),
	#("material_network", "Material network"),
	#("material_replace", "Material replace"),
	#("palette_laydown", "Palette laydown"),
	#("smart_import", "Smart import"),
	#("inspect", "Inspect"),
	#("plugins", "Plugins / introspection"),
	#("learning", "Scene learning"),
	#("controllers", "Controllers"),
	#("keyframes", "Keyframes"),
	#("viewport", "Viewport capture"),
	#("file_access", "External .max files")
)

fn mcpSettings_configPath = (
	local base = systemTools.getEnvVariable "LOCALAPPDATA"
	if base == undefined or base == "" do base = getDir #userScripts
	base + "\\3dsmax-mcp\\mcp_config.ini"
)

fn mcpSettings_trim s = (
	if s == undefined do return ""
	trimLeft (trimRight (s as string))
)

fn mcpSettings_readList key = (
	local raw = getINISetting (mcpSettings_configPath()) "mcp" key
	local out = #()
	for tok in (filterString raw ",; \t") do (
		local t = toLower (mcpSettings_trim tok)
		if t != "" and (findItem out t) == 0 do append out t
	)
	out
)

fn mcpSettings_joinList arr = (
	local s = ""
	for i = 1 to arr.count do s += (if i > 1 then ", " else "") + arr[i]
	s
)

fn mcpSettings_write key val = (
	local path = mcpSettings_configPath()
	makeDir (getFilenamePath path) all:true
	setINISetting path "mcp" key val
)

fn mcpSettings_checkboxes = (
	local out = #()
	for c in MCPSettingsRollout.controls where (matchPattern (c.name as string) pattern:"cb_*") do append out c
	out
)

fn mcpSettings_moduleOf cb = (
	local n = cb.name as string
	substring n 4 (n.count - 3)
)

fn mcpSettings_load = (
	local path = mcpSettings_configPath()
	MCPSettingsRollout.pathLabel.text = path
	local profile = toLower (mcpSettings_trim (getINISetting path "mcp" "tool_profile"))
	local idx = findItem MCPSettingsRollout.profileDD.items profile
	MCPSettingsRollout.profileDD.selection = (if idx == 0 then 1 else idx)
	MCPSettingsRollout.safeCB.checked = ((toLower (mcpSettings_trim (getINISetting path "mcp" "safe_mode"))) != "false")
	local disabled = mcpSettings_readList "disabled_modules"
	for cb in (mcpSettings_checkboxes()) do cb.checked = ((findItem disabled (mcpSettings_moduleOf cb)) == 0)
	local enabledOnly = mcpSettings_readList "enabled_modules"
	MCPSettingsRollout.noteLabel.text = if enabledOnly.count > 0 then
		("Note: enabled_modules allowlist is also set in the ini (" + (mcpSettings_joinList enabledOnly) + ").")
	else
		"Unchecked modules are written to disabled_modules. Reconnect your MCP client to apply."
	MCPSettingsRollout.statusLabel.text = (if doesFileExist path then "Loaded." else "Config file not found yet; Save will create it.")
)

fn mcpSettings_save = (
	local disabled = #()
	for cb in (mcpSettings_checkboxes()) where (not cb.checked) do append disabled (mcpSettings_moduleOf cb)
	mcpSettings_write "tool_profile" MCPSettingsRollout.profileDD.selected
	mcpSettings_write "safe_mode" (if MCPSettingsRollout.safeCB.checked then "true" else "false")
	mcpSettings_write "disabled_modules" (mcpSettings_joinList disabled)
	MCPSettingsRollout.statusLabel.text = ("Saved " + (disabled.count as string) + " disabled module(s). Reconnect your MCP client to apply.")
	format "3dsmax-mcp settings saved: profile=% safe_mode=% disabled_modules=%\n" MCPSettingsRollout.profileDD.selected MCPSettingsRollout.safeCB.checked (mcpSettings_joinList disabled)
)

fn mcpSettings_setAll state = (
	for cb in (mcpSettings_checkboxes()) do cb.checked = state
)

-- Rollout controls must be declared statically, so the definition is generated
-- as text from the module tables and evaluated.
fn mcpSettings_addGroup lines grpName title mods y cols colWidth = (
	local rows = (ceil (mods.count as float / cols)) as integer
	local height = rows * 20 + 28
	append lines ("  groupBox " + grpName + " \"" + title + "\" pos:[8," + (y as string) + "] width:" + ((cols * colWidth + 16) as string) + " height:" + (height as string))
	for i = 1 to mods.count do (
		local col = (mod (i - 1) cols) as integer
		local row = ((i - 1) / cols) as integer
		local x = 18 + col * colWidth
		local cy = y + 20 + row * 20
		append lines ("  checkbox cb_" + mods[i][1] + " \"" + mods[i][2] + "\" pos:[" + (x as string) + "," + (cy as string) + "] width:" + ((colWidth - 8) as string) + " checked:true")
	)
	y + height + 8
)

fn mcpSettings_buildRollout = (
	local cols = 3
	local colWidth = 196
	local width = cols * colWidth + 32
	local lines = #()
	append lines "rollout MCPSettingsRollout \"MCP Settings\" ("
	append lines ("  label pathLabel \"\" pos:[12,8] width:" + ((width - 24) as string) + " height:16")
	append lines "  dropdownlist profileDD \"Tool profile\" items:#(\"full\", \"core\", \"progressive\") pos:[12,28] width:160"
	append lines "  checkbox safeCB \"Safe mode (block dangerous MAXScript)\" pos:[190,46] width:300 checked:true"
	local y = 76
	y = mcpSettings_addGroup lines "grpSpecialty" "Specialty modules (full profile only)" mcpSettings_specialtyModules y cols colWidth
	y = mcpSettings_addGroup lines "grpCore" "Core modules (all profiles)" mcpSettings_coreModules y cols colWidth
	append lines ("  label noteLabel \"\" pos:[12," + (y as string) + "] width:" + ((width - 24) as string) + " height:16")
	y += 22
	append lines ("  button saveBtn \"Save\" pos:[12," + (y as string) + "] width:110 height:26")
	append lines ("  button allBtn \"Enable all\" pos:[130," + (y as string) + "] width:110 height:26")
	append lines ("  button noneBtn \"Disable all\" pos:[248," + (y as string) + "] width:110 height:26")
	append lines ("  button reloadBtn \"Reload\" pos:[366," + (y as string) + "] width:110 height:26")
	append lines ("  button closeBtn \"Close\" pos:[" + ((width - 122) as string) + "," + (y as string) + "] width:110 height:26")
	y += 32
	append lines ("  label statusLabel \"\" pos:[12," + (y as string) + "] width:" + ((width - 24) as string) + " height:16")
	y += 24
	append lines "  on MCPSettingsRollout open do mcpSettings_load()"
	append lines "  on saveBtn pressed do mcpSettings_save()"
	append lines "  on allBtn pressed do mcpSettings_setAll true"
	append lines "  on noneBtn pressed do mcpSettings_setAll false"
	append lines "  on reloadBtn pressed do mcpSettings_load()"
	append lines "  on closeBtn pressed do destroyDialog MCPSettingsRollout"
	append lines ")"
	local code = ""
	for l in lines do code += l + "\n"
	execute code
	#(width, y)
)

fn mcpSettings_open = (
	try (destroyDialog MCPSettingsRollout) catch ()
	local size = mcpSettings_buildRollout()
	createDialog MCPSettingsRollout size[1] size[2] style:#(#style_titlebar, #style_sysmenu, #style_toolwindow)
)

macroScript MCP_Settings category:"MCP" tooltip:"Choose which 3dsmax-mcp tool modules are exposed" buttonText:"MCP Settings"
(
	on execute do mcpSettings_open()
)
