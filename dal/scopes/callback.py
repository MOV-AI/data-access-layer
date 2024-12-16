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
import sys
import inspect
import pkgutil
import pydoc
import importlib
from dal.movaidb import MovaiDB
from dal.scopes.scope import Scope


class Callback(Scope):
    """Callback class"""

    scope = "Callback"
    permissions = [*Scope.permissions, "execute"]

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Callback", name=name, version=version, new=new, db=db)

    def is_valid(self):
        # what is in db is valid to run
        return True

    def remove(self, force=False):
        if force:
            self.template_depends(force)
            super().remove()
            return {"event": "delete", "data": {}}

        return self.template_depends(force)

    def has_permission(self, user, permission, app_name):
        """Override has_permission for the Scope Callback"""
        has_perm = super().has_scope_permission(user, permission)
        if not has_perm:
            # Check if user has the Callback on the authorized Applications Callbacks list.
            # If the user has authorization on the Application that is calling the callback, then authorize.
            if app_name in user.get_permissions("Applications"):
                ca = Application(name=app_name)
                if ca.Callbacks and self.name in ca.Callbacks:
                    has_perm = True

        return has_perm

    @staticmethod
    def get_modules() -> list:
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
    def _get_modules() -> dict:
        """new, recursive way to get modules"""

        modules = {}

        # use to catch an exception below
        import rospkg.common

        """
        This kinda looks like:

        pkg1/
         |
         +  __init__.py
         \  mod_dred.py
        mod1.py


        {
            'pkg1' : {
                'isPkg' : True,
                'functions' : ['foo1','bar1'],
                'classes' : ['class1'],
                'constants' : ['ID1','factor1'],
                'modules' : {
                    'mod_dred' : {
                        'isPkg': False,
                        'functions' : ['bar2','foo2'],
                        'classes' : [],
                        'constants' : []
                        # no modules here
                    }
                }
            },
            'mod1' : {
                'isPkg' : False,
                'functions' : [],
                'constants' : [],
                'classes' : ['MegaClass']
                # again, no modules here
            }
        }

        """

        def expand_package(ret_dict: dict, pkg: pkgutil.ModuleInfo, parent: str = ""):
            """check package for nested modules"""
            path = pkg[0].path + "/" + pkg[1]

            # expand it
            this = parent + "." + pkg[1]
            if this[0] == ".":
                this = this[1:]

            # iterate contents of this package
            for x in pkgutil.iter_modules([path]):
                # ignore '_*' modules
                if x[1].startswith("_") or x[1] == "init_local_db":
                    continue

                # shouldn't be python2 for sure
                ret_dict[x[1]] = {"isPkg": x[2]}

                # always expand module
                v = expand_module(ret_dict[x[1]], this + "." + x[1])
                # and maybe expand package
                if x[2] and v:  # on error expanding module, completely ignore it
                    ret_dict[x[1]]["modules"] = {}
                    expand_package(ret_dict[x[1]]["modules"], x, this)

                if not v:
                    # remove it from the list if erroneous
                    del ret_dict[x[1]]

        def expand_module(ret_dict: dict, mod: str) -> bool:
            """get methods, classes and constants from the module

            return True on success
            return False on module not found or error parsing the module
            """

            i_mod = None
            try:
                i_mod = importlib.import_module(mod)
            except ModuleNotFoundError:
                # this is an actual error
                return False
            except:
                # this may actually not be an error ...
                # but we can't still work with it
                # so, acknowledge it exists
                # (this happens with API2.Scopes)
                return True

            try:
                # i_mod = importlib.import_module(mod)

                # now read its internals
                # dammed ros
                a_all = None
                try:
                    a_all = getattr(i_mod, "__all__", None)
                except:
                    # ros sends another exception instead of using default value...
                    # #python2
                    pass

                ret_dict["classes"] = []
                ret_dict["functions"] = []
                ret_dict["consts"] = []

                # FIXME probably needs optimizing, still figuring how to...
                # when intersecting the class/function/data list with the __all__ list

                # get classes
                for key, value in inspect.getmembers(i_mod, inspect.isclass):

                    # ignore __var__ like __these__
                    # probably simpler than re.match()
                    if key[:2] == "__" and key[-2:] == "__":
                        continue

                    if a_all is not None:
                        # if there is an __all__
                        # and it's advertised there
                        if key in a_all:
                            # add it
                            ret_dict["classes"].append(key)
                            # ignore the value tho, only need key
                    else:
                        # just add it
                        ret_dict["classes"].append(key)

                # get methods
                for key, value in inspect.getmembers(i_mod, inspect.isroutine):

                    # ignore __var__ like __these__
                    if key[:2] == "__" and key[-2:] == "__":
                        continue

                    if a_all is not None:
                        # if there is an __all__
                        # and it's advertised there
                        if key in a_all:
                            # add it
                            ret_dict["functions"].append(key)
                            # ignore the value tho, only need key
                    else:
                        # just add it
                        ret_dict["functions"].append(key)

                # get data/constants
                for key, value in inspect.getmembers(i_mod, pydoc.isdata):

                    # ignore __var__ like __these__
                    if key[:2] == "__" and key[-2:] == "__":
                        continue

                    if a_all is not None:
                        # if there is an __all__
                        # and it's advertised there
                        if key in a_all:
                            # add it
                            ret_dict["consts"].append(key)
                            # ignore the value tho, only need key
                    else:
                        # just add it
                        # or don't ?
                        ret_dict["consts"].append(key)

                # so it's done ?
                del i_mod
            except rospkg.common.ResourceNotFound:
                # ros throws this exception somewhere in inspect.getmembers
                # called on a ros (python2) module
                # which means we can't get the module members,
                # but still add to the list of modules
                return True  # early return
            except:  # something?
                return False
            return True

        # iterate every module found

        builtin_modules = [("", name, False) for name in sys.builtin_module_names]
        for x in list(pkgutil.iter_modules()) + builtin_modules:
            # now ...
            # x[0] -> FileFinder(path_where_modules_was_found)
            # x[1] -> module/package name
            # x[2] -> if it is a package (True=package,False=module)

            # this finds all modules, including python2, so we need to filter that

            # filter x[0].path for python2 (ignore those)
            # not anymore
            # if '/python2.' in x[0].path:
            #    # ignore this one
            #    continue

            # ignore _pkgs _starting _with '_'
            if x[1].startswith("_"):
                # nope
                continue

            # create the template dict
            modules[x[1]] = {"isPkg": x[2]}

            # i guess always expand module
            v = expand_module(modules[x[1]], x[1])

            # and maybe expand the package, if it's one
            if x[2] and v:
                # package
                modules[x[1]]["modules"] = {}
                expand_package(modules[x[1]]["modules"], x)

            if not v:  # on error
                del modules[x[1]]

        # not using re anymore
        del rospkg.common

        # and return it
        return modules

    @staticmethod
    def export_modules():
        """Get modules and save them to Layer1

        this takes about 4 seconds to run

        and prints a LOT of stuff to the terminal

        currently (14-10 on spawner) uses about 19kb of memory (?)
        """
        # useless

        root = Callback._get_modules()
        # +DEBUG
        """
        import json
        print(json.dumps(root,indent =  2))
        del json
        """
        # -DEBUG

        # and now save to database
        MovaiDB("local").set({"System": {"PyModules": {"Value": root}}})
        # python frees the class

        # nothing to return

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
        full_node_list = MovaiDB().search(
            {
                "Node": {
                    "*": {"PortsInst": {"*": {"In": {"*": {"Callback": self.name}}}}}
                }
            }
        )

        for node_key in full_node_list:
            node = MovaiDB().keys_to_dict([(node_key, "")])
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
                MovaiDB().set(node)
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
