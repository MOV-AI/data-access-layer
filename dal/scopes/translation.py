from dal.validation.validator import TranslationValidator
from .scope import Scope

# pylint: disable=unused-import
from .translation_constants import DEFAULT_LANGUAGE


class Translation(Scope):
    """Translation scope."""

    scope = "Translation"
    validator = TranslationValidator()

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Translation", name=name, version=version, new=new, db=db)
