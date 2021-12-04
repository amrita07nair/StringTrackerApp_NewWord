import unittest
from unittest.mock import patch
from app import (
    User,
    Instruments,
    user_login_success,
    get_user_by_email,
    get_user_by_username,
    getCompoundName,
    getCurrentInstrument,
    validate_new_instr_form,
)


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.mock_db_user_entries = [
            User(
                email="test@test.com",
                username="test",
                password="hashed_test",
            )
        ]

        self.mock_db_instrument_entries = [
            Instruments(
                compound_name="Les Paul - Guitar",
                instr_name="Les Paul",
                instr_type="Guitar",
            )
        ]

    def get_mocked_db_instrument_entries(self):
        return self.mock_db_instrument_entries

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
        compound_name = getCompoundName(instrument_name, instrument_type)
        self.assertEqual(compound_name, "Les Paul - Guitar")

    def test_get_current_instr_name(self):
        with patch("app.User") as mocked_user_query:
            mocked_user_query = self.get_mocked_db_user_entries
            with patch("app.Instruments") as mocked_instr_query:
                mocked_instr_query = self.get_mocked_db_instrument_entries
                current_instr = getCurrentInstrument("Les Paul")
                current_instr_name = current_instr.instr_name
                self.assertIsNotNone(current_instr_name)

    def test_validate_new_instr_form(self):
        is_valid = validate_new_instr_form("", "Guitar")
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()
