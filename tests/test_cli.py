"""Unit tests for CLI progress bar rendering and functions."""

import unittest
from src.cli.main import render_progress_bar


class TestCLI(unittest.TestCase):
    def test_render_progress_bar(self):
        bar_100 = render_progress_bar(100.0, width=10)
        self.assertIn("██████████", bar_100)

        bar_50 = render_progress_bar(50.0, width=10)
        self.assertIn("█████░░░░░", bar_50)

        bar_0 = render_progress_bar(0.0, width=10)
        self.assertIn("░░░░░░░░░░", bar_0)


if __name__ == "__main__":
    unittest.main()
