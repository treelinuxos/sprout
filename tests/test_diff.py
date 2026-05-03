"""tests for the diff engine."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from sprout.diff import diff_config, diff_system, SystemState, format_diff


class TestDiffConfig(unittest.TestCase):

    def _write(self, content):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".prc", delete=False
        )
        f.write(content)
        f.close()
        return f.name

    def test_no_diff_when_synced(self):
        path = self._write("packages\n\tneovim\n")
        state = SystemState()
        state.installed_packages = {"neovim"}
        result = diff_config(path, state)
        self.assertEqual(result["packages"]["to_install"], [])
        self.assertEqual(result["packages"]["to_remove"], [])
        os.unlink(path)

    def test_to_install(self):
        path = self._write("packages\n\tneovim\n\tfirefox\n")
        state = SystemState()
        state.installed_packages = {"neovim"}
        result = diff_config(path, state)
        self.assertIn("firefox", result["packages"]["to_install"])
        self.assertEqual(result["packages"]["to_remove"], [])
        os.unlink(path)

    def test_to_remove(self):
        path = self._write("packages\n\tneovim\n")
        state = SystemState()
        state.installed_packages = {"neovim", "firefox", "htop"}
        result = diff_config(path, state)
        self.assertEqual(result["packages"]["to_install"], [])
        self.assertIn("firefox", result["packages"]["to_remove"])
        self.assertIn("htop", result["packages"]["to_remove"])
        os.unlink(path)

    def test_to_install_and_remove(self):
        path = self._write("packages\n\tneovim\n\tvim\n")
        state = SystemState()
        state.installed_packages = {"neovim", "emacs"}
        result = diff_config(path, state)
        self.assertIn("vim", result["packages"]["to_install"])
        self.assertIn("emacs", result["packages"]["to_remove"])
        os.unlink(path)

    def test_services_diff(self):
        path = self._write("services\n\tenable networking\n\tenable sshd\n")
        state = SystemState()
        state.installed_packages = set()
        with patch("sprout.diff._get_enabled_services", return_value={"networking"}):
            result = diff_config(path, state)
            self.assertIn("sshd", result["services"]["to_enable"])
        os.unlink(path)

    def test_empty_packages(self):
        path = self._write("")
        state = SystemState()
        state.installed_packages = {"neovim", "firefox"}
        result = diff_config(path, state)
        self.assertEqual(result["packages"]["to_install"], [])
        self.assertIn("neovim", result["packages"]["to_remove"])
        self.assertIn("firefox", result["packages"]["to_remove"])
        os.unlink(path)

    def test_with_includes(self):
        inc = self._write("packages\n\tvim\n")
        main = self._write(
            f"packages\n\tneovim\n\ninclude {os.path.basename(inc)}\n"
        )
        include_dir = os.path.dirname(inc)

        state = SystemState()
        state.installed_packages = {"neovim"}

        config = __import__("sprout.parser", fromlist=["parse"]).parse(main)
        config = __import__("sprout.parser", fromlist=["resolve_includes"]).resolve_includes(
            config, main, include_dirs=[include_dir]
        )

        # vim should be in desired packages
        self.assertIn("vim", config["blocks"]["packages"])

        os.unlink(main)
        os.unlink(inc)


class TestFormatDiff(unittest.TestCase):

    def test_synced_output(self):
        diff = {
            "system": {
                "packages": {"to_install": [], "to_remove": []},
                "services": {"to_enable": [], "to_disable": []},
            },
            "users": {},
        }
        output = format_diff(diff)
        self.assertIn("in sync", output)

    def test_to_install_output(self):
        diff = {
            "system": {
                "packages": {"to_install": ["neovim", "vim"], "to_remove": []},
                "services": {"to_enable": [], "to_disable": []},
            },
            "users": {},
        }
        output = format_diff(diff)
        self.assertIn("+ neovim", output)
        self.assertIn("+ vim", output)

    def test_to_remove_output(self):
        diff = {
            "system": {
                "packages": {"to_install": [], "to_remove": ["firefox"]},
                "services": {"to_enable": [], "to_disable": []},
            },
            "users": {},
        }
        output = format_diff(diff)
        self.assertIn("- firefox", output)


if __name__ == "__main__":
    unittest.main()
