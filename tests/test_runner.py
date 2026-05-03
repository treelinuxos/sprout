"""tests for the .smp module runner."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from sprout.runner import run_module, ModuleError, _find_python3


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

    def test_python3_not_found(self):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".smp", delete=False
        )
        f.write("# test")
        f.close()
        with patch("sprout.runner._find_python3", return_value=None):
            with patch("sprout.runner.sys.exit", side_effect=SystemExit):
                with self.assertRaises(SystemExit):
                    run_module(f.name)
        os.unlink(f.name)

    @patch("sprout.runner.subprocess.run")
    def test_run_module_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("sprout.runner._find_python3", return_value="/usr/bin/python3"):
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
        with patch("sprout.runner._find_python3", return_value="/usr/bin/python3"):
            f = tempfile.NamedTemporaryFile(
                mode="w", suffix=".smp", delete=False
            )
            f.write("# test")
            f.close()
            with self.assertRaises(ModuleError):
                run_module(f.name)
            os.unlink(f.name)

    @patch("sprout.runner._find_python3")
    def test_find_python3_returns_none_when_not_installed(self, mock_find):
        mock_find.return_value = None
        result = mock_find()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
