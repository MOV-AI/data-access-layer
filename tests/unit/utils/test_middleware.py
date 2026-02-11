"""Tests for the Middleware class."""
import asyncio
from aiohttp import test_utils
from aiohttp import web
import pytest

from dal.utils.middleware import JWTMiddleware


class TestMiddleware:
    def test_middleware_invalid_token(self):
        """Test middleware with invalid token."""

        middleware = JWTMiddleware("test")
        middleware._safelist = []  # ensure route is not safe

        request = test_utils.make_mocked_request("GET", "/test", headers={"Host": "example.com"})

        with pytest.raises(web.HTTPUnauthorized):
            asyncio.run(middleware.middleware(request, None))
