from git.refs.tag import TagReference
from .filesystem import FileSystem
from git import Repo, InvalidGitRepositoryError, GitError, GitCommandError
from git.refs import HEAD
from git.index import IndexFile
from re import search
from os.path import join as path_join
from abc import ABC

# -----------------------------------------------------------------------------
# TODO
# need to be replaced, just for testing
from .authentication import AuthService


# TODO
# should be replaced by authentication service ?
# not sure how this should work
def get_tokenized_repo(remote, username):
    git_link = GitLink(remote)
    git_user = AuthService.get_username(remote, username)
    token = AuthService.get_token(remote, username)
    remote = git_link.get_https_link().split('https://')[1]
    return f"https://{git_user}:{token}@{remote}"
# -----------------------------------------------------------------------------


SLAVE = "slave"
MASTER = "master"
MOVAI_FOLDER_NAME = ".movai"
default_local_base = path_join(FileSystem.get_home_folder(), MOVAI_FOLDER_NAME)


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
        self._remote = self._git_link.get_https_link()
        self._username = username
        self._version = version
        self._repo_object = None
        self._default_branch = None
        self._local_path = local_path
        FileSystem.create_folder_recursively(self._local_path)
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
    def local_path(self) -> str:
        """local path of the repository

        Returns:
            str: local path of the repo.
        """
        return path_join(self._local_path, self._branch, self._commit)

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
        self._repo_object.git.fetch()

    def commit(self,
               filename: str = None,
               new_branch: str = None,
               message: str = None) -> str:
        """will commit file changes to current branch in case it's not
           detached HEAD, or create new branch if specified

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
        self._repo_object.git.checkout(file_name)
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

    def checkout(self, version):
        """will checkout and change version

        Args:
            version ([type]): the desired version
        """
        self._repo_object.git.checkout(version)

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
            tokenized_repo = get_tokenized_repo(self._remote, self._username)
            repo = Repo.clone_from(tokenized_repo, self._local_path,
                                   no_checkout=True)
        except GitError as e:
            print(f"Error {e}")

        return repo


class GitManager(ABC):
    _username = None
    _repos = {}
    DEFAULT_REPO_ID = "default"

    def __init__(self, username: str, mode: str = SLAVE):
        """initialize Object with username

        Args:
            username (str): the username used to pull/push to the remote repo.
        """
        self._username = username
        self._mode = mode
        if mode not in GitManager._repos:
            GitManager._repos[mode] = {}

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
        return repo

    def _get_or_add_version(self,
                            remote: str,
                            version: str = None) -> GitRepo:
        """will get the desired version repo if exists
           if not will create a new one and returns it.

        Args:
            remote (str): remote link for the repository.
            version (str, optional): desired version. Defaults to None.

        Returns:
            GitRepo: GitRepo Object representing the requested version.
        """
        git_link = GitLink(remote)
        repo_name = git_link.get_repo_name()
        repo = self._get_repo(repo_name)
        if repo is None:
            repo = GitRepo(remote, self._username,
                           self._get_local_path(remote), version)
            GitManager._repos[self._mode][repo_name] = repo
        if version is not None:
            try:
                repo.checkout(version)
            except GitCommandError:
                # it could be that the current info does not include
                # the wanted version, so try to fetch info first.
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

    def get_file(self,
                 file_name: str,
                 remote: str,
                 version: str = None) -> str:
        """Get a File from repository with specific version

        Args:
            file_name (str): name of the file.
            remote (str): the remote repository link.
            version (str, optional): the commit/ tag/branch id desired.
                                      Defaults to None.

        Returns:
            str: the local path of the requested File.
        """
        if file_name.find('json') == -1:
            file_name = file_name + '.json'
        repo = self._get_or_add_version(remote, version)
        file_path = repo.checkout_file(file_name)

        return file_path

    def commit_file(self,
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
                                        "new_branch".
                                        Defaults to None.
            base_branch (str, optional): on what branch we want to be based in
                                         the new commit.
            message (str, optional): the commit message. Defaults to "".

        Returns:
            str: the newly committed commit hash id.
        """
        repo = self._get_or_add_version(remote, base_branch)
        return repo.commit(filename, new_branch, message)

    def diff_file(self,
                  remote: str,
                  filename: str,
                  branch: str = None,
                  revision: str = None) -> str:
        # TODO
        # get the empty default repo to extract info
        default_repo = self._get_or_add_version(remote, empty_repo=True)
        branch = branch or default_repo.default_branch
        commit = revision or self.get_full_commit_sha(remote, revision)
        repo = self._get_or_add_version(remote, branch, commit)
        for diff in repo.head.commit.diff(None).iter_change_type('M'):
            if diff.a_path.find(filename) != -1:
                print("found")

    def create_tag(self,
                   remote: str,
                   base_commit: str,
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
        repo = self._get_or_add_version(remote, base_commit)
        tag_reference = None
        try:
            tag_reference = repo.tag(base_commit, tag, message)
        except Exception:
            pass
        return tag_reference is not None

    def _get_local_path(self, remote: str):
        """return the local path of a given remote repository

        Args:
            remote (str): the remote repository link.
        """
        pass


class SlaveGitManager(GitManager):
    def __init__(self, username: str):
        super().__init__(username, mode=SLAVE)

    def commit_file(self, *args, **kwargs):
        raise Exception("Slave Manager shall not commit changes")

    def create_tag(self, *args, **kwargs):
        raise Exception("Slave Manager shall not commit changes")

    def _get_local_path(self, remote):
        git_link = GitLink(remote)
        path_params = [default_local_base]
        path_params.append(git_link.get_repo_name())
        return path_join(*path_params)


class MasterGitManager(GitManager):
    def __init__(self, username: str):
        super().__init__(username, mode=MASTER)

    def _get_local_path(self, remote):
        git_link = GitLink(remote)
        path_params = [default_local_base]
        path_params.append(self._username)
        path_params.append(git_link.get_repo_name())
        return path_join(*path_params)


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
