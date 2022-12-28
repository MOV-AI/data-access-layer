"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022

   API for the git part
"""

from abc import abstractmethod
from os import getenv
from re import search
from os.path import join as path_join
from os.path import expanduser
from pathlib import Path
from git import (Repo,
                 InvalidGitRepositoryError,
                 GitError,
                 GitCommandError)
from git.index import IndexFile
from git.refs import HEAD
from git.refs.tag import TagReference
from git.remote import PushInfo
from dal.exceptions import (NoChangesToCommit,
                            SlaveManagerCannotChange,
                            TagAlreadyExist,
                            VersionDoesNotExist,
                            BranchAlreadyExist,
                            GitUserErr,
                            FileDoesNotExist,
                            RepositoryDoesNotExist,
                            GitPermissionErr)
from dal.classes.filesystem import FileSystem
from dal.classes.common.gitlink import GitLink
from dal.archive.basearchive import BaseArchive


MOVAI_FOLDER_NAME = ".movai"
MOVAI_BASE_FOLDER = path_join(FileSystem.get_home_folder(), MOVAI_FOLDER_NAME)
MOVAI_BASE_FOLDER = getenv("MOVAI_USERSPACE", MOVAI_BASE_FOLDER)
GIT_BASE_FOLDER = path_join(MOVAI_BASE_FOLDER, 'database', 'git')


class GitRepo:
    """ class representing single repository"""

    def __init__(self, remote: str, username: str,
                 local_path: str, version: str):
        """initialze new repository.
           creates local folder and clone the repo with the path
           /repo_name/branch/commit

        Args:
            remote (str): remote link of repository.
            username (str): username to be used.
            version (str, optional): branch/tag/commit id.
        """
        self._git_link = GitLink(remote)
        self._username = username
        self._version = version
        self._versions = []
        self._branches = []
        self._manifest = {}
        self._repo_object = None
        self._default_branch = None
        self._local_path = local_path
        FileSystem.create_folder_recursively(self._local_path)
        self._repo_object = self._clone()
        self._update_versions()

    def version_exist(self, revision: str) -> bool:
        """check if version (commit / tag) exist in the repo

        Args:
            revision (str): the version need to be checked

        Returns:
            bool: True if exist otherwise fasle.
        """
        try:
            self._repo_object.git.rev_parse(revision)
        except GitCommandError as e:
            if e.stderr.find(
                    "unknown revision or path not in the working tree"):
                return False
        return True

    def prev_version(self) -> str:
        return self._repo_object.rev_parse("HEAD~1")

    @property
    def local_path(self) -> str:
        """local path of the repository

        Returns:
            str: local path of the repo.
        """
        return self._local_path

    @property
    def default_branch(self) -> str:
        """the default branch in the remote repository

        Returns:
            str: default branch string.
        """
        return self._default_branch

    @property
    def name(self) -> str:
        """the reposiotry name

        Returns:
            str: repository name.
        """
        return self._git_link.repo

    @property
    def branch(self) -> str:
        """current branch of the repository

        Returns:
            str: branch name
        """
        if self._repo_object.head.is_detached:
            raise Exception("detached HEAD state, no branch")
        return str(self._repo_object.active_branch)

    @property
    def commit_sha(self) -> str:
        """current commit sha1 id of the repository

        Returns:
            str: commit sha1 id.
        """
        return str(self._repo_object.commit())

    @property
    def git_client(self) -> Repo.git:
        """returns the git client in the repository
           used mainly for direct command lines

        Returns:
            Repo.git: git client object
        """
        return self._repo_object.git

    @property
    def head(self) -> 'HEAD':
        """will return HEAD object of the current repo

        Returns:
            HEAD: the HEAD object of the current repo tree
        """
        return self._repo_object.head

    @property
    def index(self) -> 'IndexFile':
        """will return IndexFile of the current working tree

        Returns:
            IndexFile: the IndexFile of the current working tree.
        """
        return self._repo_object.index

    def fetch(self):
        """run fetch on the local repository
        """
        self._repo_object.git.fetch()

    def commit(self,
               filename: str = None,
               new_branch: str = None,
               message: str = None) -> str:
        """will commit file changes to current branch in case it's not
           detached HEAD, or create new branch if specified
           in case it's new file it will be added.

        Args:
            filename (str, optional): desired filename. Defaults to None.
            new_branch (str, optional): the new branch name to be created.
                                    Defaults to None.
            message (str, optional): message for the commit. Defaults to None.

        Raises:
            Exception: in case it's detached HEAD and no branch specified

        Returns:
            str: the newly committed commit sha
        """
        if self._repo_object.head.is_detached \
           and new_branch is None:
            # TODO: maybe we should commit either way and warn the user
            # that this commit might be lost because it's on a detached head
            raise Exception("detached HEAD and no branch specified")
        self._repo_object.git.add(filename)
        if new_branch is not None:
            try:
                self.checkout(new_branch)
                raise BranchAlreadyExist(f"branch {new_branch} already exist")
            except VersionDoesNotExist:
                self._repo_object.create_head(new_branch)
                self.checkout(new_branch)
        self._repo_object.git.commit(m=message)
        return self.commit_sha

    def tag(self, version, tag_name: str, msg: str = None) -> TagReference:
        """will create a tag based on a version

        Args:
            version ([type]): [description]
            tag_name (str): [description]
            msg (str, optional): [description]. Defaults to None.

        Returns:
            TagReference: [description]
        """
        self.checkout(version)
        new_tag = self._repo_object.create_tag(tag_name, message=msg)

        return new_tag

    def checkout_file(self, file_name: str) -> str:
        """will checkout file of the repository commit hash
           and returns it's local path in case does not exist,
           otherwise no checkout will be running

        Args:
            file_name (str): the desired file name

        Returns:
            str: local path of the requested file
        """
        file_path = path_join(self._local_path, file_name)
        try:
            self._repo_object.git.checkout(file_name)
        except GitCommandError:
            raise FileDoesNotExist(f"file/path {file_name} does not exist")
        return file_path

    def get_latest_commit(self) -> str:
        """get the latest commit sha1 hash in repository
           on current branch

        Returns:
            str: commit sha1 hash
        """
        remote_alias = str(self._repo_object.remote())
        commits_log = self._repo_object.git.log(
                                    f"{remote_alias}/{self._branch}",
                                    "--oneline")
        commit = commits_log.split('\n')[0].split(' ')[0]
        return self._repo_object.git.rev_parse(commit)

    def branch_exist(self, branch: str, fetch: bool = False) -> bool:
        if fetch:
            self.fetch()
        for ref in self._repo_object.references:
            if branch == ref.name:
                return True
        return False

    def tag_exist(self, tag: str, fetch: bool = False) -> bool:
        if fetch:
            self.fetch()
        for _tag in self._repo_object.tags:
            if str(_tag) == tag:
                return True
        return False

    def checkout(self, version):
        """will checkout and change version

        Args:
            version ([type]): the desired version

        Raises:
            VersionDoesNotExist: in case the branch does exist in repo.
        """

        try:
            self._repo_object.git.checkout(version)
        except GitCommandError as e:
            if e.stderr.find("Your local changes to the following files \
                              would be overwritten by checkout") != -1:
                # TODO add log
                self._repo_object.git.stash()
                self._repo_object.git.checkout(version)
                self._repo_object.git.pop()
            elif e.stderr.find("did not match any file") != -1:
                raise VersionDoesNotExist(f"version {version} does not exist")

    def _clone(self, no_checkout=False, shallow=False) -> Repo:
        """clone given branch, commit, tag.

        Args:
            no_checkout (bool): if set, no checkout will be done (empty folder)
                                without actual files, only .git folder that has
                                all of the information about the repo.
            shallow (bool): if set, a shallow clone will be done without cloning
                            the whole git tree, regular clone will be done if not
                            set.

        Returns:
            git.Repo: Repo object.

        Raises:
            RepositoryDoesNotExist: in case remote repository does not exist
        """
        repo = None
        FileSystem.create_folder_recursively(self._local_path)
        # TODO: change in the future and use permission class.
        if not FileSystem.is_exist(expanduser('~/.ssh/id_rsa')):
            raise FileDoesNotExist(expanduser('~/.ssh/id_rsa'))
        try:
            repo = Repo(self._local_path)
        except InvalidGitRepositoryError:
            # local Repository does not exist, creating one.
            git_ssh_cmd = f"ssh -i {expanduser('~/.ssh/id_rsa')}"
            try:
                args = {
                    "env": dict(GIT_SSH_COMMAND=git_ssh_cmd),
                    "no_checkout": no_checkout
                }
                if shallow:
                    args.update({"depth": 1})
                    # args["filter"] = ["tree:0", "blob:none"]

                repo = Repo.clone_from(self._git_link.repo_ssh_link,
                                       self._local_path,
                                       **args)
            except GitCommandError as e:
                FileSystem.delete(self._local_path)
                raise RepositoryDoesNotExist(f"repository {self._git_link.owner}/{self._git_link.repo} does not exist, {e.stderr}")
            self._default_branch = repo.active_branch.name
        except GitError as e:
            print(f"Error {e}")

        return repo

    def get_modified_files(self) -> list:
        """return a list containing modified file names.

        Returns:
            list: list of file names
        """
        file_names = []
        for diff in self._repo_object.head.commit.diff(None).iter_change_type('M'):
            file_names.append(diff.a_path)
        return file_names

    def get_untracked_files(self) -> list:
        """return a list containing newly added file names.

        Returns:
            list: list of file names
        """
        # Gitpython 0.2 or above needed for the untracked_files to work
        return self._repo_object.untracked_files

    def diff_file(self, filename: str) -> str:
        return self._repo_object.git.diff(filename)

    def push(self, remote_name: str, tag_name: str,
             only_tag: bool) -> PushInfo:
        remote = self._repo_object.remote(remote_name)
        if only_tag:
            return remote.push(tag_name)
        remote.push(tag_name)
        return remote.push()

    def pull(self, branch_name: str):
        self.checkout(branch_name)
        try:
            ret = self._repo_object.git.pull("origin", branch_name)
        except GitCommandError as e:
            if "Permission denied" in e.stderr:
                raise GitPermissionErr(e.stderr)
        self._update_versions()
        return ret

    def _update_versions(self) -> None:
        self._versions = sorted(self._repo_object.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
        self._branches = [ref.name for ref in self._repo_object.remote().refs]

    def list_versions(self, is_branches: bool) -> list:
        """
        return a list of tags in repository sorted by commit date
        """
        if is_branches:
            return self._branches
        return self._versions

    def list_models(self) -> dict:
        """read the manifest.txt file and return it's content in a dict

        Returns:
            dict: keys are types of models (Flow/Node/Callback/...), value
                  is a list including the ids of the Flows/Nodes/...
        """
        manifest_path = path_join(self.local_path, "manifest.txt")
        if not FileSystem.is_exist(manifest_path):
            raise FileDoesNotExist("manifest.txt file does not exit in repo")
        content = FileSystem.read(manifest_path)
        models = {}
        for line in content.split("\n"):
            m = search(r"(\w+):([0-9a-zA-z-_]+)", line)
            if m is not None:
                model_type, model_name = m.group(1), m.group(2)
                if model_type not in models:
                    models[model_type] = []
                if model_name not in models[model_type]:
                    models[model_type].append(model_name)

        return models


class GitManager(BaseArchive, id="Git"):
    _username = "MOVAI_USER"
    _repos = {"slave": {},
              "master": {}}
    SLAVE = "slave"
    MASTER = "master"
    DEFAULT_REPO_ID = "default"

    def __init__(self, username: str, mode: str):
        """initialize Object with username

        Args:
            username (str): the username used to pull/push to the remote repo.
        """
        self._username = username
        self._mode = mode
        if mode not in GitManager._repos:
            GitManager._repos[mode] = {}

    @staticmethod
    def get_client(username: str) -> "GitManager":
        """will create an instance of GitManager, dynamically choose between
           master/slave according to the current running Robot.

        Args:
            username (str): the username to be used for GIT client.

        Returns:
            GitManager: an instance of the current mode applicable to the Robot

        Raises:
            GitUserError: in case there was a problem fetching git username.
        """
        manager_uri = getenv("MOVAI_MANAGER_URI", "localhost")

        client = None
        if "localhost" in manager_uri.lower().strip() or \
           "127.0.0.1" in manager_uri.lower().strip():
            # this is a manager
            client = MasterGitManager(username)
        else:
            client = SlaveGitManager(username)

        return client

    def is_tag(self, remote: str, revision: str) -> bool:
        """check if the provided revision is a tag or not
           based on the remote repo link provided.

        Args:
            remote (str): the remote link of the repository
            revision (str): commit hash or tag id.

        Returns:
            bool: indicates whether the
                  provided revision is a tag or not
        """
        if remote is None or revision is None:
            return False
        commit_id = self.get_full_commit_sha(remote, revision)
        if commit_id.find(revision) == -1:
            # this is a TAG
            return True
        return False

    def _register_repo(self, repo_name, repo: GitRepo):
        if self._mode == GitManager.MASTER:
            if self._username not in GitManager._repos[self._mode]:
                GitManager._repos[self._mode][self._username] = {}
            GitManager._repos[self._mode][self._username][repo_name] = repo
        else:
            if repo_name not in GitManager._repos[self._mode]:
                GitManager._repos[self._mode][repo_name] = repo

    def _get_repo(self, repo_name: str) -> GitRepo:
        """return the GitRepo object for the given repo_name
           taking into consideration the gitmanager type slave/master

        Args:
            repo_name (str): the repository name desired

        Returns:
            GitRepo: the matching GitRepo object foo the desired repo name.
        """
        repo = None
        if repo_name in GitManager._repos[self._mode]:
            repo = GitManager._repos[self._mode][repo_name]
        elif self._mode == GitManager.MASTER \
            and self._username in GitManager._repos[self._mode] \
                and repo_name in GitManager._repos[self._mode][self._username]:
            repo = GitManager._repos[self._mode][self._username][repo_name]
        return repo

    def _get_or_add_repo(self, remote: str) -> GitRepo:
        git_link = GitLink(remote)
        repo_name = git_link.repo
        repo = self._get_repo(repo_name)
        if repo is None:
            repo = GitRepo(remote, self._username,
                           self._get_local_path(remote), "")
            self._register_repo(repo_name, repo)
        # TODO: maybe we need to activate this in the future
        # else:
        #    repo.fetch()

        return repo

    def _get_or_add_version(self,
                            remote: str,
                            version: str="") -> GitRepo:
        """will get the desired version repo if exists
           if not will create a new one and returns it.

        Args:
            remote (str): remote link for the repository.
            version (str, optional): desired version. Defaults to None.

        Returns:
            GitRepo: GitRepo Object representing the requested version.
        """
        repo = self._get_or_add_repo(remote)
        try:
            repo.checkout(version)
        except VersionDoesNotExist:
            repo.fetch()
            repo.checkout(version)
        return repo

    def get_full_commit_sha(self, remote: str, revision: str) -> str:
        """returns a full commit sha

        Args:
            remote (str): the remote repository link
            revision (str): tag/commit/short commit id.

        Returns:
            str: returns full commit sha, 40 digits.
        """
        repo = self._get_or_add_version(remote, revision)
        if revision is None:
            return repo.get_latest_commit()
        return repo.git_client.rev_parse(revision)

    def list_versions(self, remote: str, is_branches: bool) -> list:
        """

        """
        repo = self._get_or_add_repo(remote)
        return repo.list_versions(is_branches)

    def list_models(self, remote: str) -> dict:
        repo = self._get_or_add_repo(remote)
        return repo.list_models()

    def get(self,
            obj_name: str,
            remote: str,
            version: str) -> Path:
        """Get a File from repository with specific version

        Args:
            obj_name (str): name of the file.
            remote (str): the remote repository link.
            version (str, optional): the commit/ tag/branch id desired.
                                      Defaults to None.

        Returns:
            Path: the local path of the requested File.
        """
        # TODO: check filename extension "json"
        if not obj_name.endswith('.json') and not obj_name.endswith('.py'):
            obj_name = obj_name + '.json'
        repo = self._get_or_add_version(remote, version)
        file_path = repo.checkout_file(obj_name)

        return Path(file_path)

    def commit(self,
               obj_name: str,
               remote: str,
               new_version: str = None,
               base_version: str = None,
               message: str = "") -> str:
        """will commit/save the specified obj locally.

        Args:
            obj_name (str): the filename of the desired file.
            remote (str): the remote link of the repo.
            new_version (str, optional): if given will create the new commit in
                                        a new branch with the name
                                        new_branch.
                                        Defaults to None.
            base_version (str, optional): on what branch we want to be based in
                                         the new commit.
            message (str, optional): the commit message. Defaults to "".

        Returns:
            str: the newly committed commit hash id.

        Raises:
            NoChangesToCommit: in case there was no changes to commit.
        """
        repo = self._get_or_add_version(remote, base_version)
        # TODO: check filename extension
        if obj_name.find('.json') == -1:
            obj_name += '.json'
        if obj_name not in repo.get_modified_files() \
           and obj_name not in repo.get_untracked_files():
            raise NoChangesToCommit()
        return repo.commit(obj_name, new_version, message)

    def diff_file(self,
                  remote: str,
                  filename: str) -> str:
        """return git diff string

        Args:
            remote (str): the remote repository
            filename (str): filename

        Returns:
            str: the diff string
        """
        repo = self._get_or_add_version(remote)
        if filename not in repo.get_modified_files():
            return ""
        return repo.diff_file(filename)

    def create_tag(self,
                   remote: str,
                   base_version: str,
                   tag: str,
                   message: str = "") -> bool:
        """will create a tag based on the given commit.

        Args:
            remote (str): the remote repository we want.
            base_commit (str): the base commit we want to be based on.
            tag (str): the desired tag name.
            message (str, optional): the message for the tag creation.
                                     Defaults to "".

        Returns:
            bool: whether the creation of the tag succeeded or not.
        """
        repo = self._get_or_add_version(remote, base_version)
        # in case the tag does not exist, try to fetch and check another time
        if repo.tag_exist(tag) or repo.tag_exist(tag, fetch=True):
            raise TagAlreadyExist(f"Tag {tag} already exist in Repository")
        tag_reference = repo.tag(base_version, tag, message)
        return tag_reference is not None
    
    def create_obj(self,
                   remote: str,
                   relative_path: str,
                   content: str,
                   base_version: str = None,
                   is_json: bool = True) -> None:
        """will create new file in repository locally using the relative path
           of the local repository path.
           this function neede because external user is not fully aware of the
           repo local path.

        Args:
            remote (str): the remote repository
            relative_path (str): the relative path to the root of the repo
            content (str): the file content to be added
            base_version (str, optional): based on what version to add the file
                                          Defaults to None.
            is_json (bool, optional): indicates whether the new file is json or
                                      not.
        """
        repo = self._get_or_add_version(remote, base_version)
        new_file_path = path_join(repo.local_path, relative_path)
        if FileSystem.is_exist(new_file_path):
            FileSystem.delete(new_file_path)
        FileSystem.write(new_file_path, content, is_json)

    def delete(self,
               remote: str,
               obj_name: str,
               version: str,
               **kwargs) -> str:
        """deletes an object.

        Args:
            obj_name (str): Name of the object (path)
            remote (str): Remote link.
            version (str): Version desired to remove from.

        Returns:
            str: new version hash.
        """
        # TODO: check filename extension "json"
        if not obj_name.endswith('.json') and not obj_name.endswith('.py'):
            obj_name = obj_name + '.json'
        repo = self._get_or_add_version(remote, version)
        file_path = path_join(repo.local_path, obj_name)
        if not FileSystem.is_exist(file_path):
            raise FileDoesNotExist(file_path)

        if FileSystem.delete(file_path):
            repo.index.remove(obj_name, working_tree=True)
            repo.git_client.add(all=True)
            return repo.git_client.commit(message=f"deleted {obj_name}")

        return None

    def pull(self, remote: str, branch: str):
        """will pull changes to local repository from remote_name repo

        Args:
            remote (str): the remote link of the repository.
            branch (str): the branch name.

        Returns:
            FetchInfo: see fetch method in GitPython
        """
        repo = self._get_or_add_repo(remote)
        return repo.pull(branch)

    def prev_version(self, remote: str, version: str):
        repo = self._get_or_add_version(remote, version)
        return repo.prev_version()

    def revert(self, remote: str, obj_name: str, version: str) -> Path:
        """revert a given version to previous one and return the file path
           for the reverted version

        Args:
            remote (str): the remote link of the repository.
            obj_name (str): Name of the object (path).
            version (str): the version we want to revert

        Returns:
            Path: path of the file.
        """
        prev_version = self.prev_version(remote, version)
        return self.get(obj_name, remote, prev_version)

    def push(self, remote: str, remote_name: str, tag_name: str = None,
             only_tag: bool = False) -> PushInfo:
        """will push repository defined by remote to remote_name repository

        Args:
            remote (str): the remote link of the reposiotry
            remote_name (str): remote name defined in local repository

        Returns:
            PushInfo: Carries information about the result of a push operation
                      of a single head
        """
        repo = self._get_or_add_version(remote)
        return repo.push(remote_name, tag_name, only_tag)

    @abstractmethod
    def _get_local_path(self, remote: str):
        """return the local path of a given remote repository

        Args:
            remote (str): the remote repository link.
        """
        pass

    def local_path(self, remote: str) -> Path:
        """local path of the repository

        Returns:
            str: local path of the repo.
        """
        return Path(self._get_local_path(remote))


class SlaveGitManager(GitManager):
    """a class to manage Slave Git Manager
       basically this class will be used mainly to fetch and get information
       without having the ability to change or create new content
    """
    def __init__(self, username: str):
        super().__init__(username, mode=GitManager.SLAVE)

    def commit(self, *args, **kwargs):
        raise SlaveManagerCannotChange()

    def push(self, *args, **kwargs):
        raise SlaveManagerCannotChange()

    def create_tag(self, *args, **kwargs):
        raise SlaveManagerCannotChange()

    def create_obj(self, *args, **kwargs) -> None:
        raise SlaveManagerCannotChange()

    def _get_local_path(self, remote):
        git_link = GitLink(remote)
        path_params = [GIT_BASE_FOLDER]
        path_params.append(git_link.repo)
        return path_join(*path_params)


class MasterGitManager(GitManager):
    """a class to manage Master Git Manager
       different from Slave Git Manager, this class will be able to make
       changes, pull/push/commit/tag ...
    """
    def __init__(self, username: str):
        super().__init__(username, mode=GitManager.MASTER)

    def _get_local_path(self, remote):
        git_link = GitLink(remote)
        path_params = [GIT_BASE_FOLDER]
        path_params.append(self._username)
        path_params.append(git_link.repo)
        return path_join(*path_params)
