import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

from accessloop.browser import PageEvidence, inspect_page, _record_focus
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
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["inspect", "https://example.org", "--tabs", "3"]), 0)
            adapter.assert_called_once_with("https://example.org", tabs=3, screenshot=None)

    def test_focus_cycles_without_reporting_body_or_duplicate(self):
        focus, seen = [], set()
        self.assertTrue(_record_focus(focus, seen, {"tag": "a", "text": "Learn more", "node_index": 4}))
        self.assertTrue(_record_focus(focus, seen, {"tag": "body", "text": "page", "node_index": 1}))
        self.assertFalse(_record_focus(focus, seen, {"tag": "a", "text": "Learn more", "node_index": 4}))
        self.assertEqual(focus, [{"tag": "a", "text": "Learn more"}])

    def test_identical_labels_on_distinct_controls_are_kept(self):
        focus, seen = [], set()
        self.assertTrue(_record_focus(focus, seen, {"tag": "button", "text": "Continue", "node_index": 4}))
        self.assertTrue(_record_focus(focus, seen, {"tag": "button", "text": "Continue", "node_index": 7}))
        self.assertEqual(len(focus), 2)


if __name__ == "__main__":
    unittest.main()
