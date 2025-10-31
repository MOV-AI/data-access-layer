""" This file contains middleware functions to be used by aiohttp servers

Here's a summary of each of them:
  - JWTMiddleware: Used to authenticate users against the JWT token
  - save_node_type: Used to save the node type when a node is changed
  - remove_flow_exposed_port_links: Used to search and remove exposed ports links when a flow is deleted
  - redirect_not_found: Used to redirect 404 errors to the frontend
"""


from typing import List, Union, Optional
import urllib.parse
import asyncio
import re

from aiohttp import web
import requests
import bleach

from movai_core_shared.exceptions import InvalidToken, TokenExpired, TokenRevoked
from movai_core_shared.logger import Log

from dal.scopes.flow import Flow
from dal.scopes.node import Node
from dal.models.remoteuser import RemoteUser
from dal.models.internaluser import InternalUser

from dal.classes.utils.token import UserToken


LOGGER = Log.get_logger(__name__)


class JWTMiddleware:
    """JWT authentication middleware"""

    def __init__(self, secret: str, safelist: Optional[List[str]] = None):
        """Initialize middleware
        secret -> the JWT secret
        safelist -> an initial pattern list
        """
        self._secret = secret
        self._safelist = []
        if safelist is not None:
            self._safelist.extend(safelist)

    def add_safe(self, paths: Union[str, List[str]], prefix: Optional[str] = None) -> None:
        """Add paths to bypass auth list"""

        if isinstance(paths, str):
            paths = [paths]

        if prefix is None:
            prefix = ""

        prefix = prefix.rstrip("/")

        self._safelist.extend([prefix + path for path in paths])

    def _is_safe(self, request: web.Request) -> bool:
        q_string = request.query_string
        xss_check_dict = urllib.parse.parse_qs(q_string)
        for key, value in request.query.items():
            if key in xss_check_dict and value == bleach.clean(xss_check_dict[key][0]):
                xss_check_dict.pop(key)
            else:
                return False
        if q_string.encode("ascii", "ignore").decode() != q_string or len(xss_check_dict) > 0:
            # contains non-ascii chars
            return False
        if bleach.clean(str(request.headers["Host"])) != str(request.headers["Host"]):
            return False
        decoded_params = urllib.parse.unquote(q_string)
        if "<script>" in decoded_params:
            raise requests.exceptions.InvalidHeader("Risky URL params passed")
        if request.method == "OPTIONS":
            return True

        for pattern in self._safelist:
            if re.match(pattern, request.path) is not None:
                return True

        # else
        return False

    @web.middleware
    async def middleware(self, request, handler):
        """the actual middleware JWT authentication verify"""

        safe = self._is_safe(request)
        token_str = self._get_token_str(request, safe)

        if token_str is None and not safe:
            raise web.HTTPUnauthorized(reason="Missing authorization token")

        token_obj = self._verify_token(token_str, safe)

        if token_obj:
            self._set_user_in_request(request, token_obj)

        semaphore = asyncio.Semaphore(5)
        async with semaphore:
            return await handler(request)

    def _get_token_str(self, request, safe):
        token_str = None
        try:
            if "token" in request.query:
                token_str = request.query["token"]
            elif "Authorization" in request.headers:
                _, token_str = request.headers["Authorization"].strip().split(" ")
        except ValueError:
            if not safe:
                raise web.HTTPForbidden(reason="Invalid authorization header")
        return token_str

    def _verify_token(self, token_str, safe):
        token_obj = None
        try:
            if not safe:
                UserToken.verify_token(token_str)
                token_obj = UserToken.get_token_obj(token_str)
        except InvalidToken:
            raise web.HTTPForbidden(reason="Invalid authorization token")
        except TokenExpired as t:
            raise web.HTTPForbidden(reason=t)
        except TokenRevoked as t:
            raise web.HTTPForbidden(reason=t)
        return token_obj

    def _set_user_in_request(self, request, token_obj):
        try:
            if token_obj.user_type == "INTERNAL":
                request["user"] = InternalUser.get_user_by_name(
                    token_obj.domain_name, token_obj.account_name
                )
            elif token_obj.user_type == "LDAP":
                request["user"] = RemoteUser.get_user_by_name(
                    token_obj.domain_name, token_obj.account_name
                )
            else:
                error_msg = "Users's type is invalid."
                LOGGER.error(error_msg)
                raise InvalidToken(error_msg)
        except Exception as e:
            LOGGER.error(e)
            raise web.HTTPForbidden(reason=e.__str__())


@web.middleware
async def save_node_type(request, handler):
    """Saves the node type when a node is changed"""
    response = await handler(request)

    if request.method in ("POST", "PUT"):
        scope = request.match_info.get("scope")
        if scope == "Node":
            id_ = request.match_info.get("name")
            if id_:
                Node(id_).set_type()
            else:
                data = await request.json()
                label = data["data"].get("Label")
                # change to Node(label=label).set_type()
                Node(label).set_type()

    return response


@web.middleware
async def remove_flow_exposed_port_links(request, handler):
    """Search end remove ExposedPort links"""

    scope = request.match_info.get("scope")

    if scope != "Flow":
        # Wait for the request to resolve
        response = await handler(request)
    else:
        flow_obj = None
        old_flow_exposed_ports = {}

        if request.match_info.get("name"):
            try:
                flow_obj = Flow(name=request.match_info.get("name"))
                old_flow_exposed_ports = {**flow_obj.ExposedPorts}
            except Exception as e:
                LOGGER.warning(
                    f"caught exception while getting Flow \
                               {request.match_info.get('name')}, \
                               exception: {e}"
                )

        # Wait for the request to resolve
        response = await handler(request)

        if request.method in ("POST", "PUT", "DELETE"):
            if flow_obj:
                # Check if ExposedPort was deleted
                deleted_exposed_ports = Flow.exposed_ports_diff(
                    old_flow_exposed_ports, flow_obj.ExposedPorts
                )

                LOGGER.info(f"Deleted exposed ports result: {deleted_exposed_ports}")

                # Loop trough all deleted ports and delete Links associated to that exposed port
                for node in deleted_exposed_ports:
                    for deleted_exposed_port in node.values():
                        node_inst_name = next(iter(deleted_exposed_port))
                        for port in deleted_exposed_port[node_inst_name]:
                            match = re.search(r"^.+/", port)
                            if match:
                                port_name = match[0][:-1]
                                flow_obj.delete_exposed_port_links(node_inst_name, port_name)
                            else:
                                LOGGER.warning("Invalid port name format: %s", port)

            if request.get("scope_delete"):
                # Flow was deleted
                Flow.on_flow_delete(request.match_info.get("name"))

    return response


@web.middleware
async def redirect_not_found(request, handler):
    response = await handler(request)

    if not isinstance(response, web.Response):
        LOGGER.warning("Response is not web.Response instance, but of type: %s", type(response))
        return web.Response(
            status=500, text="Internal Server Error", headers={"Server": "Movai-server"}
        )

    if response.status != 404:
        return response
    message = response.message
    return web.json_response({"error": message}, headers={"Server": "Movai-server"})
