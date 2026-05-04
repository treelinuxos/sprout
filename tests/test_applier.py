"""tests for the apply command."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from sprout.applier import apply
from sprout.utils import append_to_config


class TestAppendToConfig(unittest.TestCase):

    def _write(self, content):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".prc", delete=False
        )
        f.write(content)
        f.close()
        return f.name

    def test_append_to_existing_block(self):
        path = self._write("packages\n\tneovim\n")
        append_to_config(path, "packages", ["vim"])
        with open(path) as f:
            content = f.read()
        self.assertIn("\tneovim", content)
        self.assertIn("\tvim", content)

    def test_create_new_block(self):
        path = self._write("packages\n\tneovim\n")
        append_to_config(path, "services", ["enable networking"])
        with open(path) as f:
            content = f.read()
        self.assertIn("services", content)
        self.assertIn("\tenable networking", content)

    def test_append_multiple_items(self):
        path = self._write("packages\n\tneovim\n")
        append_to_config(path, "packages", ["vim", "htop"])
        with open(path) as f:
            content = f.read()
        self.assertIn("\tvim", content)
        self.assertIn("\thtop", content)

    def test_preserves_comments(self):
        path = self._write("# my config\npackages\n\tneovim\n")
        append_to_config(path, "packages", ["vim"])
        with open(path) as f:
            content = f.read()
        self.assertIn("# my config", content)


class TestApply(unittest.TestCase):

    def _write(self, content):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".prc", delete=False
        )
        f.write(content)
        f.close()
        return f.name

    @patch("sprout.applier.backup")
    @patch("sprout.applier.remove")
    @patch("sprout.applier.install")
    @patch("sprout.packages.list_installed", return_value=[])
    @patch("sprout.diff.SystemState")
    def test_apply_installs_missing(self, mock_state_cls, mock_list_installed, mock_install, mock_remove, mock_backup):
        path = self._write("packages\n\tvim\n")

        mock_state = MagicMock()
        mock_state.installed_packages = set()
        mock_state_cls.return_value = mock_state

        apply(path, interactive=False, dry_run=False)

        mock_install.assert_called_once()
        args = mock_install.call_args[0][0]
        self.assertIn("vim", args)

        os.unlink(path)

    @patch("sprout.applier.backup")
    @patch("sprout.applier.remove")
    @patch("sprout.applier.install")
    @patch("sprout.packages.list_installed", return_value=["neovim", "firefox"])
    @patch("sprout.diff.SystemState")
    def test_apply_removes_extra(self, mock_state_cls, mock_list_installed, mock_install, mock_remove, mock_backup):
        path = self._write("packages\n\tneovim\n")

        mock_state = MagicMock()
        mock_state.installed_packages = {"neovim", "firefox"}
        mock_state_cls.return_value = mock_state

        with patch("sprout.applier.input", return_value="r"):
            apply(path, interactive=True, dry_run=False)

        mock_remove.assert_called_once()
        args = mock_remove.call_args[0][0]
        self.assertIn("firefox", args)

        os.unlink(path)

    @patch("sprout.applier.backup")
    @patch("sprout.applier.install")
    @patch("sprout.packages.list_installed", return_value=["neovim"])
    @patch("sprout.diff.SystemState")
    def test_apply_dry_run(self, mock_state_cls, mock_list_installed, mock_install, mock_backup):
        path = self._write("packages\n\tneovim\n")

        mock_state = MagicMock()
        mock_state.installed_packages = set()
        mock_state_cls.return_value = mock_state

        apply(path, interactive=False, dry_run=True)

        mock_install.assert_not_called()
        mock_backup.assert_not_called()

        os.unlink(path)

    @patch("sprout.applier.backup")
    @patch("sprout.applier.install")
    @patch("sprout.packages.list_installed", return_value=["neovim"])
    @patch("sprout.diff.SystemState")
    def test_apply_no_changes(self, mock_state_cls, mock_list_installed, mock_install, mock_backup):
        path = self._write("packages\n\tneovim\n")

        mock_state = MagicMock()
        mock_state.installed_packages = {"neovim"}
        mock_state_cls.return_value = mock_state

        apply(path, interactive=False, dry_run=False)

        mock_install.assert_not_called()
        mock_backup.assert_not_called()

        os.unlink(path)


if __name__ == "__main__":
    unittest.main()
