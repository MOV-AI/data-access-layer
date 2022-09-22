"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
import asyncio
import os
from aiohttp import ClientSession
from aiohttp.client import ContentTypeError, ClientConnectorError
from yarl import URL

CHUNK_SIZE = 4 * 1024  # 4 KB


class RemoteArchiveAsync:
    """
    This class implements a remote archive client
    It's used for the command line tool and also for
    the filesystem to fetch missing data
    """

    def __init__(self, remote_uri: URL, user: str, password: str):
        self._remote_uri = remote_uri
        self._user = user
        self._password = password
        self._access_token = None

    def _make_url(self, path: str) -> URL:
        return self._remote_uri / path

    async def _authenticate(self):
        """
        Authenticate against the server
        """
        async with ClientSession() as session:
            async with session.post(self._make_url("token-auth/"), json={
                "username": self._user,
                "password": self._password
            }) as response:

                body = await response.json()
                self._access_token = body["access_token"]

    async def list_scopes(self, workspace_id: str):
        """
        List scopes in a workspace
        """
        try:
            await self._authenticate()
            async with ClientSession(headers={"Authorization": f"Bearer {self._access_token}"}) as session:
                async with session.get(self._make_url(f"api/v2/db/{workspace_id}")) as response:
                    return await response.json()
        except (ContentTypeError, ClientConnectorError):
            return {}

    async def list_workspaces(self):
        """
        List available workspaces
        """
        try:
            await self._authenticate()
            async with ClientSession(headers={"Authorization": f"Bearer {self._access_token}"}) as session:
                async with session.get(self._make_url("api/v2/db")) as response:
                    return await response.json()
        except (ContentTypeError, ClientConnectorError):
            return {}

    async def get_scope(self, path: str):
        """
        List available workspaces
        """
        try:
            await self._authenticate()
            async with ClientSession(headers={"Authorization": f"Bearer {self._access_token}"}) as session:
                async with session.get(self._make_url(f"api/v2/db/{path}")) as response:
                    return await response.json()
        except (ContentTypeError, ClientConnectorError):
            return {}

    async def backup(self, objs: object, destination: str):
        """
        Download a scope
        """
        try:
            await self._authenticate()
            async with ClientSession(headers={"Authorization": f"Bearer {self._access_token}"}) as session:

                # First we create the backup job with the scope
                # we want to download
                async with session.post(self._make_url("api/v2/db/backup"), json={
                    "metadata": {},
                    "manifest": objs if isinstance(objs, list) else [str(objs)]
                }) as response:

                    job = await response.json()

                # get the id of the backup job and current state
                try:
                    job_id = job["id"]
                    current_state = job["state"]["state"]
                except KeyError:
                    return False

                # we wait until the job is finished
                while current_state != "finished":
                    async with session.get(self._make_url(f"api/v2/db/backup/{job_id}")) as response:
                        job_info = await response.json()
                        try:
                            current_state = job_info["state"]["state"]
                        except KeyError:
                            return False

                # Download the backup file to a temporary folder
                try:
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                except PermissionError:
                    return False
                except FileNotFoundError:
                    pass

                async with session.get(self._make_url(f"api/v2/db/backup/{job_id}/archive")) as response:
                    # Read the content from the request
                    with open(destination, 'wb') as backup_fp:
                        while True:
                            chunk = await response.content.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            backup_fp.write(chunk)

                return True

        except (ContentTypeError, ClientConnectorError):
            return False

    async def restore(self, source: str):
        """
        Upload a restore file to the server
        """
        try:

            if not os.path.exists(source):
                return False

            await self._authenticate()
            async with ClientSession(headers={"Authorization": f"Bearer {self._access_token}"}) as session:

                # We open the restore file and upload it to the server
                with open(source, "rb") as restore_fp:
                    async with session.post(self._make_url("api/v2/db/restore"), data=restore_fp) as response:
                        job = await response.json()

                # get the id of the backup job and current state
                try:
                    job_id = job["id"]
                    current_state = job["state"]["state"]
                except KeyError:
                    return False

                # we wait until the job is finished
                while current_state != "finished":
                    async with session.get(self._make_url(f"api/v2/db/restore/{job_id}")) as response:
                        job_info = await response.json()
                        try:
                            current_state = job_info["state"]["state"]
                        except KeyError:
                            return False

                return True

        except (ContentTypeError, ClientConnectorError):
            return False


class RemoteArchive:
    """
    A helper class that encapsulates the async code
    """

    def __init__(self, remote_uri: str, user: str, password: str):
        self._async_client = RemoteArchiveAsync(
            URL(remote_uri), user, password)
        self._loop = asyncio.get_event_loop()

    def list_scopes(self, workspace_id: str):
        """
        Get a list of all scopes in a workspace
        """
        return self._loop.run_until_complete(self._async_client.list_scopes(workspace_id))

    def list_workspaces(self):
        """
        Get a list of all workspaces
        """
        return self._loop.run_until_complete(self._async_client.list_workspaces())

    def get_scope(self, path: str):
        """
        Get a scope
        """
        return self._loop.run_until_complete(self._async_client.get_scope(path))

    def backup(self, objs: object, dst: str):
        """
        Backup scopes and dependencies
        objs - a list of the objects to backup
        """
        return self._loop.run_until_complete(self._async_client.backup(objs, dst))

    def restore(self, source: str):
        """
        Restore scopes
        source - the restore file
        """
        return self._loop.run_until_complete(self._async_client.restore(source))
