from dal.utils.project_metadata import PLACEHOLDER_RE, ProjectSource

from .scope import Scope


class TaskTemplate(Scope):
    """TaskTemplate scope."""

    scope = "TaskTemplate"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="TaskTemplate", name=name, version=version, new=new, db=db)

    @classmethod
    def _import_dependencies(cls, data: dict, source: ProjectSource):
        ret = []
        callbacks = [
            data["ScoringFunction"],
            data["GenericScoringFunction"],
            data["TaskFilter"],
        ]
        callbacks = [
            callback_name for callback_name in callbacks if not PLACEHOLDER_RE.search(callback_name)
        ]

        if callbacks:
            ret += cls.get_class("Callback").import_metadata(callbacks, source)

        shared_data = data["SharedData"]

        if shared_data:
            ret += cls.get_class("SharedDataTemplate").import_metadata(shared_data.keys(), source)
        return ret

    @classmethod
    def _export_dependencies(cls, scope):
        callback_exporter = cls.get_class("Callback")
        shared_data_exporter = cls.get_class("SharedDataTemplate")

        for key in ("ScoringFunction", "GenericScoringFunction", "TaskFilter"):
            name = getattr(scope, key)
            callback_exporter.export_metadata([name])

        for name in scope.SharedData:
            shared_data_exporter.export_metadata([name])
