from .scope import Scope


class SharedDataTemplate(Scope):
    """SharedDataTemplate scope."""

    scope = "SharedDataTemplate"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="SharedDataTemplate", name=name, version=version, new=new, db=db)
