import json
import unittest

from server import render_sets_page, render_api_set_json, SET_CACHE


class MockDatabaseForSets:
    def __init__(self):
        self.closed = False

    def execute_and_fetch_all(self, query):
        expected_query = "SELECT id, name FROM lego_set ORDER BY id"
        assert query.strip() == expected_query, f"Unexpected query: {query}"
        return [
            ("123-1", "Test Set"),
            ("456-1", "Another Set"),
        ]

    def close(self):
        self.closed = True


class MockDatabaseForApiSet:
    def __init__(self):
        self.closed = False
        self.queries = []

    def execute_and_fetch_all(self, query):
        self.queries.append(query)

        if "FROM lego_set" in query:
            assert "71779-1" in query, f"Expected set id in query, got: {query}"
            return [
                (
                    "71779-1",
                    "Lloyd's Dragon Power Spin",
                    2023,
                    "Catalog: Sets: NINJAGO: Dragons Rising Season 1",
                    "https://img.bricklink.com/ItemImage/ST/0/71779-1.t1.png",
                )
            ]

        if "FROM lego_inventory" in query:
            assert "71779-1" in query, f"Expected set id in query, got: {query}"
            return [
                (
                    "15535",
                    6,
                    4,
                    "Green Tile, Round 2 x 2 with Hole",
                    "https://img.bricklink.com/P/6/15535.jpg",
                ),
                (
                    "18674",
                    11,
                    1,
                    "Black Tile, Round 2 x 2 with Open Stud",
                    "https://img.bricklink.com/P/11/18674.jpg",
                ),
            ]

        raise AssertionError(f"Unexpected query: {query}")

    def close(self):
        self.closed = True


class MockDatabaseNotFound:
    def __init__(self):
        self.closed = False

    def execute_and_fetch_all(self, query):
        if "FROM lego_set" in query:
            return []
        if "FROM lego_inventory" in query:
            return []
        raise AssertionError(f"Unexpected query: {query}")

    def close(self):
        self.closed = True


class MockDatabaseInvalidShouldNotBeUsed:
    def __init__(self):
        self.closed = False

    def execute_and_fetch_all(self, query):
        raise AssertionError("Database should not be called for invalid input")

    def close(self):
        self.closed = True


class ServerTests(unittest.TestCase):
    def setUp(self):
        SET_CACHE.clear()

    def test_render_sets_page(self):
        db = MockDatabaseForSets()

        html_result = render_sets_page(db)

        self.assertIn("123-1", html_result)
        self.assertIn("Test Set", html_result)
        self.assertIn('/set?id=123-1', html_result)
        self.assertIn("456-1", html_result)
        self.assertIn("Another Set", html_result)

    def test_render_api_set_json_success(self):
        db = MockDatabaseForApiSet()

        json_result = render_api_set_json(db, "71779-1")
        data = json.loads(json_result)

        self.assertIn("set", data)
        self.assertIn("inventory", data)

        self.assertEqual(data["set"]["id"], "71779-1")
        self.assertEqual(data["set"]["name"], "Lloyd's Dragon Power Spin")
        self.assertEqual(data["set"]["year"], 2023)
        self.assertEqual(
            data["set"]["category"],
            "Catalog: Sets: NINJAGO: Dragons Rising Season 1",
        )
        self.assertEqual(
            data["set"]["preview_image_url"],
            "https://img.bricklink.com/ItemImage/ST/0/71779-1.t1.png",
        )

        self.assertEqual(len(data["inventory"]), 2)
        self.assertEqual(data["inventory"][0]["brick_type_id"], "15535")
        self.assertEqual(data["inventory"][0]["color_id"], 6)
        self.assertEqual(data["inventory"][0]["count"], 4)
        self.assertEqual(
            data["inventory"][0]["name"],
            "Green Tile, Round 2 x 2 with Hole",
        )
        self.assertEqual(
            data["inventory"][0]["preview_image_url"],
            "https://img.bricklink.com/P/6/15535.jpg",
        )

    def test_render_api_set_json_not_found(self):
        db = MockDatabaseNotFound()

        json_result = render_api_set_json(db, "does-not-exist")
        data = json.loads(json_result)

        self.assertEqual(data["error"], "Set not found")

    def test_render_api_set_json_missing_id(self):
        db = MockDatabaseInvalidShouldNotBeUsed()

        json_result = render_api_set_json(db, None)
        data = json.loads(json_result)

        self.assertEqual(data["error"], "Missing set id")

    def test_render_api_set_json_invalid_id(self):
        db = MockDatabaseInvalidShouldNotBeUsed()

        json_result = render_api_set_json(db, "71779-1'; DROP TABLE lego_set;--")
        data = json.loads(json_result)

        self.assertEqual(data["error"], "Invalid set id")

    def test_render_api_set_json_uses_cache(self):
        first_db = MockDatabaseForApiSet()

        first_result = render_api_set_json(first_db, "71779-1")
        first_data = json.loads(first_result)

        self.assertEqual(len(first_db.queries), 2)
        self.assertEqual(first_data["set"]["id"], "71779-1")

        second_db = MockDatabaseInvalidShouldNotBeUsed()

        second_result = render_api_set_json(second_db, "71779-1")
        second_data = json.loads(second_result)

        self.assertEqual(second_data["set"]["id"], "71779-1")
        self.assertEqual(len(second_data["inventory"]), 2)


if __name__ == "__main__":
    unittest.main()