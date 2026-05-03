"""tests for backup system."""

import json
import os
import tempfile
import shutil
import unittest
from unittest.mock import patch

from sprout.backup import backup, list_backups, rollback, cleanup, BackupError


class TestBackup(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.tmpdir, "backups")
        self.system_config = os.path.join(self.tmpdir, "system.prc")
        self.user_config_dir = os.path.join(self.tmpdir, "users")

        with open(self.system_config, "w") as f:
            f.write("packages\n\tneovim\n")

        os.makedirs(self.user_config_dir, exist_ok=True)
        with open(os.path.join(self.user_config_dir, "john.prc"), "w") as f:
            f.write("packages\n\tfirefox\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_backup_creates_zip(self):
        result = backup(
            [self.system_config, self.user_config_dir],
            description="test backup",
            backup_dir=self.backup_dir,
        )
        self.assertTrue(os.path.isdir(result))
        self.assertTrue(os.path.isfile(os.path.join(result, "system.prc.zip")))
        self.assertTrue(os.path.isfile(os.path.join(result, "metadata.json")))

        with open(os.path.join(result, "metadata.json")) as f:
            meta = json.load(f)
        self.assertEqual(meta["description"], "test backup")
        self.assertIn(self.system_config, meta["files"])

    def test_backup_multiple_same_day(self):
        b1 = backup([self.system_config], description="first", backup_dir=self.backup_dir)
        b2 = backup([self.system_config], description="second", backup_dir=self.backup_dir)
        self.assertNotEqual(b1, b2)
        self.assertTrue(os.path.isdir(b1))
        self.assertTrue(os.path.isdir(b2))

    def test_list_backups(self):
        backup([self.system_config], description="test", backup_dir=self.backup_dir)
        backups = list_backups(backup_dir=self.backup_dir)
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0]["description"], "test")

    def test_list_backups_empty(self):
        backups = list_backups(backup_dir=self.backup_dir)
        self.assertEqual(backups, [])

    def test_rollback_force(self):
        # create a backup first
        backup(
            [self.system_config],
            description="pre-test",
            backup_dir=self.backup_dir,
        )

        # modify the config
        with open(self.system_config, "w") as f:
            f.write("packages\n\tchanged\n")

        # rollback
        backups = list_backups(backup_dir=self.backup_dir)
        self.assertEqual(len(backups), 1)

        rollback(
            target=backups[0]["dir"],
            force=True,
            backup_dir=self.backup_dir,
            system_config=self.system_config,
            user_config_dir=self.user_config_dir,
        )

        # verify it was restored
        with open(self.system_config) as f:
            content = f.read()
        self.assertIn("neovim", content)

    def test_rollback_no_backups(self):
        with patch("sprout.backup.sys.exit", side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                rollback(backup_dir=self.backup_dir, system_config=self.system_config,
                         user_config_dir=self.user_config_dir, force=True)

    def test_cleanup_keeps_minimum(self):
        # create 2 backups — should keep all
        backup([self.system_config], description="b1", backup_dir=self.backup_dir)
        backup([self.system_config], description="b2", backup_dir=self.backup_dir)
        cleanup(max_age_days=0, backup_dir=self.backup_dir)
        backups = list_backups(backup_dir=self.backup_dir)
        self.assertEqual(len(backups), 2)


if __name__ == "__main__":
    unittest.main()
