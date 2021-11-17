import unittest
from unittest.mock import patch
from app import (
    User,
    user_login_success,
    get_user_by_email,
    get_user_by_username,
    get_compound_name,
)


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.mock_db_user_entries = [
            User(email="test@test.com", username="test", password="hashed_test")
        ]

    def get_mocked_db_user_entries(self):
        return self.mock_db_user_entries

    def test_retrieve_user(self):
        # patch takes the path of the thing you want to change
        with patch(
            "app.User"
        ) as mocked_query:  # this line calls a patch function, assigns mocked_query as the name over the thing we're patching over (aka mocking a DB). We find a DB and call patch on it.
            # with is a context-manager in python - it means "have this condition be true for as long as we're in here"
            mocked_query = self.get_mocked_db_user_entries
            user = get_user_by_email("test@test.com")
            self.assertIsNotNone(user)

    def test_user_login_success_with_email(self):
        with patch("app.User") as mocked_query:
            mocked_query = self.get_mocked_db_user_entries
            user = get_user_by_email("test@test.com")
            password = "hashed_test"
            login_success = user_login_success(user, password)
            self.assertTrue(login_success)

    def test_user_login_success_with_username(self):
        # patch takes the path of the thing you want to change
        with patch("app.User") as mocked_query:
            mocked_query = self.get_mocked_db_user_entries
            user = get_user_by_username("test")
            self.assertIsNotNone(user)

    def test_get_compound_name(self):
        instrument_name = "Les Paul"
        instrument_type = "Guitar"
        compound_name = get_compound_name(instrument_name, instrument_type)
        self.assertEqual(compound_name, "Les Paul - Guitar")


if __name__ == "__main__":
    unittest.main()
