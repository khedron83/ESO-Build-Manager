import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import eso_build_manager.storage.database as dbmod
from eso_build_manager.models.build import Build
from eso_build_manager.models.skill import Skill


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._patches = [
            patch.object(dbmod, "DB_DIR", Path(self._tmp)),
            patch.object(dbmod, "DB_PATH", Path(self._tmp) / "test.db"),
        ]
        for p in self._patches:
            p.start()
        dbmod.init_db()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def test_create_and_get(self):
        build_id = dbmod.create_build(Build(name="Sorc DPS", eso_class="Sorcerer", role="MagDPS"))
        result = dbmod.get_build(build_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Sorc DPS")
        self.assertEqual(result.eso_class, "Sorcerer")

    def test_list_builds(self):
        dbmod.create_build(Build(name="Build A"))
        dbmod.create_build(Build(name="Build B"))
        builds = dbmod.list_builds()
        self.assertEqual(len(builds), 2)
        names = {b[1] for b in builds}
        self.assertIn("Build A", names)
        self.assertIn("Build B", names)

    def test_update_build(self):
        build_id = dbmod.create_build(Build(name="Original"))
        build = dbmod.get_build(build_id)
        build.name = "Updated"
        build.role = "Tank"
        dbmod.update_build(build)
        result = dbmod.get_build(build_id)
        self.assertEqual(result.name, "Updated")
        self.assertEqual(result.role, "Tank")

    def test_delete_build(self):
        build_id = dbmod.create_build(Build(name="Temp"))
        dbmod.delete_build(build_id)
        self.assertIsNone(dbmod.get_build(build_id))
        self.assertEqual(dbmod.list_builds(), [])

    def test_gear_seeded_on_create(self):
        build_id = dbmod.create_build(Build(name="Gear Test"))
        gear = dbmod.get_gear(build_id)
        self.assertEqual(len(gear), 14)
        slots = {g.slot for g in gear}
        self.assertIn("Head", slots)
        self.assertIn("Backup Off", slots)

    def test_skills_save_and_load(self):
        build_id = dbmod.create_build(Build(name="Skills Test"))
        skills = [
            Skill(build_id=build_id, bar=0, slot=0, name="Elemental Blockade"),
            Skill(build_id=build_id, bar=0, slot=5, name="Shooting Star"),
        ]
        dbmod.save_skills(build_id, skills)
        result = dbmod.get_skills(build_id)
        names = {s.name for s in result}
        self.assertIn("Elemental Blockade", names)
        self.assertIn("Shooting Star", names)

    def test_duplicate_build(self):
        build_id = dbmod.create_build(Build(name="Original"))
        skills = [Skill(build_id=build_id, bar=0, slot=0, name="Cloak")]
        dbmod.save_skills(build_id, skills)
        new_id = dbmod.duplicate_build(build_id)
        self.assertNotEqual(build_id, new_id)
        copy = dbmod.get_build(new_id)
        self.assertEqual(copy.name, "Original (Copy)")
        copy_skills = dbmod.get_skills(new_id)
        self.assertEqual(copy_skills[0].name, "Cloak")

    def test_delete_cascades_skills(self):
        build_id = dbmod.create_build(Build(name="Cascade Test"))
        dbmod.save_skills(build_id, [Skill(build_id=build_id, bar=0, slot=0, name="Test Skill")])
        dbmod.delete_build(build_id)
        self.assertEqual(dbmod.get_skills(build_id), [])


if __name__ == "__main__":
    unittest.main()
