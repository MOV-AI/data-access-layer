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
        errors = []
        callbacks = [
            data["ScoringFunction"],
            data["GenericScoringFunction"],
            data["TaskFilter"],
        ]
        callbacks = [
            callback_name for callback_name in callbacks if not PLACEHOLDER_RE.search(callback_name)
        ]

        if callbacks:
            imported_callbacks, callback_errors = cls.get_class("Callback").import_metadata(
                callbacks, source
            )
            ret.extend(imported_callbacks)
            errors.extend(callback_errors)

        shared_data = data["SharedData"]

        if shared_data:
            imported_sharedDataTemplates, SharedDataTemplate_errors = cls.get_class(
                "SharedDataTemplate"
            ).import_metadata(shared_data.keys(), source)
            ret.extend(imported_sharedDataTemplates)
            errors.extend(SharedDataTemplate_errors)
        return ret, errors

    @classmethod
    def _export_dependencies(cls, scope):
        callback_exporter = cls.get_class("Callback")
        shared_data_exporter = cls.get_class("SharedDataTemplate")

        for key in ("ScoringFunction", "GenericScoringFunction", "TaskFilter"):
            name = getattr(scope, key)
            callback_exporter.export_metadata([name])

        for name in scope.SharedData:
            shared_data_exporter.export_metadata([name])
