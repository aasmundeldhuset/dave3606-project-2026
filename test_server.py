# Test for get_sets_html function using a mock database
from server import get_sets_html

class MockDatabase:
    def execute_and_fetch_all(self, query):
        # Ensure correct SQL query is used
        assert query == "select id, name from lego_set order by id"
        # Return fake data instead of querying a real database
        return [
            ("1", "Test Set"),
            ("2", "Another Set")
        ]

    def close(self):
        pass


def test_get_sets_html():
    # Use mock database instead of real database
    db = MockDatabase()
    result = get_sets_html(db)

    # Check that expected data appears in generated HTML
    assert "Test Set" in result
    assert "Another Set" in result

# Test for API JSON generation
from server import get_api_set_json

def test_get_api_set_json():
    result = get_api_set_json("123")
    # Check that JSON contains correct set_id
    assert '"set_id": "123"' in result