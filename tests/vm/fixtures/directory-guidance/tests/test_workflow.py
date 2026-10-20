"""Baseline behavior shared by the independent directory-guidance VM cases."""

import unittest

from catalog.labels import normalize_label
from exports.render import render_lines


class WorkflowTests(unittest.TestCase):
    def test_label_normalization(self):
        self.assertEqual(normalize_label("  Straße  "), "strasse")
        self.assertEqual(normalize_label(" A  B "), "a  b")
        self.assertEqual(normalize_label(" \t"), "")

    def test_export_preserves_prepared_labels(self):
        self.assertEqual(render_lines(["Ada", "a  b"]), "Ada\na  b\n")
        self.assertEqual(render_lines([]), "")

    def test_catalog_to_export(self):
        labels = [normalize_label(value) for value in [" Ada ", " STRASSE "]]
        self.assertEqual(render_lines(labels), "ada\nstrasse\n")


if __name__ == "__main__":
    unittest.main()
