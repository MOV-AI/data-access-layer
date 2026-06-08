"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
import inspect
import sys
import copy
import time
import importlib
from os import getenv
from typing import TYPE_CHECKING, Any, Dict
from asyncio import CancelledError

from movai_core_shared.logger import Log
from movai_core_shared.exceptions import TransitionException

from dal.models.lock import Lock
from dal.models.nodeinst import NodeInst
from dal.models.var import Var
from dal.models.scopestree import ScopesTree, scopes

from dal.scopes.robot import Robot

if TYPE_CHECKING:
    from movai_core_enterprise.models.graphicscene import GraphicScene

# Check if enterprise modules are available
try:
    import movai_core_enterprise  # pylint: disable=unused-import

    enterprise = True
except ImportError:
    enterprise = False


LOGGER = Log.get_logger("spawner.mov.ai")


class LazyInstantiation:
    """Delay instantiation of an object until first use."""

    def __init__(self, cls, *args, **kwargs):
        self._cls = cls
        self._args = args
        self._kwargs = kwargs
        self._instance = None

    def _get_instance(self):
        if self._instance is None:
            self._instance = self._cls(*self._args, **self._kwargs)
        return self._instance

    def __getattr__(self, name):
        instance = self._get_instance()
        return getattr(instance, name)


class LazyModule:
    """Delay module/class import until first attribute access."""

    def __init__(self, module_path, class_name=None):
        self._module_path = module_path
        self._class_name = class_name
        self._cached = None

    def _load(self):
        if self._cached is None:
            module = importlib.import_module(self._module_path)
            self._cached = getattr(module, self._class_name) if self._class_name else module
        return self._cached

    def __getattr__(self, name):
        return getattr(self._load(), name)

    def __call__(self, *args, **kwargs):
        return self._load()(*args, **kwargs)


class UserFunctions:
    """Class that provides functions to the callback execution"""

    globals: Dict[str, Any]

    def __init__(
        self,
        _cb_name: str,
        _node_name: str,
        _port_name: str,
        _libraries: list,
        _message: str,
        _user="SUPER",
    ) -> None:
        """Init"""

        self.globals = {"run": self.run}
        self.cb_name = _cb_name
        self.node_name = _node_name

        self.load_libraries(_libraries)
        self.load_classes(_node_name, _port_name, _user)

    def load_classes(self, _node_name, _port_name, _user):
        _robot_id: str = UserCallback.robot().name

        class UserVar(Var):
            """Class for user to set and get vars"""

            def __init__(self, scope: str = "Node", robot_name=_robot_id):
                super().__init__(
                    scope=scope,
                    _robot_name=robot_name,
                    _node_name=_node_name,
                    _port_name=_port_name,
                )

        class UserLock(Lock):
            """Class for user to use locks"""

            def __init__(self, name, **kwargs):
                kwargs.update({"_node_name": _node_name, "_robot_name": _robot_id})
                super().__init__(name, **kwargs)

        if _user == "SUPER":
            logger = Log.get_callback_logger("GD_Callback", self.node_name, self.cb_name)
            self.globals.update(
                {
                    "scopes": scopes,
                    "Package": LazyModule("dal.scopes.package", "Package"),
                    "Message": LazyModule("dal.scopes.message", "Message"),
                    "Ports": LazyModule("dal.scopes.ports", "Ports"),
                    "Var": UserVar,
                    "Robot": UserCallback.robot(),
                    "FleetRobot": LazyModule("dal.scopes.fleetrobot", "FleetRobot"),
                    "logger": logger,
                    "PortName": _port_name,
                    "Callback": LazyModule("dal.scopes.callback", "Callback"),
                    "Lock": UserLock,
                    "print": self.user_print,
                    "Scene": LazyInstantiation(UserCallback.scene),
                    "NodeInst": NodeInst,
                    "Container": LazyModule("dal.scopes.container", "Container"),
                    "Configuration": LazyModule("dal.scopes.configuration", "Configuration"),
                }
            )

            if enterprise:
                self.globals.update(
                    {
                        "Alert": LazyModule("dal.scopes.alert", "Alert"),
                        "Annotation": LazyModule(
                            "movai_core_enterprise.models.annotation", "Annotation"
                        ),
                        "GraphicScene": LazyModule(
                            "movai_core_enterprise.models.graphicscene", "GraphicScene"
                        ),
                        "Layout": LazyModule("movai_core_enterprise.models.layout", "Layout"),
                        "metrics": LazyInstantiation(
                            LazyModule(
                                "movai_core_enterprise.message_client_handlers.metrics", "Metrics"
                            )
                        ),
                        "Task": LazyModule("movai_core_enterprise.scopes.task", "Task"),
                        "TaskEntry": LazyModule(
                            "movai_core_enterprise.models.taskentry", "TaskEntry"
                        ),
                        "TaskTemplate": LazyModule(
                            "movai_core_enterprise.models.tasktemplate", "TaskTemplate"
                        ),
                    }
                )

    def load_libraries(self, libraries):
        for lib in libraries:
            try:
                mod = importlib.import_module(libraries[lib].Module)
                try:
                    self.globals[lib] = getattr(mod, libraries[lib].Class)
                except TypeError:  # Class is not defined
                    self.globals[lib] = mod
            except CancelledError:
                raise CancelledError("cancelled task")
            except (ImportError, AttributeError, LookupError):
                LOGGER.error(
                    f"Import {lib} in callback blew up. Node: {self.node_name} Callback: {self.cb_name}",
                    exc_info=True,
                )
                # TODO We can't kill the node if callbacks blow up. Some callbacks are not critical.
                # sys.exit(1)

    def user_print(self, *args):
        """Method to redirect the print function into logger"""
        to_send = " ".join([str(arg) for arg in args])
        logger = Log.get_callback_logger("GD_Callback", self.node_name, self.cb_name)
        logger.debug(to_send)

    def run(self, cb_name, msg):
        """Run another callback from a callback"""
        callback = scopes.from_path(cb_name, scope="Callback")
        compiled_code = compile(callback.Code, cb_name, "exec")
        user = UserFunctions("", "", "", callback.Py3Lib, callback.Message)

        user.globals.update({"msg": msg})
        globais = user.globals

        exec(compiled_code, globais)


