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
import pydoc
import sys
from typing import Any, Dict, List
import rospkg

from movai_core_shared.logger import Log

from dal.scopes.scopestree import scopes
from dal.scopes.system import System

from dal.models.model import Model


logger = Log.get_logger('')


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

            # logger.debug('Classes:\n', [x[0] for x in classes])

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

            # logger.debug('Functions:\n', [x[0] for x in funcs])

            data = []
            for key, value in inspect.getmembers(object, pydoc.isdata):
                if pydoc.visiblename(key, all, object):
                    data.append((key, value))

            # logger.debug('Data:\n', [x[0] for x in data])

            # modpkgs = {}
            modpkgs_names = set()
            if hasattr(object, "__path__"):
                for _, modname, _ in pkgutil.iter_modules(object.__path__):
                    modpkgs_names.add(modname)
                    # modpkgs[modname] = Callback.get_methods(module+'.'+modname)

            # logger.debug('Modules:\n', list(modpkgs_names))

            # Detect submodules as sometimes created by C extensions
            """
            submodules = []
            for key, value in inspect.getmembers(object, inspect.ismodule):
                if value.__name__.startswith(module + '.') and key not in modpkgs_names:
                    submodules.append(key)
            if submodules:
                submodules.sort()

            logger.debug('Submodules:\n', submodules)
            """

            methods = {
                "modules": list(modpkgs_names),
                "classes": [x[0] for x in classes],
                "functions": [x[0] for x in funcs],
                "consts": [x[0] for x in data]
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

    # ported blindly
    @staticmethod
    def _get_modules() -> dict:
        """new, recursive way to get modules

        This kinda looks like:

        pkg1/
         |
         +  __init__.py
         \\  mod_dred.py
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

        modules = {}

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
                logger.debug(f"Adding nested module {x[1]}")
                if x[1].startswith("_") or x[1] == 'init_local_db' or x[1] == 'tf_monitor':
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
            if x[1].startswith("_") or x[1] == 'init_local_db':
                # nope
                logger.debug(f"Skipping module {x[1]}")

                continue
            logger.debug(f"Adding module {x[1]}")
            # create the template dict
            modules[x[1]] = {"isPkg": x[2]}

            # i guess always expand module
            v = expand_module(modules[x[1]], x[1])

            # and maybe expand the package, if it's one
            if x[2] and v:
                # package
                # logger.debug(f"expanding pack {x[0]},{x[1]}")
                modules[x[1]]["modules"] = {}
                expand_package(modules[x[1]]["modules"], x)

            if not v:  # on error
                del modules[x[1]]

        # and return it
        logger.debug(f"Found {len(modules)} modules")
        return modules

    @staticmethod
    def export_modules() -> None:
        """Get modules and save them to db (System)

        this takes about 4 seconds to run

        and prints a LOT of stuff to the terminal

        currently (14-10 on spawner) uses about 19kb of memory (?)
        """

        data = Callback._get_modules()

        try:
            # currently using the old api
            mods = System(
                "PyModules", db="local"
            )  # scopes('local').System['PyModules', 'cache']
        except Exception:  # pylint: disable=broad-except
            mods = System(
                "PyModules", new=True, db="local"
            )  # scopes('local').create('System', 'PyModules')

        mods.Value = data

        del mods, data  # not that it's gonna make a difference ...

    @staticmethod
    def fetch_modules_api() -> Dict:
        """to be called from rest api"""
        try:
            return System(
                "PyModules", db="local"
            ).Value  # scopes('local').System['PyModules', 'cache'].Value
        except Exception:  # pylint: disable=broad-except
            # non existent yet
            return {}

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
