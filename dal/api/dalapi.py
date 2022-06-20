"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022

   main DAL api
"""
from .gitapi import GitManager, SlaveGitManager, MasterGitManager
from abc import ABC, abstractmethod
from dal import validation
from dal.classes.protocols import (
    ContextClientIn,
    ContextServerIn,
    ContextClientOut,
    ContextServerOut
)


class DAL(ABC):
    """Data Access Layer Main class API
    """

    @abstractmethod
    def __init__(self, user: str, schema_version: str) -> None:
        """initialize the DAL object and prepare the git managers with user
           and the schema folder which include schemas for the configuration

        Args:
            user (str): the username
            schema_folder (str): the local path of schemas to be used
                                 to validate the configuration files
        """
        self.manager: GitManager = None
        self.schema_types = None
        self.user = user
        self.schema_version = schema_version
        self.validator = validation.JsonValidator(schema_version)

    def validate(self, file_path: str) -> dict:
        """validate a local file path against it's matching schema

        Args:
            file_path (str): the local file path to be checked

        Returns:
            dict: a dictionary including a status about the validation
                  same as Schema.validate return value
                        - status: True if succeeded otherwise False
                        - message: error or success message
                        - path: the path of the error in case there is one
            """
        return self.validator.validate(file_path)

    def get(self, filename: str, remote: str, version: str,
            should_validate: bool = True) -> str:
        """will get a file from remote with required version number
           will perform schema validation on the file according to it's type

        Args:
            name (str): the name of the desired file
            remote (str): the remote repository to get file from
            version (str): the desired version of the requested file
            should_validate (bool): should we run validation on the file or not

        Returns:
            str: the local path of the requested file.
        """
        path = self.manager.get_file(filename, remote, version)
        if should_validate:
            self.validate(path)

        return path

    def commit(self,
               filename: str,
               remote: str,
               new_branch: str = None,
               base_branch: str = None,
               message: str = "") -> str:
        """will commit the specified file locally.

        Args:
            remote (str): the remote link of the repo.
            filename (str): the filename of the desired file.
            new_branch (str, optional): if given will create the new commit in
                                        a new branch with the name
                                        new_branch.
                                        Defaults to None.
            base_branch (str, optional): on what branch we want to be based in
                                         the new commit.
            message (str, optional): the commit message. Defaults to "".

        Returns:
            str: the newly committed commit hash id.
        """
        # get the current file, if no version specified will get the current
        # local path of the repo
        path = self.manager.get_file(filename, remote)
        validation = self.validate(path)
        if not validation["status"]:
            # validation FAILED, add log
            print(validation["message"])
            print(validation["path"])
            return ''
        return self.manager.commit_file(remote, filename, new_branch,
                                        base_branch, message)

    def push(self, repo_link: str, remote_alias: str = 'origin',
             tag_to_push: str = None, only_tag: bool = False):
        """pushed local repository changes remotely to remote name

        Args:
            remote (str): the remote link of repo
            remote_name (str, optional): remote name defined in repo locally.
                                         Defaults to 'origin'.
            tag_name (str, optional): the tag name we are interested to
                                      push remotely
            only_tag: (bool): push only newly created tag or push all of
                              other changes

        Returns:
            PushInfo: Carries information about the result of a push operation
                      of a single head
        """
        return self.manager.push(repo_link, remote_alias,
                                 tag_to_push, only_tag)

    def pull(self, repo_link: str, remote_alias: str = 'origin'):
        """Pull changes from remote, being the same as a fetch followed
           by a merge of branch with your local branch.

        Args:
            remote (str): the remote link of repo
            remote_name (str, optional): remote name defined in repo locally.
                                         Defaults to 'origin'.

        Returns:
            FetchInfo: see fetch method in GitPython
        """
        return self.manager.pull(repo_link, remote_alias)

    def diff(self, remote: str, filename: str) -> str:
        """[summary]

        Args:
            remote (str): [description]
            filename (str): [description]

        Returns:
            str: [description]
        """
        return self.manager.diff_file(remote, filename)

    def get_local_path(self, remote: str) -> str:
        """return the local path of a given remote repository

        Args:
            remote (str): the remote repository link.
        """
        return self.manager._get_local_path(remote)

    def create_file(self,
                    remote: str,
                    relative_path: str,
                    content: str,
                    base_version: str = None,
                    is_json: bool = True) -> None:
        self.manager.create_file(remote, relative_path, content,
                                 base_version, is_json)

    def release(self):
        pass

    def var(self):
        pass


class RedisProtocols:
    """organize all of Redis related Protocols
    """
    @staticmethod
    def context_client_in(callback: callable, params: dict,
                          **kwargs) -> ContextClientIn:
        return ContextClientIn(callback, params, **kwargs)

    @staticmethod
    def context_client_out(node_name: str,
                           params: dict) -> ContextClientOut:
        return ContextClientOut(node_name, params)

    @staticmethod
    def context_server_in(callback: callable, params: dict,
                          **kwargs) -> ContextServerIn:
        return ContextServerIn(callback, params, **kwargs)

    @staticmethod
    def context_server_out(node_name: str,
                           params: dict) -> ContextServerOut:
        return ContextServerOut(node_name, params)


class SlaveDAL(DAL):
    def __init__(self, user: str, schema_version: str = validation.default_version) -> None:
        super().__init__(user, schema_version)
        self.manager = SlaveGitManager(user)


class MasterDAL(DAL):
    def __init__(self, user: str, schema_version: str = validation.default_version) -> None:
        super().__init__(user, schema_version)
        self.manager = MasterGitManager(user)