class UserCallback:
    """Callback class used by GD_Node to execute code

    Args:
        _cb_name: The name of the callback
        _node_name: The name of the node instance
        _port_name: The name of the input port
        _update: Real time update of the callback code
    """

    _robot = None
    _scene = None
    _user_functions_class = UserFunctions

    def __init__(
        self,
        _cb_name: str,
        _node_name: str,
        _port_name: str,
        _update: bool = False,
    ) -> None:
        self.name = _cb_name
        self.node_name = _node_name
        self.port_name = _port_name
        self.updated_globals = {}

        self.callback = ScopesTree().from_path(_cb_name, scope="Callback")

        self.compiled_code = compile(self.callback.Code, _cb_name, "exec")
        self.user = self._user_functions_class(
            _cb_name,
            _node_name,
            _port_name,
            self.callback.Py3Lib,
            self.callback.Message,
        )
        self.count = 0

        self._debug = eval(getenv("DEBUG_CB", "False"))

    @classmethod
    def robot(cls) -> Robot:
        if cls._robot is None:
            cls._robot = Robot()
        return cls._robot

    @classmethod
    def scene(cls) -> "GraphicScene":
        if cls._scene is None:
            scene_name = cls.robot().get_active_scene()
            if scene_name:
                try:
                    cls._scene = scopes.from_path(scene_name, scope="GraphicScene")
                except KeyboardInterrupt:
                    LOGGER.warning(
                        "[KILLED] Callback forcefully killed while initializing. It was trying to load Scene %s.",
                        scene_name,
                    )
                    sys.exit(1)
                except:
                    LOGGER.error("Scene %s was not found", scene_name)
        return cls._scene

    def execute(self, msg: Any = None) -> None:
        """Executes the code

        Args:
            msg: Message received in the callback
        """

        self.user.globals.update({"msg": msg})
        self.user.globals.update({"count": self.count})
        globais = copy.copy(self.user.globals)
        self.start(self.compiled_code, globais)
        self.count += 1
        self.updated_globals = globais
        if (
            "response" in globais
            and isinstance(globais["response"], dict)
            and "status_code" in globais["response"]
        ):
            self.updated_globals["status_code"] = globais["response"]["status_code"]

    def start(self, code, globais):
        """Executes the code

        Args:
            msg: Message received in the callback
        """
        try:
            t_init = time.perf_counter()
            if self._debug:
                import linecache

                linecache.cache[self.name] = (
                    len(self.callback.Code),
                    None,
                    self.callback.Code.splitlines(True),
                    self.name,
                )
            exec(code, globais)
            t_delta = time.perf_counter() - t_init
            if t_delta > 0.5:
                LOGGER.debug(
                    f"{self.node_name}/{self.port_name}/{self.callback.Label} took: {t_delta}"
                )
        except TransitionException:
            LOGGER.debug("Transitioning...")
            self.set_transitioning()
        except CancelledError:
            raise CancelledError("cancelled task")
        except KeyboardInterrupt:
            LOGGER.warning(
                f"[KILLED] Callback forcefully killed (node: {self.node_name}, callback={self.name})"
            )
            sys.exit(1)
        except Exception as e:
            # check if the exception is a ROSException (or an exception that
            # extends from ROSException) without having to import it
            if any(ecls.__name__ == "ROSException" for ecls in e.__class__.__mro__):
                LOGGER.warning(
                    f"[KILLED] Callback's ros protocol forcefully killed (node: {self.node_name}, callback={self.name})"
                )
                LOGGER.warning(f"Exception: {e}", exc_info=True)
                sys.exit(1)
            else:
                LOGGER.error(
                    f"Error in executing callback. Node: {self.node_name} Callback: {self.name}",
                    exc_info=True,
                )
                # TODO We can't kill the node if callbacks blow up. Some callbacks are not critical.
                # sys.exit(1)

    def set_transitioning(self):
        pass


