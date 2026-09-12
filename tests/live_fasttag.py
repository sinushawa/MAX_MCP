"""Manual UI smoke, after build_tagmanager_probes.ps1, in an empty Max test session.

Requires installed TagApi 1.2. Does not reset or save the scene. Scoped fixtures
are removed; refuses to run when user objects/entities already exist.
"""
import json
from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maxmcp.max_client import MaxClient
from maxmcp.entity_proposals import ProposalWorker


def main():
    root = Path(__file__).resolve().parents[1]
    client = MaxClient()
    worker = ProposalWorker("unused")
    def script(code):
        return client.send_command(code, cmd_type="maxscript")["result"]
    def call(method, arg=None):
        return worker.call(client, method, arg)
    def probe(method, arg=None):
        tail = "()" if arg is None else " " + json.dumps(arg)
        result = script('(dotNetClass "FastTagLiveProbe").' + method + tail)
        if isinstance(result, str) and result.startswith("{"):
            return json.loads(result)
        return result
    assert call("Version")["apiVersion"] == "1.2", "Restart with the rebuilt plugin first"
    assert int(script("objects.count")) == 0, "Use an empty test session"
    assert call("ListEntities")["entities"] == [], "Use an empty entity tree"
    dll = (root / "local/tagmanager-tests/FastTagLiveProbe.dll").as_posix()
    script(f'dotNet.loadAssembly "{dll}"')
    print(probe("Shapes"))
    created = []
    try:
        call("ReviewProposals")
        time.sleep(.3)
        state = probe("State")
        assert state["open"] and state["text"] == "" and len(state["paths"]) >= 6, state
        assert state["height"] == 30, state
        assert call("ListEntities")["entities"] == []
        print("PASS: truly empty scene opens starter autocomplete, no hierarchy created")
        probe("Close")

        # Use units.decodeValue so the fixture has metric dimensions in any system unit.
        name = "FastTagSmoke" + uuid.uuid4().hex[:8]
        handle = int(script(f'(local n = Box name:"{name}" width:(units.decodeValue "10m") length:(units.decodeValue "8m") height:(units.decodeValue "0.2m"); n.inode.handle)'))
        created.append(handle)
        script(f'select (maxOps.getNodeByHandle {handle})')
        call("ReviewProposals")
        time.sleep(.3)
        state = probe("State")
        assert state["open"] and state["text"] == "", state
        assert state["paths"][0] == "Building_Structure_Slabs", state
        evidence = call("Evidence", str(handle))["objects"][0]
        assert all(abs(a-b) < .001 for a, b in zip(evidence["sizeMeters"], [10, 8, .2])), evidence
        assert abs(evidence["boundsVolumeM3"] - 16) < .01, evidence
        image = (root / "local/tagmanager-tests/fasttag-slab.png").as_posix()
        probe("Capture", image)
        print("PASS: blank input offers slabs from metric shape alone; screenshot:", image)
        probe("Key", "Down")
        state = probe("State")
        assert state["text"] == "Building_Structure_Slabs", state
        probe("Key", "Return")
        assert "Building_Structure_Slabs" in call("GetEntities", str(handle))["objects"][str(handle)]
        assert not probe("State")["loaded"]
        script("max undo")
        assert call("ListEntities")["entities"] == []
        assert call("GetEntities", str(handle))["objects"][str(handle)] == []
        script("max redo")
        assert "Building_Structure_Slabs" in call("GetEntities", str(handle))["objects"][str(handle)]
        print("PASS: arrow + Enter creates nested hierarchy and membership; one-step undo/redo")
        script("max undo")
        call("ReviewProposals")
        time.sleep(.3)
        probe("Key", "W")
        probe("Text", "Paving")
        time.sleep(.3)
        state = probe("State")
        assert state["paths"] and all("Paving" in p for p in state["paths"]), state
        probe("Key", "Escape")
        assert call("GetEntities", str(handle))["objects"][str(handle)] == []
        print("PASS: typing filters existing dropdown; Escape does not assign")
    finally:
        try:
            probe("Close")
        except Exception:
            pass
        for handle in created:
            script(f'(local n = maxOps.getNodeByHandle {handle}; if n != undefined do delete n)')
        # Branch creation is undone by the test; never delete an unexpected user branch.


if __name__ == "__main__":
    main()
