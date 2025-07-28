"""Translation scope."""
from .scope import Scope


class Translation(Scope):
    """Translation scope."""

    scope = "Translation"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Translation", name=name, version=version, new=new, db=db)
