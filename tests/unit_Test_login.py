
import unittest
from unittest.case import TestCase
from unittest.mock import MagicMock, patch

import sys
import os

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to
# the sys.path.
sys.path.append(parent)

import app
from app import User, signup_post

INPUT = "INPUT"
EXPECTED_OUTPUT = "EXPECTED_OUTPUT"

class registerUser(unittest, TestCase):
    def setUp(self):
        self.success_test_params = [
            {
                INPUT: {"email", "username", "password"},
                EXPECTED_OUTPUT: {"email", "username", "password"}
            }
        ]
    def test_add_user_to_db(self):
        for test in self.success_test_params:
            self.asserEqual()