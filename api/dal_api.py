from .gitapi import SlaveGitManager, MasterGitManager
from classes.exceptions import SchemaTypeNotKnown, ValidationError
from abc import ABC, abstractmethod
import validation
from json import load as load_json
from os.path import realpath, dirname


class DAL(ABC):
    """Data Access Layer Main class API
    """
    schema_folder_path = dirname(realpath(validation.__file__)) + '/schemas'

    @abstractmethod
    def __init__(self, user: str, schema_folder: str) -> None:
        """initialize the DAL object and prepare the git managers with user
           and the schema folder which include schemas for the configuration

        Args:
            user (str): the username
            schema_folder (str): the local path of schemas to be used
                                 to validate the configuration files
        """
        self.manager = None
        self.schema_types = None
        self.user = user
        self.schema_folder = schema_folder
        self._init_schemas()

    def _init_schemas(self):
        """will initialize schemas objects in the schema folder
           for all of our configuration files
        """
        self.schema_types = ["node", "callback", "annotation", "layout",
                             "flow", "graphicscene"]
        for type in self.schema_types:
            schema_file = f'{self.schema_folder}/{type}.schema.json'
            schema_obj = validation.Schema(schema_file)
            setattr(self, f'{type}_schema', schema_obj)

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
        content = None
        with open(file_path) as f:
            content = load_json(f)
        type = (list(content.keys())[0]).lower()
        if type not in self.schema_types:
            raise SchemaTypeNotKnown(f"type: {type}")
        schema_obj: validation.Schema = getattr(self, f'{type}_schema')

        validation_res = schema_obj.validate(content)
        if validation_res["status"] is False:
            # validation Failed
            raise ValidationError(f"message:{validation_res['message']},\
                                path:{validation_res['path']}")
        return schema_obj.validate(content)

    def get(self, name: str, remote: str, version: str,
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
        path = self.manager.get_file(name, remote, version)
        if should_validate:
            self.validate(path)

        return path

    def commit(self,
               remote: str,
               filename: str,
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

    def push(self, remote: str, remote_name: str = 'origin',
             tag_name: str = None, only_tag: bool = False):
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
        return self.manager.push(remote, remote_name, tag_name, only_tag)

    def pull(self, remote: str, remote_name: str = 'origin'):
        """Pull changes from remote, being the same as a fetch followed
           by a merge of branch with your local branch.

        Args:
            remote (str): the remote link of repo
            remote_name (str, optional): remote name defined in repo locally.
                                         Defaults to 'origin'.

        Returns:
            FetchInfo: see fetch method in GitPython
        """
        return self.manager.pull(remote, remote_name)

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


class SlaveDAL(DAL):
    def __init__(self, user: str,
                 schema_folder: str = DAL.schema_folder_path) -> None:
        super().__init__(user, schema_folder)
        self.manager = SlaveGitManager(user)


class MasterDAL(DAL):
    def __init__(self, user: str,
                 schema_folder: str = DAL.schema_folder_path) -> None:
        super().__init__(user, schema_folder)
        self.manager = MasterGitManager
