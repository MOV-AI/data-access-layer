from .scope import Scope


class Annotation(Scope):
    """Annotation scope."""

    scope = "Annotation"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Annotation", name=name, version=version, new=new, db=db)
