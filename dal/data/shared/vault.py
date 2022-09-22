from datetime import timedelta

from movai_core_shared.envvars import (FLEET_NAME,
                                       DEFAULT_JWT_ACCESS_DELTA_SECS,
                                       DEFAULT_JWT_REFRESH_DELTA_DAYS)

from dal.classes.utils.secretkey import SecretKey

# JWT Authentication
JWT_SECRET_KEY = SecretKey.get_secret(FLEET_NAME)
JWT_ACCESS_EXPIRATION_DELTA = timedelta(seconds=DEFAULT_JWT_ACCESS_DELTA_SECS)
JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=DEFAULT_JWT_REFRESH_DELTA_DAYS)
