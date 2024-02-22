import sys

from movai_core_shared.core.secure import generate_secret_string

import dal.classes.utils.secretkey

def mock_secretkey():
    """ Replaces the function that calls out to Redis with a mock """

    dal.classes.utils.secretkey.SecretKey.get_secret = lambda fleet_name: generate_secret_string(64)


mock_secretkey()