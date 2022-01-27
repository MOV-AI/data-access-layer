from os import stat
from re import search
authentications = dict()
authentications["github.com"] = \
            {
                "Mograbi": {
                    "user": "Mograbi",
                    "token": "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"
                    }
            }


class AuthService:
    @staticmethod
    def get_token(remote, movai_user):
        website = "github.com"
        m = search(r"(\w+\.com)", remote)
        if m is not None:
            website = m.group(1)

        return authentications[website][movai_user]["token"]

    @staticmethod
    def get_username(remote, movai_user):
        website = "github.com"
        m = search(r"(\w+\.com)", remote)
        if m is not None:
            website = m.group(1)

        return authentications[website][movai_user]["user"]
