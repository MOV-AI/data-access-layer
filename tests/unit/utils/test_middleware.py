"""Tests for the Middleware class."""
import asyncio
from aiohttp import test_utils
from aiohttp import web

from dal.utils.middleware import JWTMiddleware


class TestMiddleware:
    def test_middleware_invalid_token(self):
        """Test middleware with invalid token."""

        middleware = JWTMiddleware("test")
        middleware._safelist = []  # ensure route is not safe

        request = test_utils.make_mocked_request("GET", "/test", headers={"Host": "example.com"})

        async def handler(request):
            return web.Response(text="ok")

        async def run_test():
            await middleware.middleware(request, handler)

        try:
            asyncio.run(run_test())
        except web.HTTPUnauthorized:
            assert True
        else:
            assert False, "HTTPUnauthorized not raised"
