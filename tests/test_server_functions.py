import json
import unittest

from lego_set_binary_format import decode_lego_set_binary
from server import (
    SET_CACHE,
    SET_CACHE_LOCK,
    generate_set_binary,
    generate_set_json,
    generate_sets_page_html,
)


class MockDatabase:
    def __init__(self, expected_calls):
        self.expected_calls = list(expected_calls)
        self.closed = False

    def execute_and_fetch_all(self, query):
        if len(self.expected_calls) == 0:
            raise AssertionError(f"Unexpected query: {query}")

        expected_query, response_rows = self.expected_calls.pop(0)
        if query != expected_query:
            raise AssertionError(
                "Unexpected query.\n"
                f"Expected: {expected_query}\n"
                f"Actual:   {query}"
            )
        return response_rows

    def close(self):
        self.closed = True


class ServerFunctionTests(unittest.TestCase):
    def setUp(self):
        with SET_CACHE_LOCK:
            SET_CACHE.clear()

    def test_generate_sets_page_html_renders_escaped_rows(self):
        template = "{META_CHARSET}<tbody>{ROWS}</tbody>"
        rows = [
            ("<set-1>", "Name & Co"),
            ("safe-2", '"quoted" <b>tag</b>'),
        ]
        database = MockDatabase([
            ("select id, name from lego_set order by id", rows),
        ])

        html_result = generate_sets_page_html(database, template, "utf-8")

        self.assertIn('<meta charset="UTF-8">', html_result)
        self.assertIn('&lt;set-1&gt;', html_result)
        self.assertIn('Name &amp; Co', html_result)
        self.assertIn('&quot;quoted&quot; &lt;b&gt;tag&lt;/b&gt;', html_result)

    def test_generate_set_json_queries_expected_sql_and_formats_output(self):
        set_id = "abc-1"
        set_query = (
            "select id, name, year, category, preview_image_url "
            "from lego_set "
            "where id = 'abc-1'"
        )
        inventory_query = (
            "select i.brick_type_id, i.color_id, i.count, b.name, b.preview_image_url "
            "from lego_inventory i "
            "join lego_brick b on b.brick_type_id = i.brick_type_id and b.color_id = i.color_id "
            "where i.set_id = 'abc-1' "
            "order by i.brick_type_id, i.color_id"
        )
        database = MockDatabase([
            (set_query, [("abc-1", "Cool Set", 2020, "Space", "https://example.com/set.png")]),
            (inventory_query, [("3001", 5, 2, "Brick 2x4", "https://example.com/brick.png")]),
        ])

        json_result = generate_set_json(database, set_id)
        parsed = json.loads(json_result)

        self.assertEqual(parsed["set"]["id"], "abc-1")
        self.assertEqual(parsed["set"]["name"], "Cool Set")
        self.assertEqual(parsed["inventory"][0]["brickTypeId"], "3001")
        self.assertEqual(parsed["inventory"][0]["count"], 2)
        self.assertEqual(database.expected_calls, [])

    def test_generate_set_json_returns_none_for_unknown_set(self):
        set_id = "missing-1"
        set_query = (
            "select id, name, year, category, preview_image_url "
            "from lego_set "
            "where id = 'missing-1'"
        )
        database = MockDatabase([
            (set_query, []),
        ])

        json_result = generate_set_json(database, set_id)

        self.assertIsNone(json_result)
        self.assertEqual(database.expected_calls, [])

    def test_generate_set_binary_uses_expected_queries_and_encodes_payload(self):
        set_id = "bin-1"
        set_query = (
            "select id, name, year, category, preview_image_url "
            "from lego_set "
            "where id = 'bin-1'"
        )
        inventory_query = (
            "select i.brick_type_id, i.color_id, i.count, b.name, b.preview_image_url "
            "from lego_inventory i "
            "join lego_brick b on b.brick_type_id = i.brick_type_id and b.color_id = i.color_id "
            "where i.set_id = 'bin-1' "
            "order by i.brick_type_id, i.color_id"
        )
        database = MockDatabase([
            (set_query, [("bin-1", "Binary Set", 1999, "Classic", None)]),
            (inventory_query, [("3005", 1, 10, "Brick 1x1", None)]),
        ])

        binary_result = generate_set_binary(database, set_id)
        decoded = decode_lego_set_binary(binary_result)

        self.assertEqual(decoded["set"]["id"], "bin-1")
        self.assertEqual(decoded["set"]["name"], "Binary Set")
        self.assertEqual(decoded["inventory"][0]["brickTypeId"], "3005")
        self.assertEqual(decoded["inventory"][0]["count"], 10)
        self.assertEqual(database.expected_calls, [])


if __name__ == "__main__":
    unittest.main()
