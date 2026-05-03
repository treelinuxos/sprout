"""tests for the .prc parser."""

import os
import tempfile
import unittest

from sprout.parser import parse, ParseError, resolve_includes


class TestParser(unittest.TestCase):

    def _write(self, content):
        """write content to a temp .prc file and return the path."""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".prc", delete=False
        )
        f.write(content)
        f.close()
        return f.name

    def test_empty_file(self):
        path = self._write("")
        result = parse(path)
        self.assertEqual(result["blocks"], {})
        self.assertEqual(result["includes"], [])
        os.unlink(path)

    def test_comments_only(self):
        path = self._write("# just a comment\n# another one\n")
        result = parse(path)
        self.assertEqual(result["blocks"], {})
        self.assertEqual(result["includes"], [])
        os.unlink(path)

    def test_simple_list_block(self):
        path = self._write(
            "packages\n\tfirefox\n\tneovim\n"
        )
        result = parse(path)
        self.assertEqual(
            result["blocks"]["packages"], ["firefox", "neovim"]
        )
        os.unlink(path)

    def test_kv_block(self):
        path = self._write(
            "user\n\tname john\n\tshell zsh\n"
        )
        result = parse(path)
        self.assertEqual(result["blocks"]["user"]["name"], "john")
        self.assertEqual(result["blocks"]["user"]["shell"], "zsh")
        os.unlink(path)

    def test_include(self):
        path = self._write("include networking.prc\n")
        result = parse(path)
        self.assertEqual(result["includes"], ["networking.prc"])
        os.unlink(path)

    def test_multiple_blocks(self):
        content = (
            "packages\n\tfirefox\n\tneovim\n\n"
            "services\n\tenable networking\n\n"
            "user\n\tname john\n\tshell zsh\n"
        )
        path = self._write(content)
        result = parse(path)
        self.assertEqual(
            result["blocks"]["packages"], ["firefox", "neovim"]
        )
        self.assertEqual(
            result["blocks"]["services"], ["enable networking"]
        )
        self.assertEqual(result["blocks"]["user"]["name"], "john")
        os.unlink(path)

    def test_include_inside_block(self):
        # includes are allowed anywhere
        path = self._write(
            "packages\n\tfirefox\n\tinclude networking.prc\n"
        )
        result = parse(path)
        self.assertIn("networking.prc", result["includes"])
        os.unlink(path)

    def test_indented_outside_block_raises(self):
        path = self._write("\torphan_item\n")
        with self.assertRaises(ParseError):
            parse(path)

    def test_duplicate_block_raises(self):
        path = self._write(
            "packages\n\tfirefox\n\npackages\n\tneovim\n"
        )
        with self.assertRaises(ParseError):
            parse(path)

    def test_multiple_includes(self):
        path = self._write(
            "include a.prc\ninclude b.prc\ninclude c.prc\n"
        )
        result = parse(path)
        self.assertEqual(
            result["includes"], ["a.prc", "b.prc", "c.prc"]
        )
        os.unlink(path)

    def test_empty_block(self):
        path = self._write("packages\n\nservices\n\tenable foo\n")
        result = parse(path)
        self.assertEqual(result["blocks"]["packages"], [])
        self.assertEqual(
            result["blocks"]["services"], ["enable foo"]
        )
        os.unlink(path)


class TestResolveIncludes(unittest.TestCase):

    def _write(self, content, name=".prc"):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=name, delete=False
        )
        f.write(content)
        f.close()
        return f.name

    def test_resolve_simple(self):
        # create an included file
        inc = self._write("packages\n\tneovim\n")
        main = self._write(f"include {os.path.basename(inc)}\n")
        include_dir = os.path.dirname(inc)

        config = parse(main)
        result = resolve_includes(config, main, include_dirs=[include_dir])
        self.assertIn("neovim", result["blocks"]["packages"])

        os.unlink(main)
        os.unlink(inc)

    def test_missing_include_raises(self):
        main = self._write("include nonexistent.prc\n")
        config = parse(main)
        with self.assertRaises(ParseError):
            resolve_includes(config, main, include_dirs=["/tmp"])
        os.unlink(main)


if __name__ == "__main__":
    unittest.main()
