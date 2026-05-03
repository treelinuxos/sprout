"""tests for privilege/doas integration."""

import unittest
from unittest.mock import patch, MagicMock

from sprout.privilege import doas, doas_run, PrivilegeError


class TestPrivilege(unittest.TestCase):

    @patch("sprout.privilege.subprocess.run")
    def test_doas_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ok", stderr=""
        )
        out, err, rc = doas("apk", "add", "neovim")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "ok")
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ["doas", "apk", "add", "neovim"])

    @patch("sprout.privilege.subprocess.run")
    def test_doas_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        with self.assertRaises(PrivilegeError) as ctx:
            doas("apk", "add", "neovim")
        self.assertIn("doas not found", str(ctx.exception))

    @patch("sprout.privilege.subprocess.run")
    def test_doas_timeout(self, mock_run):
        mock_run.side_effect = __import__("subprocess").TimeoutExpired("cmd", 300)
        with self.assertRaises(PrivilegeError) as ctx:
            doas("apk", "add", "neovim")
        self.assertIn("timed out", str(ctx.exception))

    @patch("sprout.privilege.subprocess.run")
    def test_doas_run_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        rc = doas_run("apk", "add", "neovim")
        self.assertEqual(rc, 0)

    @patch("sprout.privilege.subprocess.run")
    def test_doas_run_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        with self.assertRaises(PrivilegeError):
            doas_run("apk", "add", "neovim")


if __name__ == "__main__":
    unittest.main()
