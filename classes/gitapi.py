from git.util import join_path
from filesystem import FileSystem
from git import Repo, InvalidGitRepositoryError, GitError, GitCommandError
from re import search
from os.path import join as path_join

default_local_base = path_join(FileSystem.get_home_folder(), ".movai")


class GitRepo:
    """ class representing single repository"""

    def __init__(self, remote: str, username: str, token: str,
                 branch: str = None, commit: str = None):
        """initialze new repository.
           creates local folder and clone the repo with the path
           /repo_name/branch/commit

        Args:
            remote (str): remote link of repository.
            username (str): username to be used.
            token (str): token string to be used
            branch (str, optional): branch name desired, if None the default
                                    branch of the repo will be used
            commit (str, optional): commit hash id, if None the latest commit
                                    in branch will be used.
        """
        self._git_link = GitLink(remote)
        self._remote = self._git_link.get_https_link()
        self._username = username
        self._token = token
        self._branch = branch
        self._commit = commit
        self._repo_object = None
        self._default_branch = None
        self._local_path = path_join(default_local_base,
                                     self._git_link.get_repo_name())
        self.REPO_LOCAL_PATH = path_join(default_local_base,
                                         self._git_link.get_repo_name())
        FileSystem.create_folder_recursively(self._local_path)
        if branch is None:
            # this should be default repository
            self._repo_object = self.get_or_create_empty_repo()
            self._default_branch = str(self._repo_object.active_branch)
            self._branch = self._default_branch
        else:
            self._commit = commit
            self._local_path = join_path(default_local_base,
                                         self._git_link.get_repo_name(),
                                         branch,
                                         commit)
            self._repo_object = self._clone_no_checkout()

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

    @property
    def repository(self) -> str:
        """return the repository link with username and token.
           used to pull/push to the reposiotry with permission.

        Returns:
            str: username:token@remote
        """
        remote = self._remote.split("https://")[1]
        return f"https://{self._username}:{self._token}@{remote}"

    @property
    def local_path(self) -> str:
        """local path of the repository

        Returns:
            str: local path of the repo.
        """
        return join_path(self._local_path, self._branch, self._commit)

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
        return self._git_link.get_repo_name()

    @property
    def branch(self) -> str:
        """current branch of the repository

        Returns:
            str: branch name
        """
        return self._branch

    @property
    def commit_sha(self) -> str:
        """current commit sha1 id of the repository

        Returns:
            str: commit sha1 id.
        """
        return self._commit

    @property
    def git_client(self) -> Repo.git:
        """returns the git client in the repository
           used mainly for direct command lines

        Returns:
            Repo.git: git client object
        """
        return self._repo_object.git

    def checkout_file(self, file_name: str) -> str:
        """will checkout file of the repository commit hash
           and returns it's local path

        Args:
            file_name (str): the desired file name

        Returns:
            str: local path of the requested file
        """
        print(f"running: checkout {self.commit_sha} -- {file_name}")
        self._repo_object.git.checkout(self.commit_sha, "--", file_name)
        file_path = join_path(self._local_path, file_name)
        return file_path

    def get_or_create_empty_repo(self) -> Repo:
        """create or get empty repository to extract info from it
           instead of always cloning a new empty repo.
           the purpose is to see information such as branches, commits, tags
           a fetch will be called every time this function called.

        Returns:
            git.Repo: a git Repository object representing the empty repo for
                      the remote provided in init function
        """
        path = path_join(self._local_path, '.empty_default_repo')
        FileSystem.create_folder_recursively(path)
        try:
            repo = Repo(path)
        except InvalidGitRepositoryError:
            repo = Repo.clone_from(self.repository, path,
                                   no_checkout=True)
        repo.git.fetch()
        return repo

    def get_latest_commit(self) -> str:
        """get the latest commit sha1 hash in repository

        Returns:
            str: commit sha1 hash
        """
        remote_alias = str(self._repo_object.remote())
        commits_log = self._repo_object.git.log(
                                    f"{remote_alias}/{self._branch}",
                                    "--oneline")
        commit = commits_log.split('\n')[0].split(' ')[0]
        return self._repo_object.git.rev_parse(commit)

    def _clone_no_checkout(self) -> Repo:
        """clone given branch, commit, tag without really checking out files
           similar to empty repository but with all the repo information.

        Returns:
            git.Repo: Repo object.
        """
        repo = None
        FileSystem.create_folder_recursively(self._local_path)
        try:
            repo = Repo(self._local_path)
        except InvalidGitRepositoryError:
            # Repository does not exist, creating one.
            repo = Repo.clone_from(self.repository, self._local_path,
                                   branch=self._branch, no_checkout=True)
        except GitError as e:
            print(f"Error {e}")

        return repo


