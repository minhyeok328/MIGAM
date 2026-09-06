from datetime import date
from pathlib import Path
import unittest

from backend.data_pipeline.fixture_loader import load_qualification_fixture
from backend.data_pipeline.pipeline import process_records
from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


class SemaExpansionTests(unittest.TestCase):
    def test_each_new_physical_institution_passes_all_five_official_samples(self):
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        records = load_qualification_fixture(ROOT / "fixtures/source-expansion-2026-09-06.json", registry)
        results = process_records(records, registry, as_of=date(2026, 9, 6))
        counts = {}
        for result in results:
            identity = result.normalized.raw_record.institution_id
            self.assertEqual(result.quality.core_result, "PASS", result.quality.issues)
            self.assertEqual(registry.institution(identity)["lifecycle"], "PROVISIONAL")
            counts[identity] = counts.get(identity, 0) + 1
        self.assertEqual(len(counts), 4)
        self.assertEqual(set(counts.values()), {5})
