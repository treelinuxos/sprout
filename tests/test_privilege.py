"""tests for privilege/doas integration."""

import unittest
from unittest.mock import patch, MagicMock

from sprout.privilege import (
    is_root,
    require_root,
    doas,
    doas_run,
    PrivilegeError,
)


class TestPrivilege(unittest.TestCase):

    def test_is_root_true(self):
        with patch("sprout.privilege.os.geteuid", return_value=0):
            self.assertTrue(is_root())

    def test_is_root_false(self):
        with patch("sprout.privilege.os.geteuid", return_value=1000):
            self.assertFalse(is_root())

    def test_require_root_passes(self):
        with patch("sprout.privilege.os.geteuid", return_value=0):
            require_root("test")  # should not raise

    def test_require_root_fails(self):
        with patch("sprout.privilege.os.geteuid", return_value=1000):
            with patch("sprout.privilege.sys.exit") as mock_exit:
                require_root("test")
                mock_exit.assert_called_once_with(1)

    @patch("sprout.privilege.subprocess.run")
    def test_doas_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ok", stderr=""
        )
        out, err, rc = doas("apk", "add", "neovim")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "ok")
        mock_run.assert_called_once()
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

    @patch("sprout.privilege.subprocess.run")
    def test_run_with_privilege_as_root(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("sprout.privilege.is_root", return_value=True):
            rc = __import__("sprout.privilege", fromlist=["run_with_privilege"]).run_with_privilege(
                ["apk", "add", "neovim"]
            )
            self.assertEqual(rc, 0)

    @patch("sprout.privilege.subprocess.run")
    def test_run_with_privilege_as_user(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("sprout.privilege.is_root", return_value=False):
            rc = __import__("sprout.privilege", fromlist=["run_with_privilege"]).run_with_privilege(
                ["apk", "add", "neovim"]
            )
            self.assertEqual(rc, 0)
            args = mock_run.call_args[0][0]
            self.assertEqual(args, ["doas", "apk", "add", "neovim"])


if __name__ == "__main__":
    unittest.main()
