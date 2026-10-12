from __future__ import annotations

import json
import tempfile
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from common import confirmation_payload_sha256
from extract_code_material import collect_code_lines, MAX_CODE_COLUMNS, display_width, material_code_lines, paginate, wrap_display_line  # noqa: E402


class CodeLayoutTests(unittest.TestCase):
    def test_legacy_confirmed_range_is_not_expanded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.js").write_text("before\nselected\n\nafter\n", encoding="utf-8")
            data = {"selection_required": True, "user_confirmed": True,
                    "files": [{"path": "app.js", "selected": True, "start_line": 2, "end_line": 3}]}
            data["confirmed_content_sha256"] = confirmation_payload_sha256(data)
            selection = root / "selection.json"
            selection.write_text(json.dumps(data), encoding="utf-8")
            lines, manifest = collect_code_lines(root, selection)
            self.assertEqual(lines, ["// File: app.js", "selected"])
            self.assertEqual((manifest[0]["selected_line_start"], manifest[0]["selected_line_end"]), (2, 3))
            data["files"][0]["end_line"] = 4
            selection.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(SystemExit):
                collect_code_lines(root, selection)
            data["files"][0]["end_line"] = 99
            data["confirmed_content_sha256"] = confirmation_payload_sha256(data)
            selection.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(SystemExit):
                collect_code_lines(root, selection)

    def test_display_width_counts_cjk_as_two_columns(self) -> None:
        self.assertEqual(display_width("abc中文"), 7)

    def test_long_line_wrap_preserves_all_characters(self) -> None:
        source = "const value = '" + ("中" * 70) + ("x" * 80) + "';"
        wrapped = wrap_display_line(source, 100)
        self.assertGreater(len(wrapped), 1)
        self.assertEqual("".join(wrapped), source)
        self.assertTrue(all(display_width(line) <= 100 for line in wrapped))

    def test_tabs_are_expanded_before_wrapping(self) -> None:
        wrapped = wrap_display_line("a\tb", 100)
        self.assertEqual(wrapped, ["a   b"])

    def test_material_lines_drop_blanks_and_wrap(self) -> None:
        material = material_code_lines("\nshort\n" + ("x" * 101) + "\n")
        self.assertEqual(material, ["short", "x" * MAX_CODE_COLUMNS, "x" * (101 - MAX_CODE_COLUMNS)])

    def test_paginate_uses_physical_lines(self) -> None:
        pages = paginate([str(i) for i in range(101)], 50)
        self.assertEqual([len(page) for page in pages], [50, 50, 1])


if __name__ == "__main__":
    unittest.main()
