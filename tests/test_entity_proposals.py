import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from maxmcp.entity_proposals import Neighbours, features, validate_ranking, ProposalWorker, LocalModels


class FakeModels:
    def embed(self, texts):
        return [[1, 0] for _ in texts]


class ProposalTests(unittest.TestCase):
    def test_empty_tree_keeps_only_ticketed_architecture_candidates(self):
        obj = {"handle": 1, "candidates": [
            {"path": "Building_Structure_Slabs", "geometryScore": .74, "proposedHierarchy": True},
            {"path": "Site_Paving", "geometryScore": .4, "proposedHierarchy": True},
            {"path": "Stale_Entity", "overlap": 1}]}
        result = Neighbours().candidates(obj, FakeModels(), set())
        self.assertEqual([c["path"] for c in result], ["Building_Structure_Slabs", "Site_Paving"])
        self.assertEqual(validate_ranking([{"path": result[0]["path"], "confidence": .6}], result)[0]["confidence"], .6)

    def test_model_receives_metric_geometry_and_new_hierarchy(self):
        models = LocalModels("test")
        models.ready = True
        requests = []
        def post(route, payload):
            requests.append(payload)
            return {"message": {"content": '{"ranked":[{"path":"Building_Structure_Slabs","confidence":0.6}]}'}}
        models.post = post
        obj = {"sizeMeters": [10, 8, .2], "boundsVolumeM3": 16}
        candidates = [{"path": "Building_Structure_Slabs", "proposedHierarchy": True}]
        self.assertEqual(len(models.rank(obj, candidates)), 1)
        content = json.loads(requests[0]["messages"][1]["content"])
        self.assertEqual(content["object"]["sizeMeters"], [10, 8, .2])
        self.assertEqual(content["object"]["boundsVolumeM3"], 16)
        self.assertTrue(content["candidates"][0]["proposedHierarchy"])

    def test_worker_ranks_geometry_without_existing_entities(self):
        worker = ProposalWorker("test")
        worker.models.rank = lambda obj, candidates: validate_ranking([
            {"path": candidates[0]["path"], "confidence": .6}], candidates)
        with TemporaryDirectory() as directory:
            result = worker.process({"session": "s", "decisionLog": str(Path(directory)/"missing"), "objects": [
                {"handle": 1, "token": "t", "candidates": [{"path": "Building_Structure_Slabs", "proposedHierarchy": True, "geometryScore": .74}]}]}, set())
        self.assertEqual(result["proposals"][0]["token"], "t")
        self.assertEqual(result["proposals"][0]["ranked"][0]["path"], "Building_Structure_Slabs")

    def test_semantic_candidate_outside_spatial_bounds_survives(self):
        neighbours = Neighbours()
        neighbours.rows = [{"handle": 2, "chosen": "Kitchen", "evidence": {"name": "Chair", "class": "Box", "size": [1,1,1]}}]
        obj = {"handle": 1, "name": "Chair", "size": [1,1,1], "candidates": [{"path": "Hall", "overlap": 1}]}
        result = neighbours.candidates(obj, FakeModels(), {"Kitchen", "Hall"})
        self.assertEqual({c["path"] for c in result}, {"Kitchen", "Hall"})
        self.assertGreater(next(c for c in result if c["path"] == "Kitchen")["neighbourScore"], .9)

    def test_ranker_cannot_invent_paths_or_nonfinite_confidence(self):
        for ranking in ([{"path": "Other", "confidence": .9}], [{"path": "Kitchen", "confidence": float("nan")}], [{"path": "Kitchen", "confidence": 2}]):
            with self.assertRaises(ValueError):
                validate_ranking(ranking, [{"path": "Kitchen"}])

    def test_log_excludes_automatic_legacy_and_other_scene_decisions(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/"decisions.jsonl"
            rows = [
                {"handle": 1, "chosen": "Kitchen", "session": "current", "kind": "confirmed", "evidence": {"name": "original"}},
                {"handle": 2, "chosen": "Kitchen", "session": "current", "kind": "automatic", "evidence": {"name": "auto"}},
                {"handle": 3, "chosen": "Kitchen", "session": "old", "kind": "confirmed", "evidence": {"name": "old"}},
                {"handle": 4, "chosen": "Kitchen"},
            ]
            path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            neighbours = Neighbours(); neighbours.refresh(path, "current")
            self.assertEqual([r["handle"] for r in neighbours.rows], [1])

    def test_generated_layer_does_not_leak_into_embedding(self):
        self.assertNotIn("Kitchen", features({"name": "Chair", "class": "Box", "layer": "Kitchen", "entities": ["Kitchen"]}))

    def test_undo_retracts_confirmed_example(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/"decisions.jsonl"
            rows = [{"handle": 1, "session": "s", "kind": "confirmed", "chosen": "Kitchen", "evidence": {"name": "Chair"}},
                    {"handle": 1, "session": "s", "kind": "retracted"}]
            path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            neighbours = Neighbours(); neighbours.refresh(path, "s")
            self.assertEqual(neighbours.rows, [])

    def test_ranker_failure_keeps_provisional_result(self):
        worker = ProposalWorker("test")
        def fail(*args):
            raise ValueError("model offline")
        worker.models.rank = fail
        with TemporaryDirectory() as directory:
            result = worker.process({"session": "s", "decisionLog": str(Path(directory)/"missing"), "objects": [
                {"handle": 1, "token": "t", "candidates": [{"path": "Kitchen", "overlap": 1}]}]}, {"Kitchen"})
        self.assertEqual(result["proposals"], [])
        self.assertIn("offline", worker.metrics["error"])