class AsyncCallback:
    """Callback class used to execute user code

    Args:
        _cb_name: The name of the callback
        _node_name: The name of the node instance
        _port_name: The name of the input port
        _update: Real time update of the callback code
    """

    def __init__(
        self, _cb_name: str, _node_name: str, _port_name: str, _update: bool = False
    ) -> None:
        """Init"""
        self.name = _cb_name
        self.node_name = _node_name
        self.port_name = _port_name
        self.updated_globals = {}

        self.callback = ScopesTree().from_path(_cb_name, scope="Callback")

        self.compiled_code = compile(self.callback.Code, _cb_name, "exec")
        self.user = UserFunctions(
            _cb_name,
            _node_name,
            _port_name,
            self.callback.Py3Lib,
            self.callback.Message,
        )
        self.count = 0

        self._debug = eval(getenv("DEBUG_CB", "False"))

    async def execute(self, msg: Any = None) -> None:
        """Executes the code

        Args:
            msg: Message received in the callback
        Returns:
            Result from the callback function, if any
        """

        self.user.globals.update({"msg": msg})
        self.user.globals.update({"count": self.count})
        globais = copy.copy(self.user.globals)
        await self.start(self.compiled_code, globais)
        self.count += 1
        self.updated_globals = globais
        if (
            "response" in globais
            and isinstance(globais["response"], dict)
            and "status_code" in globais["response"]
        ):
            self.updated_globals["status_code"] = globais["response"]["status_code"]
            del globais["response"]["status_code"]

    async def start(self, code, globais):
        """Executes the code

        Args:
            msg: Message received in the callback
        """
        try:
            t_init = time.perf_counter()
            if self._debug:
                import linecache

                linecache.cache[self.name] = (
                    len(self.callback.Code),
                    None,
                    self.callback.Code.splitlines(True),
                    self.name,
                )
            exec(code, globais)
            if "start" in globais and inspect.iscoroutinefunction(globais["start"]):
                globais["response"] = await globais["start"]()
            t_delta = time.perf_counter() - t_init
            if t_delta > 0.5:
                LOGGER.debug(
                    f"{self.node_name}/{self.port_name}/{self.callback.Label} took: {t_delta}"
                )
        except TransitionException:
            LOGGER.debug("Transitioning...")
            self.set_transitioning()
        except CancelledError:
            raise CancelledError("cancelled task")
        except KeyboardInterrupt:
            LOGGER.warning(
                f"[KILLED] Callback forcefully killed (node: {self.node_name}, callback={self.name})"
            )
            sys.exit(1)
        except Exception:
            LOGGER.error(
                f"Error in executing callback. Node: {self.node_name} Callback: {self.name}",
                exc_info=True,
            )
            # TODO We can't kill the node if callbacks blow up. Some callbacks are not critical.
            # sys.exit(1)

    def set_transitioning(self):
        pass
