"""TagManager entity tools: script composition, response handling, registration."""

import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from maxmcp.tools import entities

ROOT = Path(__file__).resolve().parent.parent
FACADE = '(dotNetClass "TagManager.TagApi")'


def _send(result):
    return patch.object(entities.client, "send_command", return_value={"result": result})


class ScriptCompositionTests(unittest.TestCase):
    def test_list_entities_calls_the_facade_without_arguments(self) -> None:
        with _send('{"ok":true,"entities":[]}') as mocked:
            out = entities.list_entities()
        self.assertEqual(json.loads(out), {"ok": True, "entities": []})
        script, kwargs = mocked.call_args.args[0], mocked.call_args.kwargs
        self.assertEqual(script, f"({FACADE}.ListEntities())")
        self.assertEqual(kwargs["cmd_type"], "maxscript")

    def test_remove_puts_the_path_before_the_handles(self) -> None:
        with _send('{"ok":true}') as mocked:
            entities.remove_from_entity("A_B", handles=[5])
        self.assertEqual(mocked.call_args.args[0], f'({FACADE}.Remove "A_B" "5")')

    def test_handles_only_apply_is_a_direct_call_with_rendered_booleans(self) -> None:
        with _send('{"ok":true}') as mocked:
            entities.apply_entity("Building_Floor1", handles=[12, 13, 12, 0], layer=False, rename=True)
        script = mocked.call_args.args[0]
        self.assertEqual(script, f'({FACADE}.Apply "Building_Floor1" "12,13" false true)')

    def test_path_and_names_are_escaped_for_maxscript_strings(self) -> None:
        with _send('{"missingNames":[],"api":{"ok":true}}') as mocked:
            entities.apply_entity('Odd"Path\\x', names=['Chair "A"'])
        script = mocked.call_args.args[0]
        self.assertIn('#("Chair \\"A\\"")', script)
        self.assertIn('.Apply "Odd\\"Path\\\\x" __csv true true', script)
        self.assertIn("getNodeByName __n", script)

    def test_names_and_handles_combine_into_one_csv(self) -> None:
        with _send('{"missingNames":[],"api":{"ok":true}}') as mocked:
            entities.entity_evidence(names=["Box001"], handles=[7])
        script = mocked.call_args.args[0]
        self.assertIn('local __csv = "7"', script)
        self.assertIn(f"{FACADE}.Evidence __csv", script)

    def test_present_proposals_serializes_payload_into_a_string_argument(self) -> None:
        proposals = [{"handle": 1943, "token": "ticket", "ranked": [{"path": "A_B", "confidence": 0.93, "reason": "inside"}]}]
        with _send('{"ok":true,"applied":[1943],"queued":0,"pending":0}') as mocked:
            out = entities.present_proposals(proposals, session="scene", threshold=0.8)
        script = mocked.call_args.args[0]
        self.assertTrue(script.startswith(f"({FACADE}.Present \""))
        inner = re.search(r'\.Present "(.*)"\)$', script, re.S).group(1)
        payload = json.loads(inner.replace('\\"', '"').replace("\\\\", "\\"))
        self.assertEqual(payload["threshold"], 0.8)
        self.assertEqual(payload["proposals"][0]["ranked"][0]["path"], "A_B")
        self.assertEqual(json.loads(out)["applied"], [1943])

    def test_pending_actions_map_to_facade_calls(self) -> None:
        with _send('{"ok":true,"pending":[]}') as mocked:
            entities.pending_proposals()
        self.assertEqual(mocked.call_args.args[0], f"({FACADE}.Pending())")
        with _send('{"ok":true}') as mocked:
            entities.pending_proposals(action="accept", handle=8, index=1)
        self.assertEqual(mocked.call_args.args[0], f"({FACADE}.AcceptPending 8 1)")
        with _send('{"ok":true,"pending":0}') as mocked:
            entities.pending_proposals(action="clear", handles=[8, 9])
        self.assertEqual(mocked.call_args.args[0], f'({FACADE}.ClearPending "8,9")')

    def test_targets_and_paths_are_validated_before_any_bridge_call(self) -> None:
        with _send('{"ok":true}') as mocked:
            no_targets = json.loads(entities.apply_entity("A_B"))
            no_path = json.loads(entities.apply_entity("", handles=[1]))
            bad_action = json.loads(entities.pending_proposals(action="nope"))
            no_proposals = json.loads(entities.present_proposals([]))
        mocked.assert_not_called()
        for payload in (no_targets, no_path, bad_action, no_proposals):
            self.assertEqual(payload["status"], "error")


class ResponseHandlingTests(unittest.TestCase):
    def test_missing_names_are_merged_into_the_facade_result(self) -> None:
        wrapped = '{"missingNames":["Ghost"],"api":{"ok":true,"objects":{"7":["A_B"]}}}'
        with _send(wrapped):
            out = json.loads(entities.get_object_entities(names=["Ghost", "Box001"]))
        self.assertEqual(out["missingNames"], ["Ghost"])
        self.assertEqual(out["objects"]["7"], ["A_B"])

    def test_not_initialized_gets_a_load_hint(self) -> None:
        with _send('{"ok":false,"error":"InvalidOperationException: TagManager is not initialized in this session"}'):
            out = json.loads(entities.list_entities())
        self.assertFalse(out["ok"])
        self.assertIn("bin\\assemblies", out["hint"])

    def test_maxscript_error_sentinel_becomes_structured_error(self) -> None:
        sentinel = entities._MAXSCRIPT_ERROR_SENTINEL + '-- Runtime error: dotNetClass "TagManager.TagApi" not found'
        with _send(sentinel):
            out = json.loads(entities.entity_status())
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["error_type"], "MAXScriptError")
        self.assertIn("hint", out)

    def test_non_json_result_is_reported_not_raised(self) -> None:
        with _send("OK"):
            out = json.loads(entities.entity_bounds())
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["raw"], "OK")


class RegistrationTests(unittest.TestCase):
    def test_entities_is_a_specialty_module_everywhere(self) -> None:
        import maxmcp.server as server
        from maxmcp.tool_discovery import TOOLSET_SPECS

        self.assertIn("entities", server.SPECIALTY_TOOL_MODULES)
        self.assertTrue(any("entities" in spec.modules for spec in TOOLSET_SPECS))
        settings = (ROOT / "maxscript" / "mcp_settings.ms").read_text(encoding="utf-8")
        self.assertIn('#("entities",', settings)


if __name__ == "__main__":
    unittest.main()
