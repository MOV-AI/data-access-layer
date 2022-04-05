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
