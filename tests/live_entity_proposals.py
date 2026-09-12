"""Explicit live smoke: uv run python tests/live_entity_proposals.py.

Creates only ProposalSmoke_* fixtures, removes its nodes and branches in finally,
never resets/saves. Requires TagApi 1.2 loaded.
"""
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maxmcp.max_client import MaxClient
from maxmcp.entity_proposals import ProposalWorker, LocalModels


def main():
    client = MaxClient()
    worker = ProposalWorker("unused")
    created = []
    background = None
    prefix = "ProposalSmoke" + uuid.uuid4().hex[:6]

    def script(code):
        return client.send_command(code, cmd_type="maxscript")["result"]

    def call(method, arg=None):
        return worker.call(client, method, arg)

    def box(suffix, width, height, x=0):
        h = int(script(f'(local n = Box name:"{prefix}_{suffix}" width:{width} length:{width} height:{height} pos:[{x},0,0]; n.inode.handle)'))
        created.append(h)
        return h

    def proposal(batch, path):
        obj = batch["objects"][0]
        return json.dumps({"session": batch["session"], "proposals": [{"handle": obj["handle"], "token": obj["token"], "ranked": [{"path": path, "confidence": .99, "reason": "live verification"}]}]})

    try:
        assert call("Version")["apiVersion"] == "1.2"
        room = box("room", 10, 3)
        path = prefix + "_Room"
        script(f'((dotNetClass "TagManager.TagApi").Apply "{path}" "{room}" false false)')
        obj = box("chair", 1, 1)
        batch = call("RequestEvidence", str(obj))
        assert batch["objects"], batch
        result = call("Present", proposal(batch, path))
        assert result["applied"] == [] and result["queued"] == 1, result
        print("PASS: high-confidence proposal requires review")
        script(f'(local n = maxOps.getNodeByHandle {obj}; n.pos.x = 30)')
        result = call("Present", proposal(batch, path))
        assert result.get("rejected") == 1, result
        print("PASS: moved object rejects stale result")
        script(f'(local n = maxOps.getNodeByHandle {obj}; n.pos.x = 0)')
        batch = call("RequestEvidence", str(obj))
        call("ClearPending", str(obj))
        result = call("Present", proposal(batch, path))
        assert result.get("rejected") == 1, result
        print("PASS: ignored proposal cannot reappear from late model result")
        batch = call("RequestEvidence", str(obj))
        call("Present", proposal(batch, path))
        accepted = script(f'((dotNetClass "TagManager.TagApi").AcceptPending {obj} 0)')
        accepted = json.loads(accepted) if isinstance(accepted, str) else accepted
        assert accepted["ok"], accepted
        script("max undo")
        assert call("GetEntities", str(obj))["objects"][str(obj)] == []
        script("max redo")
        assert path in call("GetEntities", str(obj))["objects"][str(obj)]
        print("PASS: accepted membership undo/redo")
        fresh = box("branch", 1, 1, 20)
        branch = prefix + "_NewBranch"
        script(f'((dotNetClass "TagManager.TagApi").Apply "{branch}" "{fresh}" false false)')
        script("max undo")
        assert branch not in {e["path"] for e in call("ListEntities")["entities"]}
        script("max redo")
        assert branch in {e["path"] for e in call("ListEntities")["entities"]}
        print("PASS: new branch undo/redo")
        script(f'((dotNetClass "TagManager.TagApi").SetEntityZone "{path}" "{room}")')
        assert any(e["path"] == path for e in call("EntityBounds")["entities"])
        extra = box("auto", 1, 1)
        time.sleep(1.6)
        assert any(p["handle"] == extra for p in call("Pending")["pending"])
        print("PASS: creation callback produces provisional suggestion")
        script(f'select (maxOps.getNodeByHandle {extra})')
        call("ReviewProposals")
        print("PASS: inline FastTag opens")
        if len(sys.argv) > 1:
            background = ProposalWorker(sys.argv[1])
            background.start()
            deadline = time.monotonic() + 50
            ranked = False
            while time.monotonic() < deadline:
                pending = call("Pending")["pending"]
                ranked = any(p["handle"] == extra and p["ranked"] and not p["ranked"][0]["reason"].startswith("Provisional:") for p in pending)
                if ranked:
                    break
                time.sleep(.5)
            assert ranked, background.metrics
            print("PASS: background worker delivers real LLM ranking", background.metrics)
    finally:
        if background:
            background.stop_event.set()
            background.thread.join(timeout=5)
        call("ClearPending", ",".join(map(str, created)))
        for h in created:
            script(f'(local n = maxOps.getNodeByHandle {h}; if n != undefined do delete n)')
        script(f'(local e = (dotNetClass "TagManager.TagHelperMethods").RetrieveEntityFromTag "{prefix}"; if e != undefined do e.Parent.Children.Remove e; LayerManager.deleteLayerByName "{prefix}_Room"; LayerManager.deleteLayerByName "{prefix}")')


if __name__ == "__main__":
    main()
