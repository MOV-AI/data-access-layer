from datetime import timedelta
from importlib.util import find_spec
from os import getenv, environ

from movai_core_shared.logger import Log
from movai_core_shared.core.secure import generate_secret_string
from movai_core_shared.envvars import (
    FLEET_NAME,
    DEFAULT_JWT_ACCESS_DELTA_SECS,
    DEFAULT_JWT_REFRESH_DELTA_DAYS,
)

from dal.classes.utils.secretkey import SecretKey


# JWT Authentication
if find_spec("movai-core-enterprise"):
    JWT_SECRET_KEY = SecretKey.get_secret(FLEET_NAME)
else:
    JWT_SECRET_KEY = getenv("JWT_SECRET_KEY", generate_secret_string(64))
    environ["JWT_SECRET_KEY"] = JWT_SECRET_KEY

JWT_ACCESS_EXPIRATION_DELTA = timedelta(seconds=DEFAULT_JWT_ACCESS_DELTA_SECS)
JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=DEFAULT_JWT_REFRESH_DELTA_DAYS)
