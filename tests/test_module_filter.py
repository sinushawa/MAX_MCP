"""Settings-driven tool module filter (disabled_modules / enabled_modules)."""

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from maxmcp.tool_discovery import TOOLSET_SPECS, ToolsetSpec, restrict_toolsets

ROOT = Path(__file__).resolve().parent.parent
FILTER_ENV_KEYS = {
    "MCP_TOOL_PROFILE",
    "THREEDSMAX_MCP_TOOL_PROFILE",
    "MCP_DISABLED_MODULES",
    "MCP_ENABLED_MODULES",
}


def _server():
    import maxmcp.server as server

    return server


def _envelope(result) -> dict:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and "ok" in structured:
        return structured
    for block in getattr(result, "content", []):
        text = getattr(block, "text", None)
        if not isinstance(text, str):
            continue
        try:
            parsed = json.loads(text)
        except (TypeError, ValueError):
            continue
        if isinstance(parsed, dict) and "ok" in parsed:
            return parsed
    raise AssertionError(f"No ToolEnvelope in result: {result!r}")


class ModuleFilterUnitTests(unittest.TestCase):
    def test_parse_module_list_accepts_mixed_separators_and_dedupes(self) -> None:
        server = _server()
        parsed = server.parse_module_list(" chat, tyflow;railclone  MCG\nmcg ,")
        self.assertEqual(parsed, ("chat", "tyflow", "railclone", "mcg"))
        self.assertEqual(server.parse_module_list(None), ())
        self.assertEqual(server.parse_module_list(""), ())

    def test_filter_disabled_removes_modules_and_keeps_order(self) -> None:
        server = _server()
        result = server.filter_tool_modules(
            ("bridge", "chat", "render", "tyflow"), disabled=("chat", "tyflow")
        )
        self.assertEqual(result, ("bridge", "render"))

    def test_filter_enabled_is_an_allowlist_and_disabled_still_applies(self) -> None:
        server = _server()
        result = server.filter_tool_modules(
            ("bridge", "chat", "render", "tyflow"),
            enabled=("bridge", "render", "chat"),
            disabled=("chat",),
        )
        self.assertEqual(result, ("bridge", "render"))

    def test_filter_warns_about_unknown_names_and_ignores_them(self) -> None:
        server = _server()
        with self.assertLogs(level="WARNING") as captured:
            result = server.filter_tool_modules(("bridge", "render"), disabled=("no_such_module",))
        self.assertEqual(result, ("bridge", "render"))
        self.assertTrue(any("no_such_module" in line for line in captured.output))

    def test_restrict_toolsets_drops_modules_and_empty_toolsets(self) -> None:
        specs = (
            ToolsetSpec("a", "A", ("x", "y")),
            ToolsetSpec("b", "B", ("z",)),
        )
        self.assertEqual(restrict_toolsets(specs, ("x",)), (ToolsetSpec("a", "A", ("x",)),))

    def test_restrict_toolsets_is_identity_for_the_full_module_set(self) -> None:
        server = _server()
        self.assertEqual(restrict_toolsets(TOOLSET_SPECS, server.ALL_TOOL_MODULES), TOOLSET_SPECS)

    def test_active_modules_prefer_env_over_ini_and_empty_env_clears(self) -> None:
        server = _server()
        saved = {key: os.environ.get(key) for key in ("LOCALAPPDATA", *FILTER_ENV_KEYS)}
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "3dsmax-mcp"
            config_dir.mkdir()
            (config_dir / "mcp_config.ini").write_text(
                "[mcp]\ntool_profile = full\ndisabled_modules = effects, tyflow\n",
                encoding="utf-8",
            )
            try:
                os.environ["LOCALAPPDATA"] = temp_dir
                for key in FILTER_ENV_KEYS:
                    os.environ.pop(key, None)

                active = server.active_tool_modules("full")
                self.assertNotIn("effects", active)
                self.assertNotIn("tyflow", active)
                self.assertIn("render", active)

                os.environ["MCP_DISABLED_MODULES"] = "render"
                active = server.active_tool_modules("full")
                self.assertIn("effects", active)
                self.assertNotIn("render", active)

                os.environ["MCP_DISABLED_MODULES"] = ""
                self.assertEqual(server.active_tool_modules("full"), server.ALL_TOOL_MODULES)
            finally:
                for key, value in saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_settings_window_lists_every_tool_module(self) -> None:
        """maxscript/mcp_settings.ms hardcodes the module table; keep it in sync."""
        server = _server()
        source = (ROOT / "maxscript" / "mcp_settings.ms").read_text(encoding="utf-8")
        listed = set(re.findall(r'#\("([a-z_]+)",\s*"', source))
        self.assertEqual(listed, set(server.ALL_TOOL_MODULES))


class ModuleFilterLaunchTests(unittest.IsolatedAsyncioTestCase):
    async def _list_tool_names(
        self, ini_text: str | None, extra_env: dict[str, str] | None = None
    ) -> list[str]:
        env = {key: value for key, value in os.environ.items() if key not in FILTER_ENV_KEYS}
        with tempfile.TemporaryDirectory() as temp_dir:
            if ini_text is not None:
                config_dir = Path(temp_dir) / "3dsmax-mcp"
                config_dir.mkdir()
                (config_dir / "mcp_config.ini").write_text(ini_text, encoding="utf-8")
            env["LOCALAPPDATA"] = temp_dir
            if extra_env:
                env.update(extra_env)
            params = StdioServerParameters(
                command=sys.executable, args=["-m", "maxmcp.server"], env=env
            )
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return [tool.name for tool in (await session.list_tools()).tools]

    async def test_full_profile_with_disabled_modules_hides_their_tools(self) -> None:
        names = await self._list_tool_names(
            "[mcp]\ntool_profile = full\ndisabled_modules = effects, tyflow, tyflow_graph, mcg\n"
        )
        self.assertNotIn("get_effects", names)
        self.assertNotIn("toggle_effect", names)
        self.assertNotIn("get_tyflow_graph", names)
        self.assertNotIn("mcg_create_graph", names)
        self.assertIn("render_scene", names)
        self.assertIn("query_scene", names)

    async def test_env_disabled_modules_overrides_ini(self) -> None:
        names = await self._list_tool_names(
            "[mcp]\ntool_profile = full\ndisabled_modules = render\n",
            extra_env={"MCP_DISABLED_MODULES": "effects"},
        )
        self.assertIn("render_scene", names)
        self.assertNotIn("get_effects", names)

    async def test_progressive_profile_respects_disabled_modules(self) -> None:
        env = {key: value for key, value in os.environ.items() if key not in FILTER_ENV_KEYS}
        env["MCP_TOOL_PROFILE"] = "progressive"
        env["MCP_DISABLED_MODULES"] = (
            "effects, tyflow, tyflow_graph, tyflow_patch, tyflow_manifest, tyflow_census, mcg"
        )
        params = StdioServerParameters(command=sys.executable, args=["-m", "maxmcp.server"], env=env)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                names = [tool.name for tool in (await session.list_tools()).tools]
                self.assertEqual(names, ["list_toolsets", "describe_toolset", "call_tool"])

                listed = _envelope(await session.call_tool("list_toolsets", {}))
                self.assertTrue(listed["ok"])
                toolsets = {item["name"] for item in listed["result"]["toolsets"]}
                self.assertNotIn("tyflow", toolsets)
                self.assertNotIn("max_creation_graph", toolsets)
                self.assertIn("scene", toolsets)
                self.assertLess(listed["result"]["tool_count"], 150)


if __name__ == "__main__":
    unittest.main()
