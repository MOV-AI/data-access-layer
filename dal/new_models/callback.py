import pydantic
import importlib
import inspect
import pkgutil
import sys
import rospkg
from typing import Union, Optional, Dict, List
from .base import MovaiBaseModel
from pydantic import StringConstraints
from typing_extensions import Annotated
from movai_core_shared.exceptions import DoesNotExist

ValidStr = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z_]+$")]
ValidStrNums = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")]


class Py3LibValue(pydantic.BaseModel):
    Class: Union[pydantic.types.StrictStr, bool] = None
    Module: str


class Callback(MovaiBaseModel):
    Code: Optional[str] = None
    Message: Optional[str] = None
    Py3Lib: Optional[Dict[ValidStrNums, Py3LibValue]] = {}

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Code", "Message", "Py3Lib"]

    @staticmethod
    def export_modules(jump_over_modules=None) -> None:
        """Get modules and save them to db (System)

        this takes about 4 seconds to run

        and prints a LOT of stuff to the terminal

        currently (14-10 on spawner) uses about 19kb of memory (?)
        Args:
            jump_over_modules (list): the list of modules not to expand
        """
        if jump_over_modules is None:
            jump_over_modules = ["scipy", "twisted"]

        data = Callback._get_modules(jump_over_modules)

        try:
            from .system import System
            mods = System("PyModules", db="local")
        except DoesNotExist:  # pylint: disable=broad-except
            mods = System.model_validate({"System": {"PyModules": {}}})

        mods.Value = data
        mods.save(db="local")

    # from old callback models
    @staticmethod
    def _get_modules(jump_over_modules) -> dict:
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
        Args:
            jump_over_modules (list): the list of modules not to expand

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
                if x[1].startswith("_") or x[1] == "init_local_db" or x[1] == "tf_monitor":
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
        for x in set(list(pkgutil.iter_modules()) + builtin_modules):
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
            if x[1].startswith("_") or x[1] == "init_local_db":
                # nope

                continue
            # create the template dict
            modules[x[1]] = {"isPkg": x[2]}

            # i guess always expand module
            v = expand_module(modules[x[1]], x[1])
            if x[1] in jump_over_modules:
                continue

            # and maybe expand the package, if it's one
            if x[2] and v:
                # package
                modules[x[1]]["modules"] = {}
                expand_package(modules[x[1]]["modules"], x)

            if not v:  # on error
                del modules[x[1]]

        # and return it
        return modules
