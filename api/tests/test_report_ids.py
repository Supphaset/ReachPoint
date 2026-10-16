"""Report IDs stay unique when demo examples are removed and the server restarts."""

import tempfile
import unittest
from pathlib import Path

from api.server.memory import Clock, MemoryStore
from api.server.sqlite_store import SQLiteMemoryStore, SQLiteState


class ReportIdTests(unittest.TestCase):
    def submit(self, memory):
        return memory.write(None, lambda: memory.submit_report("Synthetic request", "form", {}))["value"]

    def test_gaps_do_not_collide_with_retained_reports(self):
        memory = MemoryStore()
        for _ in range(6):
            self.submit(memory)
        memory.store.seed["reports"] = memory.store.seed["reports"][2:]
        report = self.submit(memory)
        self.assertEqual(report["reportId"], "R-007")
        ids = [row["reportId"] for row in memory.store.seed["reports"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_deleted_highest_id_is_not_reused_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteState(str(Path(directory) / "demo.sqlite3"))
            try:
                memory = SQLiteMemoryStore(database, Clock())
                for _ in range(3):
                    self.submit(memory)
                memory.write(None, lambda: memory.store.seed.__setitem__("reports", []))
                restored = SQLiteMemoryStore(database, Clock())
                self.assertEqual(self.submit(restored)["reportId"], "R-004")
            finally:
                database._db.close()

    def test_legacy_snapshot_starts_after_highest_existing_number(self):
        memory = MemoryStore(seed={"reports": [{"reportId": "R-012"}, {"reportId": "R-003"}]})
        self.assertEqual(self.submit(memory)["reportId"], "R-013")


if __name__ == "__main__":
    unittest.main()
