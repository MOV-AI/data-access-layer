import os
from pathlib import Path
import re

from dal.utils.project_metadata import ProjectSource
from dal.validation.validator import TranslationValidator
from .scope import Scope

# pylint: disable=unused-import
from dal.constants.translation import DEFAULT_LANGUAGE


class Translation(Scope):
    """Translation scope."""

    scope = "Translation"
    validator = TranslationValidator()

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Translation", name=name, version=version, new=new, db=db)

    @classmethod
    def _update_metadata(cls, data: dict, file_path: str, source: ProjectSource) -> dict:
        path = Path(file_path)
        translations = data["Translations"] = {}

        pattern = re.compile(rf"{re.escape(path.stem)}\.([a-z]+)\.po$")
        for file in source.list_dir(str(path.parent)):
            match = pattern.match(file)
            if not match:
                continue

            po_path = str(path.parent / file)
            if source.is_file(po_path):
                translations[match[1]] = {"po": source.read_text(po_path)}
        return data

    @classmethod
    def _export_extra_files(cls, scope, name: str):
        ret = {}

        for lang, data in scope.Translations.items():
            code_path = os.path.join("Translation", f"{name}.{lang}.po")
            ret[code_path] = data.po

        return ret
