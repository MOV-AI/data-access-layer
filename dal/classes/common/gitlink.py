"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from re import search
from os.path import join


class GitLink:
    """a class to represent a remote git link
       whether it was ssh link or https.
       Git links Parser.

        example of git links:
            GitLab:
                git@gitlab.com:szabiprog/cashflow.git
                https://gitlab.com/szabiprog/cashflow.git
                https://gitlab.com/szabiprog/cashflow

            GitHub:
                https://github.com/MOV-AI/data-access-layer.git
                git@github.com:MOV-AI/data-access-layer.git
                https://github.com/MOV-AI/data-access-layer

            Bitbucket:
                git@bitbucket.org:robosavvy/movai-cli.git
                https://Moawiyam@bitbucket.org/robosavvy/movai-cli.git
    """
    HTTPS_REGEX = "https://([^/]+)/([^/]+)/([^/]*)(/(.*))?"
    SSH_REGEX = "git@([^:]+):([^/]+)/([^/]*)(/(.*))?"

    def __init__(self, link: str):
        self._link = link
        m = search(GitLink.HTTPS_REGEX, link) or \
            search(GitLink.SSH_REGEX, link)
        if m is None:
            raise ValueError("git link provided does not match \
                             with HTTPS or SSH git links")
        self._domain = m.group(1)
        if "@" in self._domain:
            self._domain = self._domain.split("@")[1]
        self._owner = m.group(2)
        self._repo = m.group(3)
        self._path = m.group(5) or ""

    @property
    def repo_https_link(self) -> str:
        """return https link representing the remote link
           useful in case git link received.

        Returns:
            str: https link
        """
        return f"https://{self.remote}"

    @property
    def repo_ssh_link(self) -> str:
        return f"git@{self.domain}:{self.owner}/{self.repo}"

    @property
    def domain(self) -> str:
        """return the domain of the given link

        Returns:
            str: domain name
        """
        return self._domain

    @property
    def owner(self) -> str:
        """the owner of the repository given by link

        Returns:
            str: owner name
        """
        return self._owner

    @property
    def repo(self) -> str:
        """return the repository name

        Returns:
            str: repository name
        """
        repo = self._repo
        if ".git" in self._repo:
            repo = self._repo.split(".git")[0]
        return repo

    @property
    def path(self) -> str:
        """the path inside the repo given by the link

        Returns:
            str: the path inside the repository.
        """
        return self._path

    @property
    def remote(self) -> str:
        """the remote link
           composed of: domain/owner/repository/path

        Returns:
            str: the remote link
        """
        return join(self.domain, self.owner, self.repo, self.path)
