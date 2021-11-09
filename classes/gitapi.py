from typing import Tuple
from git.util import join_path
from filesystem import FileSystem
from git import Repo, InvalidGitRepositoryError, GitError, GitCommandError
from re import search
from os.path import join as path_join

default_local_base = path_join(FileSystem.get_home_folder(), ".movai")


class GitRepo:
    _token = None
    _username = None
    _default_branch = None
    _versions = {}

    def __init__(self, remote: str):
        """initialize with remote link, get default branch name

        Args:
            remote (str): the remote link of the repository, ssh or https.
        """
        git_link = GitRepo.GitLink(remote)
        self._remote = git_link.get_https_link()
        self._local_path = path_join(default_local_base,
                                     git_link.get_repo_name())
        FileSystem.create_folder_recursively(self._local_path)
        self._tags = {}
        self.git_link = git_link
        empty_repo = self.get_or_create_empty_repo()
        GitRepo._default_branch = str(empty_repo.active_branch)

    @classmethod
    def login(cls, username: str, token: str):
        """will register access token to git in class.

        Args:
            token (str): the token str to be used.
            username (str): username to be used.
        """
        cls._token = token
        cls._username = username

    @property
    def repository(self) -> str:
        """return the repository link with username and token

        Returns:
            str: username:token@repository
        """
        remote = self._remote.split("https://")[1]
        return f"https://{self._username}:{self._token}@{remote}"

    @property
    def local_path(self) -> str:
        """return the local path where the current repo exist

        Raises:
            AttributeError: in case _local_path does not exist in object

        Returns:
            str: local path of the current repo
        """
        if hasattr(self, '_local_path'):
            return self._local_path
        # TODO add proper exception
        raise AttributeError('local_path does not exist')

    @property
    def default_branch(self) -> str:
        """returns the default branch for the remote repository

        Returns:
            str: string representing the default branch name.
        """
        return GitRepo._default_branch

    def get_version_local_path(self, version: str) -> str:
        """return the local path of specific version that was already requested

        Args:
            version (str): the desired version.

        Returns:
            str: the path which the version exist in.
        """
        if version in GitRepo._versions:
            return GitRepo._versions[version].git.working_dir
        return ""

    def get_version_repo(self, version: str) -> Repo:
        """get a git.Repo object for the requested version in case it exist

        Args:
            version (str): the requested version

        Raises:
            Exception: in case the requested version does not exist in class.

        Returns:
            git.Repo: a git.Repo object for the requested version.
        """
        if version in GitRepo._versions:
            return GitRepo._versions[version]
        raise Exception("version: {version} never checked out")

    def get_or_create_empty_repo(self) -> Repo:
        """create or get empty repository to extract info from it
           instead of always cloning a new empty repo.
           the purpose is to see branches, commits, tags, ....
           a fetch will be called every time this function called.

        Returns:
            git.Repo: a git Repository object representing the empty repo for
                      the remote provided in init function
        """
        path = path_join(self.local_path, '.empty_default_repo')
        FileSystem.create_folder_recursively(path)
        try:
            repo = Repo(path)
        except InvalidGitRepositoryError:
            repo = Repo.clone_from(self.repository, path,
                                   no_checkout=True)
        repo.git.fetch()
        return repo

    def get_file(self,
                 file_name: str,
                 revision: str = None,
                 branch: str = None) -> str:
        """Get a File from repository with specific version

        Args:
            file_name (str): name of the file
            revision (str, optional): the commit/ tag id desired.
                                    Defaults to None.
            branch (str, optional): the branch name to be based on.
                                    Defaults to None.

        Returns:
            str: the local path of the requested File.
        """
        if revision is not None:
            if not self._version_exist(revision):
                raise Exception("tag or commit does not exist in repository")
        rev, _ = self._get_version(branch, revision)
        clone_succeeded = self.clone_no_checkout(branch, revision)
        if not clone_succeeded:
            return None
        repo = self.get_version_repo(rev)
        if file_name.find('json') == -1:
            file_name = file_name + '.json'

        commit_hash = rev.split("/")[1]
        print(f"running: checkout {commit_hash} -- {file_name}")
        repo.git.checkout(commit_hash, "--", file_name)
        file_path = join_path(self.get_version_local_path(rev), file_name)
        return file_path

    def get_latest_commit(self, branch: str = None):
        """get the latest commit sha1 hash in given branch

        Args:
            branch (str, optional): the desired branch,
                                    if None the default branch will be used.
                                    Defaults to None.

        Returns:
            str: commit sha1 hash
        """
        empty_repo = self.get_or_create_empty_repo()
        if branch is None:
            branch = self.default_branch
        remote_alias = str(empty_repo.remote())
        commits_log = empty_repo.git.log(f"{remote_alias}/{branch}",
                                         "--oneline")
        commit = commits_log.split('\n')[0].split(' ')[0]
        return empty_repo.git.rev_parse(commit)

    def _version_exist(self, revision: str) -> bool:
        """check if version (commit / tag) exist in the repo

        Args:
            revision (str): the version need to be checked

        Returns:
            bool: True if exist otherwise fasle.
        """
        empty_repo = self.get_or_create_empty_repo()
        try:
            empty_repo.git.rev_parse(revision)
        except GitCommandError as e:
            if e.stderr.find(
                    "unknown revision or path not in the working tree"):
                return False
        return True

    def _get_version(self,
                     branch: str = None,
                     revision: str = None) -> Tuple[str, bool]:
        """get the version of given branch commit tag

        Args:
            branch (str, optional): branch name. Defaults to None.
            revision (str, optional): commit hash or tag id. Defaults to None.

        Returns:
            str: (branch/commit, bool), the bool to indicates whether the
                 provided revision is a tag or not
        """
        if branch is None:
            branch = self._get_default_branch_name()
        if revision is None:
            revision = self.get_latest_commit()
        empty_repo = self.get_or_create_empty_repo()
        commit_id = empty_repo.git.rev_parse(revision)
        rev_tag = False
        if commit_id.find(revision) == -1:
            # this is a TAG
            rev_tag = True
        return (f"{branch}/{commit_id}", rev_tag)

    def clone_no_checkout(self,
                          branch: str = None,
                          revision: str = None) -> bool:
        """clone giver branch, commit, tag without really checking out files
           similar to empty repository but with all the repo information.

        Args:
            branch (str, optional): branch name. Defaults to None.
            commit (str, optional): commit hash id. Defaults to None.
            tag (str, optional): tag name. Defaults to None.

        Raises:
            Exception: in case branch was not provided.

        Returns:
            bool: wether the clone succeeded or not
        """
        if branch is None:
            raise Exception("a branch must be provided")
        if revision is None:
            rev = self.get_latest_commit(branch)
        rev, is_tag = self._get_version(branch, revision)
        if rev in GitRepo._versions:
            # we already have this version repo locally
            return True
        path = join_path(self.local_path, rev)
        FileSystem.create_folder_recursively(path)
        if is_tag:
            # in case this is a TAG create symlink to the commit folder.
            print(f"{join_path(self.local_path, branch, revision)},,,{path}")
            link_path = join_path(self.local_path, branch, revision)
            FileSystem.create_symbolic_link(
                            src="./" + rev.split("/")[1],
                            dst=link_path)
        try:
            repo = Repo(path)
        except InvalidGitRepositoryError:
            # Repository does not exist, creating one.
            repo = Repo.clone_from(self.repository, path,
                                   branch=branch, no_checkout=True)
        except GitError as e:
            print(f"Error {e}")
            return False

        GitRepo._versions[rev] = repo
        return True

    class GitLink:
        """a class to represent a remote git link
           whether it was ssh link or https.
        """
        def __init__(self, link: str):
            self._link = link
            self._ssh_link = None
            self._https_link = None
            if link.find("https://") != -1:
                self._https_link = link
                self._ssh_link = self.get_ssh_link()
            elif link.find("git@") != -1:
                self._ssh_link = link
                self._https_link = self.get_https_link()
            else:
                raise Exception("not a valid Git link")

        def get_https_link(self) -> str:
            if self._https_link is not None:
                return self._https_link
            return "https://" + self._ssh_link.split("@")[1].replace(":", "/")

        def get_ssh_link(self) -> str:
            if self._ssh_link is not None:
                return self._ssh_link
            return "git@" + \
                self._https_link.split("//")[1].replace("/", ":", 1)

        def get_relative_repo_path(self) -> str:
            return search("https://([^/]+)(/.*)", self._https_link).group(2)

        def get_repo_name(self) -> str:
            repo_name = self._https_link.split("/")[-1]
            if repo_name.find(".") != -1:
                repo_name = repo_name.split(".")[0]
            return repo_name

