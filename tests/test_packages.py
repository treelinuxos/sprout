"""tests for apk integration."""

import unittest
from unittest.mock import patch, MagicMock

from sprout.packages import (
    ApkError,
    install,
    remove,
    upgrade,
    search,
    list_installed,
    is_installed,
    info,
    sync,
)


class TestApkWrapper(unittest.TestCase):

    @patch("sprout.packages.subprocess.run")
    def test_install_single(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        install("neovim")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["apk", "add", "neovim"])

    @patch("sprout.packages.subprocess.run")
    def test_install_multiple(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        install(["firefox", "neovim"])
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["apk", "add", "firefox", "neovim"])

    @patch("sprout.packages.subprocess.run")
    def test_remove_purge(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        remove("firefox")
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["apk", "del", "--purge", "firefox"])

    @patch("sprout.packages.subprocess.run")
    def test_remove_no_purge(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        remove("firefox", purge=False)
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["apk", "del", "firefox"])

    @patch("sprout.packages.subprocess.run")
    def test_upgrade_all(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        upgrade()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["apk", "upgrade"])

    @patch("sprout.packages.subprocess.run")
    def test_upgrade_specific(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        upgrade("firefox")
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["apk", "add", "--upgrade", "firefox"])

    @patch("sprout.packages.subprocess.run")
    def test_search(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="firefox\nfirefox-dev\n"
        )
        results = search("firefox")
        self.assertEqual(results, ["firefox", "firefox-dev"])

    @patch("sprout.packages.subprocess.run")
    def test_search_no_results(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        results = search("nonexistent-pkg-xyz")
        self.assertEqual(results, [])

    @patch("sprout.packages.subprocess.run")
    def test_list_installed(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="apk-tools-3.14.0-r0\nbusybox-1.36.1-r0\nzsh-5.9-r0\n",
        )
        result = list_installed()
        self.assertEqual(result, ["apk-tools", "busybox", "zsh"])

    @patch("sprout.packages.subprocess.run")
    def test_is_installed_true(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="neovim-0.9.5-r0\n"
        )
        self.assertTrue(is_installed("neovim"))

    @patch("sprout.packages.subprocess.run")
    def test_is_installed_false(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout=""
        )
        self.assertFalse(is_installed("nonexistent"))

    @patch("sprout.packages.subprocess.run")
    def test_sync(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        sync()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["apk", "update"])

    @patch("sprout.packages.subprocess.run")
    def test_apk_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        with self.assertRaises(ApkError) as ctx:
            install("test")
        self.assertIn("apk not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