class GitManager:
    _token = None
    _username = None
    _versions = {}

    def __init__(self, username: str, token: str):
        """initialize Object with username and token

        Args:
            username (str): the username used to pull/push to the remote repo.
            token (str): the token string used for permission for
                         the remote repo.
        """
        self._username = username
        self._token = token

    @staticmethod
    def get_version(branch: str, commit: str) -> str:
        """returns a string representing a version for the branch and commit provided

        Args:
            branch (str): branch name
            commit (str): commit hash sha1

        Returns:
            str: a string representing a version for branch and commit.
        """
        if branch is None or commit is None:
            return None
        return branch + "/" + commit

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

    def _get_or_add_version(self,
                            remote: str,
                            branch: str = None,
                            commit: str = None) -> GitRepo:
        """will get the desired version repo if exists
           if not will create a new one and returns it.

        Args:
            remote (str): remote link for the repository.
            branch (str, optional): desired branch name. Defaults to None.
            commit (str, optional): desired commit hash id. Defaults to None.

        Returns:
            GitRepo: GitRepo Object representing the requested version.
        """
        git_link = GitLink(remote)
        repo_name = git_link.get_repo_name()
        repo = None
        if repo_name not in GitManager._versions:
            GitManager._versions[repo_name] = {}
        version = GitManager.get_version(branch, commit)
        if version not in GitManager._versions[repo_name]:
            repo = GitRepo(remote, self._username, self._token, branch, commit)
            _branch = branch or repo.branch
            _commit = commit or repo.commit_sha
            version = GitManager.get_version(_branch, _commit)
            GitManager._versions[repo_name][version] = repo
        return GitManager._versions[repo_name][version]

    def get_full_commit_sha(self, remote: str, revision: str) -> str:
        """returns a full commit sha

        Args:
            remote (str): the remote repository link
            revision (str): tag/commit/short commit id.

        Returns:
            str: returns fuoll commit sha, 40 digits.
        """
        # get the empty default repo to extract info
        repo = self._get_or_add_version(remote, branch=None, commit=None)
        return repo.git_client.rev_parse(revision)

    def get_file(self,
                 file_name: str,
                 remote: str,
                 branch: str = None,
                 revision: str = None) -> str:
        """Get a File from repository with specific version

        Args:
            file_name (str): name of the file.
            remote (str): the remote repository link.
            branch (str, optional): the branch name to be based on.
                                    Defaults to None.
            revision (str, optional): the commit/ tag id desired.
                                      Defaults to None.

        Returns:
            str: the local path of the requested File.
        """
        if file_name.find('json') == -1:
            file_name = file_name + '.json'
        repo = self._clone_no_checkout(remote, branch, revision)
        file_path = repo.checkout_file(file_name)

        return file_path

    def _clone_no_checkout(self,
                           remote: str,
                           branch: str = None,
                           revision: str = None) -> GitRepo:
        """clone given branch, commit, tag without really checking out files
           similar to empty repository but with all the repo information.

        Args:
            remote (str): the remote link of the repository.
            branch (str, optional): branch name. Defaults to None.
            revision (str, optional): commit hash id or tag name.
                                      Defaults to None.

        Returns:
            GitRepo: GitRepo Object representing the requested version.
        """
        # get the empty default repo to extract info
        default_repo = self._get_or_add_version(remote,
                                                branch=None,
                                                commit=None)
        branch = branch or default_repo.default_branch
        if revision is None:
            commit = default_repo.get_latest_commit()
        else:
            if not default_repo.version_exist(revision):
                raise Exception(f"commit/tag <{revision}> does not \
                                exist in {remote}")
            commit = self.get_full_commit_sha(remote, revision)

        version = GitManager.get_version(branch, commit)
        if version not in GitManager._versions[default_repo.name]:
            repo = GitRepo(remote, self._username, self._token, branch, commit)
            GitManager._versions[default_repo.name][version] = repo

        if self.is_tag(remote, revision):
            # in case this is a TAG create symlink to the commit folder
            link_path = join_path(default_repo.REPO_LOCAL_PATH,
                                  branch, revision)
            FileSystem.create_symbolic_link(src="./" + commit,
                                            dst=link_path)
        return GitManager._versions[default_repo.name][version]


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
        """reutrns a https link for provided link in init function

        Returns:
            str: https link
        """
        if self._https_link is not None:
            return self._https_link
        return "https://" + self._ssh_link.split("@")[1].replace(":", "/")

    def get_ssh_link(self) -> str:
        """returns a ssh link for the provided link in init function

        Returns:
            str: ssh link
        """
        if self._ssh_link is not None:
            return self._ssh_link
        return "git@" + \
            self._https_link.split("//")[1].replace("/", ":", 1)

    def get_relative_repo_path(self) -> str:
        """will return relative repository path without the domain

        Returns:
            str: relative repository path.
        """
        return search("https://([^/]+)(/.*)", self._https_link).group(2)

    def get_repo_name(self) -> str:
        """returns the repository name from the provided link in init.

        Returns:
            str: repository name
        """
        repo_name = self._https_link.split("/")[-1]
        if repo_name.find(".") != -1:
            repo_name = repo_name.split(".")[0]
        return repo_name


manager = GitManager(username="Mograbi",
                     token="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")

manager.get_file("file1", "https://github.com/Mograbi/try.git")
manager.get_file(file_name="file2",
                 remote="https://github.com/Mograbi/try.git",
                 branch="v2",
                 revision="v0.2")
manager.get_file(file_name="file1",
                 remote="https://github.com/Mograbi/try.git",
                 branch="v2",
                 revision="918bcd7fb25b")
