from dal.utils.project_metadata import ProjectSource

from .scope import Scope


class GraphicScene(Scope):
    """GraphicScene scope."""

    scope = "GraphicScene"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="GraphicScene", name=name, version=version, new=new, db=db)

    @classmethod
    def _import_dependencies(cls, data: dict, source: ProjectSource):
        ret = []
        errors = []
        for assets in data["AssetType"].values():
            for asset in assets.values():
                annotation_names = list(asset.get("Annotation", {}).keys())
                imported_annotations, annotation_errors = cls.get_class(
                    "Annotation"
                ).import_metadata(annotation_names, source)
                ret.extend(imported_annotations)
                errors.extend(annotation_errors)
        return ret, errors

    @classmethod
    def _export_dependencies(cls, scope):
        ret = {}
        for package_name in ("maps", "meshes", "point_clouds"):
            ret.update(cls.get_class("Package").export_metadata([package_name]))

        for asset_type in scope.AssetType.values():
            for asset in asset_type.AssetName.values():
                for key in asset.Annotation:
                    ret.update(cls.get_class("Annotation").export_metadata([key]))
        return ret
