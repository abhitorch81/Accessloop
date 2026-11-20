import unittest
from unittest.mock import patch

from accessloop.browser import PageEvidence, inspect_page
from accessloop.cli import main


class BrowserTests(unittest.TestCase):
    def test_rejects_non_web_scheme(self):
        with self.assertRaises(ValueError):
            inspect_page("javascript:alert(1)")

    def test_rejects_invalid_budget(self):
        with self.assertRaises(ValueError):
            inspect_page("https://example.org", tabs=0)

    def test_cli_uses_browser_adapter(self):
        evidence = PageEvidence("https://example.org", "Example", [], [])
        with patch("accessloop.cli.inspect_page", return_value=evidence) as adapter:
            self.assertEqual(main(["inspect", "https://example.org", "--tabs", "3"]), 0)
            adapter.assert_called_once_with("https://example.org", tabs=3, screenshot=None)


if __name__ == "__main__":
    unittest.main()
