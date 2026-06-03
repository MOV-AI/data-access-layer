"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Callback Model
"""

import importlib
import inspect
import pkgutil
from typing import Any, Dict, List
from movai_core_shared.logger import Log

from .scopestree import scopes

from .model import Model


logger = Log.get_logger(__name__)


class Callback(Model):
    """Callback Model"""

    __RELATIONS__ = {
        # "schemas/1.0/Callback/Message" : {
        #     "schema_version": "1.0",
        #     "scope": "Message"
        # }
    }

    # default __init__

    def is_valid(self) -> bool:
        """returns true"""
        return True

    def remove(self, force: bool = False) -> Dict:  # pylint: disable=unused-argument
        """This doesn't make sense here anymore"""
        return {}

    def has_permission(
        self, user: Any, permission: Any, app_name: str
    ) -> bool:  # pylint: disable=unused-argument
        """Needs implementation"""
        # TODO implement
        return True

    # ported blindly
    @staticmethod
    def get_modules() -> List:
        """Get list of modules"""
        import pydoc

        modules_list = [x[1] for x in pkgutil.iter_modules()]

        modules = {}

        def callback(path, modname, desc, modules=modules):
            if modname and modname[-9:] == ".__init__":
                modname = modname[:-9] + " (package)"
            if modname.find(".") < 0:
                modules[modname] = 1

        def onerror(modname):
            callback(None, modname, None)

        pydoc.ModuleScanner().run(callback, onerror=onerror)

        return list(modules.keys())

    # ported blindly
    @staticmethod
    def get_methods(module: str) -> Dict:
        """get methods of module"""
        import pydoc

        try:
            object = importlib.import_module(module)

            all = getattr(object, "__all__", None)
            # try:
            #    all = object.__all__
            # except:
            #    all = None

            classes = []
            for key, value in inspect.getmembers(object, inspect.isclass):
                # if __all__ exists, believe it.  Otherwise use old heuristic.
                if all is not None or (inspect.getmodule(value) or object) is object:
                    if pydoc.visiblename(key, all, object):
                        classes.append((key, value))
                else:
                    classes.append((key, value))

            funcs = []
            for key, value in inspect.getmembers(object, inspect.isroutine):
                # if __all__ exists, believe it.  Otherwise use old heuristic.
                if (
                    all is not None
                    or inspect.isbuiltin(value)
                    or inspect.getmodule(value) is object
                ):
                    if pydoc.visiblename(key, all, object):
                        funcs.append((key, value))
                else:
                    funcs.append((key, value))

            data = []
            for key, value in inspect.getmembers(object, pydoc.isdata):
                if pydoc.visiblename(key, all, object):
                    data.append((key, value))

            # modpkgs = {}
            modpkgs_names = set()
            if hasattr(object, "__path__"):
                for _, modname, _ in pkgutil.iter_modules(object.__path__):
                    modpkgs_names.add(modname)
                    # modpkgs[modname] = Callback.get_methods(module+'.'+modname)

            # Detect submodules as sometimes created by C extensions

            methods = {
                "modules": list(modpkgs_names),
                "classes": [x[0] for x in classes],
                "functions": [x[0] for x in funcs],
                "consts": [x[0] for x in data],
            }

            return methods
        except:
            logger.error("Cannot import Module", module)
            return {}

    # ported blindly
    @staticmethod
    def get_full_modules() -> Dict:
        """get get full dict of modules"""

        module_description = {}

        mods = Callback.get_modules()
        for module in mods:
            # filter modules
            if module.startswith("_"):
                # ignore module
                continue
            module_description[module] = Callback.get_methods(module)

        return module_description

    def template_depends(self, force: bool = False) -> Dict:
        """get all the objects that depend on this callback"""
        # FIXME either implement or wait for api to be able to handle reverse dependency lookup
        # FIXME in the future, with versions, it won't (?) be deletable, or the nodes that depend on this callback
        #   will have a fixed version of this callback

        # anyway, for now
        db_scopes = scopes()  # use global workspace
        deps = []
        nodes = db_scopes.list_scopes(scope="Node")
        for node in nodes:
            node_obj = db_scopes.Node[node["ref"]]
            for port_inst_name, port_inst in node_obj.PortsInst.items():
                for port_inst_in, port_inst_in_name in port_inst.In.items():
                    if port_inst_in.Callback.ref == self.ref:  # TODO check versions
                        deps.append((node["ref"], port_inst_name, port_inst_in_name))
            # delete cache for this node
            db_scopes.unload(scope="Node", ref=node["ref"])
            del node_obj

        deps_dict = dict()
        for dep in deps:
            try:
                l = deps_dict[dep[0]]
            except KeyError:
                l = deps_dict[dep[0]] = []
            l.append(
                {
                    "NodeInst": dep[1],
                }
            )

        return {
            "event": "warning",
            "data": {"numberDependencies": len(deps), "dependencies": deps_dict},
        }


Model.register_model_class("Callback", Callback)
