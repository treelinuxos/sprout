"""tests for user config management."""

import os
import tempfile
import shutil
import unittest
from unittest.mock import patch

from sprout.users import (
    create_user_config,
    get_user_config,
    list_user_configs,
    remove_user_config,
    add_to_user_config,
    remove_from_user_config,
)


class TestUserConfig(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.user_dir = os.path.join(self.tmpdir, "users")
        os.makedirs(self.user_dir, exist_ok=True)

        # patch utils paths
        import sprout.utils
        self.orig_user_config_dir = sprout.utils.USER_CONFIG_DIR
        sprout.utils.USER_CONFIG_DIR = self.user_dir

    def tearDown(self):
        import sprout.utils
        sprout.utils.USER_CONFIG_DIR = self.orig_user_config_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_user_config(self):
        with patch("sprout.users.utils.is_root", return_value=True):
            with patch("sprout.users.utils.ensure_dirs"):
                create_user_config("john", packages=["neovim"], shell="zsh")
        path = os.path.join(self.user_dir, "john.prc")
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            content = f.read()
        self.assertIn("packages", content)
        self.assertIn("\tneovim", content)
        self.assertIn("user", content)
        self.assertIn("\tname john", content)
        self.assertIn("\tshell zsh", content)

    def test_get_user_config_exists(self):
        with patch("sprout.users.utils.is_root", return_value=True):
            with patch("sprout.users.utils.ensure_dirs"):
                create_user_config("jane")
        result = get_user_config("jane")
        self.assertTrue(result.endswith("jane.prc"))

    def test_get_user_config_not_exists(self):
        result = get_user_config("nobody")
        self.assertIsNone(result)

    def test_list_user_configs(self):
        with patch("sprout.users.utils.is_root", return_value=True):
            with patch("sprout.users.utils.ensure_dirs"):
                create_user_config("alice")
                create_user_config("bob")
        configs = list_user_configs()
        self.assertEqual(len(configs), 2)
        names = [c[0] for c in configs]
        self.assertIn("alice", names)
        self.assertIn("bob", names)

    def test_list_user_configs_empty(self):
        configs = list_user_configs()
        self.assertEqual(configs, [])

    def test_remove_user_config(self):
        with patch("sprout.users.utils.is_root", return_value=True):
            with patch("sprout.users.utils.ensure_dirs"):
                create_user_config("charlie")
        with patch("sprout.users.utils.is_root", return_value=True):
            remove_user_config("charlie")
        path = os.path.join(self.user_dir, "charlie.prc")
        self.assertFalse(os.path.isfile(path))

    def test_add_to_user_config_new_block(self):
        with patch("sprout.users.utils.is_root", return_value=True):
            with patch("sprout.users.utils.ensure_dirs"):
                create_user_config("dave")
        with patch.dict("os.environ", {"USER": "dave"}):
            add_to_user_config("dave", "packages", ["firefox"])
        path = os.path.join(self.user_dir, "dave.prc")
        with open(path) as f:
            content = f.read()
        self.assertIn("packages", content)
        self.assertIn("\tfirefox", content)

    def test_add_to_user_config_existing_block(self):
        with patch("sprout.users.utils.is_root", return_value=True):
            with patch("sprout.users.utils.ensure_dirs"):
                create_user_config("eve", packages=["neovim"])
        with patch.dict("os.environ", {"USER": "eve"}):
            add_to_user_config("eve", "packages", ["vim"])
        path = os.path.join(self.user_dir, "eve.prc")
        with open(path) as f:
            content = f.read()
        self.assertIn("\tneovim", content)
        self.assertIn("\tvim", content)

    def test_remove_from_user_config(self):
        with patch("sprout.users.utils.is_root", return_value=True):
            with patch("sprout.users.utils.ensure_dirs"):
                create_user_config("frank", packages=["neovim", "vim"])
        with patch.dict("os.environ", {"USER": "frank"}):
            remove_from_user_config("frank", "packages", ["vim"])
        path = os.path.join(self.user_dir, "frank.prc")
        with open(path) as f:
            content = f.read()
        self.assertIn("\tneovim", content)
        self.assertNotIn("\tvim", content)


if __name__ == "__main__":
    unittest.main()
