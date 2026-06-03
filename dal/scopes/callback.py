"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module that implements a Callback scope class
   https://github.com/python/cpython/blob/master/Lib/pydoc.py
"""
import inspect
import pkgutil
import importlib

from dal.movaidb import MovaiDB
from dal.scopes.scope import Scope
from dal.scopes.application import Application
from dal.models.acl import ResourceType, ApplicationsType


class Callback(Scope):
    """Callback class"""

    scope = "Callback"
    permissions = [*Scope.permissions, "execute"]

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Callback", name=name, version=version, new=new, db=db)

    @staticmethod
    def user_can_execute(user, callback_name: str = "") -> bool:
        """Check if user has permission to execute a callback.

        Args:
            user (BaseUser): The user object to check permissions for.
            callback_name (str): Optional specific callback name to check

        Returns:
            bool: True if user can execute the callback, False otherwise

        Note:
            TODO Remove after migration to endpoints - this exists because
            frontend apps execute callbacks directly.
        """

        # Allow running callbacks from allowed applications
        for app_name in [app.value for app in ApplicationsType]:
            if user.has_permission(ResourceType.Applications.value, app_name):
                try:
                    ca = Application(name=app_name)
                    if ca.Callbacks and callback_name in ca.Callbacks:
                        return True
                except Exception:
                    continue

        return False

    def is_valid(self):
        # what is in db is valid to run
        return True

    def remove(self, force=False):
        if force:
            self.template_depends(force)
            super().remove()
            return {"event": "delete", "data": {}}

        return self.template_depends(force)

    @staticmethod
    def get_modules() -> list:
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

    @staticmethod
    def get_methods(module: str) -> dict:
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

            # print('Classes:\n', [x[0] for x in classes])

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

            # print('Functions:\n', [x[0] for x in funcs])

            data = []
            for key, value in inspect.getmembers(object, pydoc.isdata):
                if pydoc.visiblename(key, all, object):
                    data.append((key, value))

            # print('Data:\n', [x[0] for x in data])

            # modpkgs = {}
            modpkgs_names = set()
            if hasattr(object, "__path__"):
                for _, modname, _ in pkgutil.iter_modules(object.__path__):
                    modpkgs_names.add(modname)
                    # modpkgs[modname] = Callback.get_methods(module+'.'+modname)

            # print('Modules:\n', list(modpkgs_names))

            # Detect submodules as sometimes created by C extensions
            """
            submodules = []
            for key, value in inspect.getmembers(object, inspect.ismodule):
                if value.__name__.startswith(module + '.') and key not in modpkgs_names:
                    submodules.append(key)
            if submodules:
                submodules.sort()

            print('Submodules:\n', submodules)
            """

            methods = {
                "modules": list(modpkgs_names),
                "classes": [x[0] for x in classes],
                "functions": [x[0] for x in funcs],
                "consts": [x[0] for x in data],
            }

            return methods
        except:
            print("Cannot import Module", module)
            return {}

    @staticmethod
    def get_full_modules() -> dict:
        module_description = {}

        mods = Callback.get_modules()
        for module in mods:
            # filter modules
            if module.startswith("_"):
                # ignore module
                continue
            module_description[module] = Callback.get_methods(module)

        return module_description

    @staticmethod
    def fetch_modules_api():
        """Retrieve saved modules from Layer1, called from REST API"""

        mods = MovaiDB("local").get({"System": {"PyModules": "**"}})
        # [0] -> result dict
        # [1] -> "error" string
        # TODO possibly check error string

        return mods["System"]["PyModules"]["Value"]

    def template_depends(self, force=False):
        # this will give a list of tuples (node_name, node_inst_name, iport_name)
        replaced_cbs = []
        full_node_list = self._movai_db_global.search(
            {"Node": {"*": {"PortsInst": {"*": {"In": {"*": {"Callback": self.name}}}}}}}
        )

        for node_key in full_node_list:
            node = self._movai_db_global.keys_to_dict([(node_key, "")])
            for flow in node["Node"]:
                node_name = flow
            for name in node["Node"][node_name]["PortsInst"]:
                node_inst_name = name
            for iport in node["Node"][node_name]["PortsInst"][node_inst_name]["In"]:
                iport_name = iport

            if force:
                node["Node"][node_name]["PortsInst"][node_inst_name]["In"][iport_name][
                    "Callback"
                ] = "null_callback"
                self._movai_db_global.set(node)
                return "True"

            replaced_cbs.append((node_name, node_inst_name, iport_name))

        if not replaced_cbs:
            super().remove()
            return {
                "event": "delete",
                "data": {"numberDependencies": 0, "dependencies": {}},
            }

        dependencies = {}

        for elem in replaced_cbs:
            try:
                dependencies[elem[0]].append({"NodeInst": elem[1], "Port": elem[2]})
            except:
                dependencies.update({elem[0]: []})
                dependencies[elem[0]].append({"NodeInst": elem[1], "Port": elem[2]})

        to_return = {
            "event": "warning",
            "data": {
                "numberDependencies": len(set(replaced_cbs)),
                "dependencies": dependencies,
            },
        }

        return to_return
