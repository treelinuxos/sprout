"""tests for the .smp module runner."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from sprout.runner import run_module, ModuleError, _find_micropython


class TestRunner(unittest.TestCase):

    def test_file_not_found(self):
        with patch("sprout.runner.sys.exit", side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                run_module("/nonexistent/module.smp")

    def test_wrong_extension(self):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        )
        f.write("# test")
        f.close()
        with patch("sprout.runner.sys.exit", side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                run_module(f.name)
        os.unlink(f.name)

    def test_micropython_not_found(self):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".smp", delete=False
        )
        f.write("# test")
        f.close()
        with patch("sprout.runner._find_micropython", return_value=None):
            with patch("sprout.runner.sys.exit", side_effect=SystemExit):
                with self.assertRaises(SystemExit):
                    run_module(f.name)
        os.unlink(f.name)

    @patch("sprout.runner.subprocess.run")
    def test_run_module_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("sprout.runner._find_micropython", return_value="/usr/bin/micropython"):
            f = tempfile.NamedTemporaryFile(
                mode="w", suffix=".smp", delete=False
            )
            f.write("# test")
            f.close()
            run_module(f.name)
            mock_run.assert_called_once()
            os.unlink(f.name)

    @patch("sprout.runner.subprocess.run")
    def test_run_module_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        with patch("sprout.runner._find_micropython", return_value="/usr/bin/micropython"):
            f = tempfile.NamedTemporaryFile(
                mode="w", suffix=".smp", delete=False
            )
            f.write("# test")
            f.close()
            with self.assertRaises(ModuleError):
                run_module(f.name)
            os.unlink(f.name)

    def test_find_micropython_returns_none_when_not_installed(self):
        result = _find_micropython()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
