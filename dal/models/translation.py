"""Translation model"""
from typing import List

from dal.movaidb.database import MovaiDB
from .model import Model


class Translation(Model):
    """Translation model"""

    @staticmethod
    def get_available_languages() -> List[str]:
        """Fetch the list of available languages.

        Returns:
            list: A list of available languages in the database.
        """
        all_languages = set()
        records, _ = MovaiDB("local").search_by_args("Translation", Name="*")
        for record in records["Translation"]:
            for language in record["Translations"].keys():
                all_languages.add(language)
        return sorted(all_languages)


Model.register_model_class("Translation", Translation)
