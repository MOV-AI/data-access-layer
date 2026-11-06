from dal.utils.project_metadata import ProjectSource

from .scope import Scope


class SharedDataEntry(Scope):
    """SharedDataEntry scope."""

    scope = "SharedDataEntry"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="SharedDataEntry", name=name, version=version, new=new, db=db)

    @classmethod
    def _import_dependencies(cls, data: dict, source: ProjectSource):
        shared_data_template_name = data["TemplateID"].values()
        return cls.get_class("SharedDataTemplate").import_metadata(
            [shared_data_template_name], source
        )

    @classmethod
    def _export_dependencies(cls, scope):
        return cls.get_class("SharedDataTemplate").export_metadata([scope.TemplateID])
