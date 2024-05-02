"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Erez Zomer  (erez@mov.ai) - 2022
"""

from socket import gethostname
import uuid
import jwt
from datetime import timedelta

from movai_core_shared.logger import Log
from movai_core_shared.common.time import current_timestamp_int, delta_time_int

from movai_core_shared.exceptions import (
    InvalidToken,
    TokenError,
    TokenExpired,
    TokenRevoked,
    UserError,
)

from dal.movaidb import MovaiDB
from dal.models.baseuser import BaseUser

from dal.data.shared.vault import (
    JWT_SECRET_KEY,
    JWT_ACCESS_EXPIRATION_DELTA,
    JWT_REFRESH_EXPIRATION_DELTA,
)


class TokenObject:
    """An object for refercing token info with object attributes."""

    def __init__(self, token: dict) -> None:
        """Initializes the object.

        Args:
            token (dict): a dictionary with the token info.

        Raises:
            InvalidToken: In case there are missing keys.
        """
        try:
            self.subject = token["sub"]
            self.issuer = token["iss"]
            self.issue_time = token["iat"]
            self.expiration_time = token["exp"]
            self.jwt_id = token["jti"]
            if "refresh_id" in token:
                self.refresh_id = token["refresh_id"]
        except KeyError:
            error_msg = f"Token has missing key"
            raise InvalidToken(error_msg)


class UserTokenObject(TokenObject):
    """Extends the Token object with more attributes relating to user tokens."""

    def __init__(self, token: dict) -> None:
        """Initializes the object.

        Args:
            token (dict): A dictionary with the user token info.
        """
        super().__init__(token)
        self.account_name = token["account_name"]
        self.domain_name = token["domain_name"]
        self.common_name = token["common_name"]
        self.user_type = token["user_type"]
        self.roles = token["roles"]
        self.email = token["email"]
        self.super_user = token["super_user"]
        self.read_only = token["read_only"]
        self.send_report = token["send_report"]


class DBToken(dict):
    def __init__(self, token: TokenObject, token_type: str = "Token"):
        super().__init__()
        self[token_type] = {token.jwt_id: {"ExpirationTime": token.expiration_time}}


class EmptyDBToken(dict):
    def __init__(self, token_id: str = None, token_type: str = "Token"):
        super().__init__()
        if token_id is None:
            self[token_type] = {"*": {"ExpirationTime": ""}}
        else:
            self[token_type] = {token_id: {"ExpirationTime": ""}}


class TokenManager:
    """A general class for managing tokens in DB."""

    log = Log.get_logger("TokenManger")
    _db = None
    token_type = "Token"

    @classmethod
    @property
    def db(cls):
        if cls._db is None:
            cls._db = MovaiDB(db="local")
        return cls._db

    @classmethod
    def is_token_exist(cls, token_id: str) -> bool:
        """Checks whether a specific token exist in the DB.

        Args:
            token (TokenObject): The token to look for.

        Returns:
            bool: True if exist, False otherwise.
        """
        result = cls.db.get(EmptyDBToken(token_id))
        return len(result.keys()) > 0

    @classmethod
    def remove_token(cls, token_id: str) -> None:
        """Removes token scheme from DB by the Token id.

        Args:
            token (TokenObject): The token to remove.
        """
        if cls.is_token_exist(token_id):
            cls.db.delete(EmptyDBToken(token_id))
            cls.log.debug(f"The token id {token_id} has been removed from the allowed token list.")

    @classmethod
    def store_token(cls, token: TokenObject) -> None:
        """Stors a token in the DB.

        Args:
            token (TokenObject): The token to store.
        """
        cls.db.set(DBToken(token))
        cls.log.debug(f"The token id {token.jwt_id} has been added to the allowed token list.")

    @classmethod
    def remove_all_tokens(cls):
        """Removes all token from db."""
        cls.log.info(f"Removing all tokens from token list.")
        tokens = cls.db.get(EmptyDBToken(None, cls.token_type))
        tokens = tokens.get(cls.token_type)
        if tokens is not None:
            for token_id in tokens.keys():
                cls.remove_token(token_id)

    @classmethod
    async def remove_all_expired_tokens(cls):
        """Removes all the tokens that their expiration
        time has passed.
        """
        cls.log.info(f"Removing all expired tokens.")
        tokens = cls.db.get(EmptyDBToken(None, cls.token_type))
        tokens = tokens.get(cls.token_type)
        current_time = current_timestamp_int()
        if tokens is not None:
            for token_id, token_data in tokens.items():
                if token_data["ExpirationTime"] < current_time:
                    cls.remove_token(token_id)


class Token:
    allowed_algorithms = ["HS256", "RS256", "ES256"]
    required_keys = set(["sub", "iss", "iat", "exp", "jti"])
    log = Log.get_logger("Token")
    _token_manager = TokenManager
    _issuer = gethostname()

    @classmethod
    def get_token_id(cls, token: str):
        return TokenObject(cls.decode_no_verify_token(token)).jwt_id

    @classmethod
    def init_payload(cls, subject: str, expiration_delta: timedelta) -> dict:
        """initializes a dictionary which will be used as a payload
        for token (JWT) generation.

        Args:
            subject (str): The subject of the token ('Access', 'Refresh')
            expiration_delta (timedelta): the time delta from now.
        
        Returns:
            (dict): the payload of the token.
        """
        cls.log.debug(f"Initializing token payload.")
        payload = {}
        payload["sub"] = subject
        payload["iss"] = cls._issuer
        payload["iat"] = current_timestamp_int()
        payload["exp"] = delta_time_int(expiration_delta)
        payload["jti"] = str(uuid.uuid4())
        return payload

    @classmethod
    def decode_and_verify_token(cls, token: str, secret_key=JWT_SECRET_KEY) -> dict:
        """This function verifies and decodes the token, the decoded token
        is returned in a dictionary with meaninigfull keys. if verification fails
        an Exception would be returned.

        Args:
            token (str): a string representing the token (encoded JWT).
            secret_key (str): The key used to encrypt the data. Defaults
                to JWT_SECRET_KEY.

        Raises:
            wt.exceptions.InvalidTokenError: In case token verification fails.

        Returns:
            dict: a dicitionary with all the token's payload info.
        """
        #cls.log.debug(f"Decoding and verifying token.")
        options = {}
        options["require"] = cls.required_keys
        options["verify_iss"] = True
        token_payload = jwt.decode(jwt=token, key=secret_key, algorithms=cls.allowed_algorithms, options=options)
        return token_payload

    @classmethod
    def decode_no_verify_token(cls, token: str, secret_key=JWT_SECRET_KEY) -> dict:
        """This function decodes the token withoud verifying it, the decoded token
        is returned in a dictionary with meaninigfull keys.

        Args:
            token (str): a string representing the token (encoded JWT).
            secret_key (str): The key used to verify token signature. Defaults
                to JWT_SECRET_KEY.

        Returns:
            dict: A dicitionary with all the token's payload info.
        """
        #cls.log.debug(f"Decoding token without verification.")
        return jwt.decode(
            jwt=token, key=secret_key, verify=False, algorithms=cls.allowed_algorithms
        )

    @classmethod
    def encode_token(cls, token_payload: dict, secret_key: str = JWT_SECRET_KEY, algorithm: str = "HS256") -> str:
        """This function generates Json Web Token (JWT) that will use the
        client to access system resources.

        Args:
            token_payload (dict): A dictionary containing the payload values.
            secret_key (str): The key used to sign token signature. Defaults
                to JWT_SECRET_KEY.
            algorithm (str, optional): The signing algorithm to use. Defaults to 'HS256'.

        Raises:
            TokenError: In case the requested algorithm is not found on the allowed algorithms set.
            TokenError: In case the one of the required keys is not found in the token.

        Returns:
            str: The encoded token.
        """
        if algorithm not in cls.allowed_algorithms:
            error_msg = f"The algorithm {algorithm} is not allowed for encoding tokens."
            raise TokenError(error_msg)

        for key in Token.required_keys:
           if key not in token_payload.keys():
               error_msg = f"The key: \"{key}\" is missing from payload dictionary."
               raise TokenError(error_msg)
        cls.log.debug(f"Encoding token using {algorithm} algorithm.")
        token_str = jwt.encode(payload=token_payload, key=secret_key, algorithm=algorithm).decode("utf-8")
        return token_str

    @classmethod
    def verify_token(cls, token: str) -> None:
        """verifies the token validity

        Args:
            token (str): The string representation of the token.

        Raises:
            TokenRevoked: In case the token was revoked from the DB.
            TokenExpired: In case the token expiration time has expired.
            InvalidToken: In case there is decode error
            InvalidToken: In case the token is invalid.
        """
        if not isinstance(token, str):
            error_msg = "Token must be a string!"
            raise TokenError(error_msg)
        try:
            token_id = cls.get_token_id(token)
            #cls.log.debug(f"Verifying token id {token_id}")
            cls.decode_and_verify_token(token)
            if not cls._token_manager.is_token_exist(token_id):
                error_msg = "Token have been revoked, please login again."
                raise TokenRevoked(error_msg)
        except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError)  as e:
            error_msg = f"Failed to verify token: {e}"
            cls.log.warning(error_msg)
            cls._token_manager.remove_token(token_id)
            raise TokenExpired(error_msg)

    @classmethod
    def get_token_obj(cls, token: str) -> TokenObject:
        """Extracts the token and returns a TokenObject.
        Args:
            token (str): the token to extract.

        Returns:
            TokenObject: The token info wrapped in an object.
        """
        return TokenObject(cls.decode_no_verify_token(token))

    @classmethod
    def revoke_token(cls, token: str) -> None:
        """Removes the token id from the allowed token list.
        If the token has a refresh_id token it will remove the refresh_id token as well.

        Args:
            token (str): The token to revoke.
        """
        token_obj = cls.get_token_obj(token)
        cls._token_manager.remove_token(token_obj.jwt_id)
        cls._token_manager.remove_token(token_obj.refresh_id)


class UserToken(Token):
    @classmethod
    def init_payload(cls, user: BaseUser, subject: str, expiration_delta: timedelta, refresh_id: str) -> None:
        """initializes a dictionary which will be used as a payload
        for token (JWT) generation.

        Args:
            user: (BaseUser): The user to for whom the token will be generated.
            expiration_delta (timedelta): the time delta from now.
            refresh_id (str): An id of the assciated refresh token.
        
        Returns:
            (dict): The dictionary to use as a payload when encoding the token.
        """
        payload = super().init_payload(subject, expiration_delta)
        payload["refresh_id"] = refresh_id
        payload["domain_name"] = user.domain_name
        payload["account_name"] = user.account_name
        payload["common_name"] = user.common_name
        payload["user_type"] = user.user_type
        payload["roles"] = user.Roles
        payload["email"] = user.email
        payload["super_user"] = user.super_user
        payload["read_only"] = user.read_only
        payload["send_report"] = user.send_report
        return payload

    @classmethod
    def get_token_obj(cls, token: str) -> UserTokenObject:
        """Extracts the token and returns a UserTokenObject.

        Args:
            token (str): the token to extract.

        Returns:
            UserTokenObject: The token info wrapped in an object.
        """
        return UserTokenObject(cls.decode_no_verify_token(token))

    @classmethod
    def get_refresh_id(cls, token: str) -> str:
        """Returns the refresh_id of the token if exist.

        Args:
            token (str): The token where refresh_id is specified.

        Returns:
            str: The refresh_id if exists, None otherwise.
        """
        token_obj = cls.get_token_obj(token)
        if "" == token_obj.refresh_id:
            return None
        return token_obj.refresh_id
            
            
    @classmethod
    def _generate_user_token(
        cls, user: BaseUser, subject: str, time_delta: timedelta, refresh_id: str = ""
    ) -> str:
        """This function encapsulates the generate_token function to
        generate the access token.
        
        Args:
            user (BaseUser): The user for whom the token is generated.
            subect (str): The subject of the token ('Access', 'Refresh').
            time_delta (timedelta): The time difference between issue time to
                expiration time.
            refresh_id (str): The id of the associated refresh token. Defaults to
                empty string.

        Returns:
            str: The generated token decoded in utf-8.
        """
        if not isinstance(user, BaseUser):
            error_msg = f"The user argument is from unknown type."
            raise UserError(error_msg)
        token_payload = cls.init_payload(user, subject, time_delta, refresh_id)
        token_str = cls.encode_token(token_payload)
        cls._token_manager.store_token(UserTokenObject(token_payload))
        return token_str

    @classmethod
    def generate_access_token(cls, user: BaseUser, refresh_id) -> str:
        """This function encapsulates the generate_token function to
        generate the access token.

        Args:
            user (BaseUser): The user for whom the token is generated.
            refresh_id (str): The id of the associated refresh token. Defaults to
                empty string.

        Returns:
            str: The generated token decoded in utf-8.
        """
        return cls._generate_user_token(user, "Access", JWT_ACCESS_EXPIRATION_DELTA, refresh_id)

    @classmethod
    def generate_refresh_token(cls, user: BaseUser) -> str:
        """This function encapsulates the generate_token function to
        generate the refresh token.

        Args:
            user (BaseUser): The user for whom the token is generated.

        Returns:
            str: The generated token decoded in utf-8.
        """
        return cls._generate_user_token(user, "Refresh", JWT_REFRESH_EXPIRATION_DELTA)

 