from dal.validation.validator import TranslationValidator
from .scope import Scope


DEFAULT_LANGUAGE = "en"


class Translation(Scope):
    """Translation scope."""

    scope = "Translation"
    validator = TranslationValidator()

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Translation", name=name, version=version, new=new, db=db)
