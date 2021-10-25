from filesystem import FileSystem
from git import Repo, InvalidGitRepositoryError, GitError
from json import load as LoadJson

default_local_base = "~/.movai"


class GitApi:
    _token = None
    _username = None

    def __init__(self, remote, token=None, username=None):
        self._token = token
        self._username = username
        self._remote = ''.join(("github.com", remote.split('github.com')[1]))
        relative_path = self._remote.split("github.com")[1]
        if relative_path[0] == ":":
            relative_path = relative_path.replace(":", "/")
        self._local_path = FileSystem.create_folder_recursively(
                            default_local_base + relative_path)
        self._versions = {}

    @classmethod
    def login(cls, username, token):
        """will register access token to git localy.

        Args:
            token (str): the token str to be used.
            username (str): username to be used.
        """
        cls._token = token
        cls._username = username

    @property
    def repository(self) -> str:
        return f"https://{self._username}:{self._token}@{self._remote}"

    @property
    def local_path(self) -> str:
        if hasattr(self, '_local_path'):
            return self._local_path
        # TODO add proper exception
        raise AttributeError('local_path does not exist')

    @property
    def version(self) -> str:
        if self._repo is None:
            # TODO change Exception
            raise Exception('')
        return str(self._repo.head.commit)

    def get_file(self, file_name, version=None, tag=None):
        data = None
        if not self.clone_no_checkout(version):
            return None
        repo = self._versions[version]
        repo.git.checkout(version)
        if file_name.find('json') == -1:
            file_name = file_name + '.json'
        file_path = self.get_version_local_path(version) + "/" + file_name
        with open(file_path) as f:
            data = LoadJson(f)
        return data

    def get_version_local_path(self, version):
        if version in self._versions:
            return self._versions[version].git.working_dir
        return None

    def pull(self, version):
        if version in self._versions:
            self._versions[version].remotes.origin.pull()
        else:
            # TODO , add better exceptions here
            raise Exception('version does not exist')

    def clone_no_checkout(self, version) -> bool:
        repo = None
        if version in self._versions:
            return True
        version_path = self.local_path + '/' + version
        FileSystem.create_folder_recursively(version_path)
        try:
            repo = Repo(version_path)
        except InvalidGitRepositoryError:
            repo = Repo.clone_from(self.repository,
                                   version_path, no_checkout=True)
        except GitError as e:
            print(f"Error {e}")
            return False

        self._versions[version] = repo
        return True


#token="....."
#user="Mograbi"
#archive = GitApi("https://github.com/MOV-AI/node-baseline",
#                 token,
#                 user)
#print(archive.get_file('lidar_slam.json',
#                 version='ae56aef76445c0a644325d13b80d18db50f1e9b3'))
