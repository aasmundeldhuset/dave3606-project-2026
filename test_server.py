import unittest
from server import get_all_sets_html, get_set_html, get_set_json

class MockDatabase:
    def execute_and_fetch_all(self, query, params=None):
        if "FROM lego_set ORDER BY id" in query:
            return [("1234-1", "Mock Set 1"), ("5678-1", "Mock Set 2")]
        elif "FROM lego_set WHERE id =" in query:
            if params[0] == "1234-1":
                return [("1234-1", "Mock Set 1", 2023, "Star Wars")]
            return []
        elif "FROM lego_inventory WHERE set_id =" in query:
            if params[0] == "1234-1":
                return [("3001", 1, 10), ("3002", 2, 5)]
            return []
        return []

class TestServer(unittest.TestCase):
    def setUp(self):
        self.db = MockDatabase()
    
    def test_get_all_sets_html(self):
        html_output = get_all_sets_html(self.db)
        self.assertIn("1234-1", html_output)
        self.assertIn("Mock Set 1", html_output)
        self.assertIn("5678-1", html_output)

    def test_get_set_html(self):
        html_output = get_set_html(self.db, "1234-1")
        self.assertIn('<html lang="en">', html_output)

    def test_get_set_json(self):
        json_output = get_set_json(self.db, "1234-1")
        self.assertIn('"id": "1234-1"', json_output)
        self.assertIn('"brick_type_id": "3001"', json_output)
        self.assertIn('"count": 10', json_output)

    def test_get_set_json_not_found(self):
        json_output = get_set_json(self.db, "9999-1")
        self.assertIn('"error": "Set not found"', json_output)


if __name__ == "__main__":
    unittest.main()