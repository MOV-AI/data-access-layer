import pydantic
import importlib
import inspect
import pkgutil
import sys
import rospkg
from typing import Union, Optional, Dict, List
from .base_model import MovaiBaseModel
from pydantic import StringConstraints
from typing_extensions import Annotated

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
            # TODO change old system
            from dal.scopes.system import System

            # currently using the old api
            mods = System("PyModules", db="local")  # scopes('local').System['PyModules', 'cache']
        except Exception:  # pylint: disable=broad-except
            mods = System(
                "PyModules", new=True, db="local"
            )  # scopes('local').create('System', 'PyModules')

        mods.Value = data

        del mods, data  # not that it's gonna make a difference ...

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


if __name__ == "__main__":
    r = Callback(
        **{
            "Callback": {
                "fleetDashboard.statistics": {
                    "Code": "'''\n    Copyright (C) Mov.ai  - All Rights Reserved\n    Unauthorized copying of this file, via any medium is strictly prohibited\n    Proprietary and confidential\n\n    This is a sample statistics callback which is responsible for getting all robots\n    information such as distance travelled, number of carts delivered etc.\n\n    This callback is called for the following functions\n        -> cache_session_stats    : called everytime the system was running (right side in top bar) and it stops to get the last start/end time and update the cache in redis\n        -> last_session_stats     : called once to get the cached statistics values\n        -> get_stats             : called every 10s to refresh the data in the charts\n    It's important to remark that if the system is not running in FleetDashboard app, the get_stats function is not going to be called\n\n    DEBUG INFO:\n        1) If it's necessary to send any error message back to the UI, it's necessary to add an \"error\" property in the response object returned\n        2) To debug 'cache_session_stats', you need to start and stop the system in FleetDashboard\n            2.1) It will call this function to update the cached statistics data\n        3) To debug 'last_session_stats', you just need to refresh the page\n            3.1) It will call this function to fetch the cached values\n        4) To debug 'get_stats', you need to have the system running in FleetDashboard\n            4.1) It will automatically call to fetch new results to refresh data in charts (every 10s)\n'''\nfrom datetime import date, datetime\n\n# parameters\nCONFIG_NAME = \"project\"\nMANAGER_DEFAULT = \"manager\"\nTIMEZONE_DEFAULT = \"Europe/Berlin\"\n\ntry:\n    project_config = Configuration(CONFIG_NAME).get_value()\n    timezone = project_config['check_work_conditions']['timezone']\n    manager = project_config['manager_name']\nexcept Exception as e:\n    timezone = TIMEZONE_DEFAULT\n    manager = MANAGER_DEFAULT\n    logger.error(f\"Error in configuration {CONFIG_NAME}\", e)\n\n# instanciate database vars\ngvar = Var('Global')\n\n# get all fleet robots except manager\nrobots = set([FleetRobot(robot).RobotName for robot in Robot.get_all()]) - {manager}\n\n# get timezone\ntz = pytz.timezone(timezone)\n\n# consts\nBUBBLE_1 = \"bubble1\"\nBUBBLE_2 = \"bubble2\"\nBAR_1 = \"bar1\"\nBAR_2 = \"bar2\"\nLINE_CHART = \"lineChart\"\n\nGLOBAL_BLACKLIST = []\n\n#  format values from global var (current_date) and get today's date\nuse_old_format = isinstance(gvar.current_date, date)\ntoday_date = datetime.now(tz).date()\nif use_old_format or gvar.current_date is None:\n    current_date = gvar.current_date\nelse:\n    current_date = datetime.date(datetime.strptime(gvar.current_date, '%Y-%m-%d'))\n# reset fleet variables on new day\nif current_date is None or current_date < today_date:\n    gvar.current_date = today_date.strftime(\"%Y-%m-%d\")\n    logger.debug('Resetting day vars')\n    for robot in robots:\n        fvar = Var('Fleet', robot)\n        fvar.time_today = 0\n        fvar.kms_today = 0\n        fvar.carts_today = 0\n\ndef clean_statistics(stats):\n    \"\"\"\n        Remove each statistics related to robot that are not well defined in Redis\n        Or was already removed\n\n        Returns:\n            dict:Individual statiscts from valid robots only\n    \"\"\"\n    for index, stat in enumerate(stats):\n        if not stat['robot'] or stat['robot'] not in robots or stat['robot'] in GLOBAL_BLACKLIST:\n            stats.pop(index)\n    return stats\n\ndef validate_statistics(statistics):\n    \"\"\"\n        Remove statistics related to robot that are not well defined in Redis\n        Or was already removed\n\n        Returns:\n            dict:Statiscts from valid robots only\n    \"\"\"\n    valid_statistics = {}\n    try:\n        valid_statistics[BUBBLE_1] = clean_statistics(statistics[BUBBLE_1])\n        valid_statistics[BUBBLE_2] = clean_statistics(statistics[BUBBLE_2])\n        valid_statistics[BAR_1] = clean_statistics(statistics[BAR_1])\n        valid_statistics[BAR_2] = clean_statistics(statistics[BAR_2])\n        statistics.update(valid_statistics)\n    except KeyError:\n        logger.debug(\"lastSessionStats Var not found\", ui=True)\n    return statistics\n\ndef time_km_per_robot_today():\n    \"\"\"\n        Time in operation and kms per robot today\n        Use case: \n            Populate \"Time in operation and Kms Today\" chart (bubble1)\n        \n        Returns:\n            array:List of robots with its kilometers/time data today\n    \"\"\"\n    time_kms = []\n    for robot in robots:\n        try:\n            fvar = Var('Fleet', robot)\n            time = fvar.time_today\n            kms = fvar.kms_today\n        except Exception:\n            time = 0\n            kms = 0\n        time_kms.append({'x': kms, 'y': time, 'robot': robot})\n    return time_kms\n\ndef time_km_per_robot():\n    \"\"\"\n        Time in operation and kms per robot lifelong\n        Use case: \n            Populate \"Time in operation and Kms\" chart (bubble2)\n        \n        Returns:\n            array:List of robots with its kilometers/time data accumulated\n    \"\"\"\n    time_kms = []\n    for robot in robots:\n        try:\n            fvar = Var('Fleet', robot)\n            time = fvar.time_lifetime\n            kms = fvar.kms_lifetime\n        except Exception:\n            time = 0\n            kms = 0\n        time_kms.append({'x': kms, 'y': time, 'robot': robot})\n    return time_kms\n\ndef carts_per_robot():\n    \"\"\"\n        Carts pulled per robot accumulated\n        Use case: \n            Populate \"Total carts per Robot\" chart (bar2)\n\n        Returns:\n            array:List of robots with its quantity of pulled carts accumulated\n    \"\"\"\n    carts = []\n    for robot in robots:\n        try:\n            carts_lifetime = Var('Fleet', robot).carts_lifetime\n            carts.append({'data': carts_lifetime, 'robot': robot})\n        except Exception:\n            carts.append({'data': 0, 'robot': robot})\n    return carts\n\ndef carts_per_robot_today():\n    \"\"\"\n        Carts pulled per robot today\n        Use case: \n            Populate \"Total carts per Robot Today\" chart (bar1)\n\n        Returns:\n            array:List of robots with its quantity of pulled carts today\n    \"\"\"\n    carts = []\n\n    for robot in robots:\n        try:\n            carts_today = Var('Fleet', robot).carts_today\n            carts.append({'data': carts_today, 'robot': robot})\n        except Exception:\n            carts.append({'data': 0, 'robot': robot})\n        \n    return carts\n\ndef last_session_stats(blacklist):\n    \"\"\"\n        Get last session data redis var last_session_stats \n        Use cases:\n            Returns last session statistics values in cache\n        \n        Raises:\n            Exception: If last_session_stats doesn't exists in global var in redis\n        \n        Returns:\n            Last session statistics values in cache\n    \"\"\" \n    \n    GLOBAL_BLACKLIST = blacklist\n\n    response = {'success': False}\n\n    try:\n        response['result'] = Var('global').get('lastSessionStats') or {}\n        response['result'] = validate_statistics(response['result'])\n        response['success'] = True\n\n    except Exception as e:\n        logger.error(e)\n        raise e\n\n    return response\n\ndef cache_session_stats(startTimeVar, endTimeVar, blacklist):\n    \"\"\" \n        Get the session cached statistics values\n        Use case: \n            Whenever the system stops, update cache in redis and returns last start/end time to calculate 'Last Session Duration' value\n        \n        Parameters:\n            start_time_var (str):The name of the start_time_var variable in redis\n            end_time_var (str):The name of the end_time_var variable in redis\n        \n        Raises:\n            Exception: If variable names doesn't exists in redis\n        \n        Returns:\n            Object containing start/end time of last session and last statistics data in cache\n    \"\"\"\n    response = {'success': False}\n\n    try:\n        cache = get_stats(blacklist)\n        response = cache.get('result', {})\n        start_time = Var('global').get(startTimeVar)\n        end_time = Var('global').get(endTimeVar)\n\n        response.update({endTimeVar: end_time, startTimeVar: start_time, 'success': True })\n\n        Var('global').lastSessionStats = response\n\n    except Exception as e:\n        logger.error(e)\n        raise e\n\n    return response\n\ndef line_chart():\n    \"\"\" \n        Number of carts per robot during session (line chart)\n        Use cases: \n            Populate main chart with carts_per_robot and total_timeseries variables\n            Populate 'Delivered Carts' with deliveriesNumber variable \n        \n        Returns:\n            Object containing overall data to build line chart and fill deliveriesNumber\n    \"\"\"\n\n    response = {\"success\": False}\n\n    metrics_name = 'numberOfDeliveries'\n    carts_per_robot = {}   # {<robot id>: <robot data>, }\n    total_timeseries = [] # [ {'t': <timestamp>, 'y': <accumulated delivered carts>}]\n    totals_per_robot = {}  # {<robot id>: <total carts delivered>}\n    totals = 0\n\n    # series format: {<robot name>: <robot data>}\n    # robot data format: [ {'t': <timestamp>, 'y': <accumulated delivered carts>}]\n\n    try:\n        # session start time; gives last hour by default\n        start_time = Var('global').get('startTime') or (time.time() - 3600)\n        entries = metrics.get_metrics(metrics_name)\n        entries.reverse()\n\n        # add first point\n        total_timeseries.append({'t': start_time, 'y': 0})\n\n        for entry in entries:\n            _robot = entry.get(\"robot\")\n            _timestamp = entry.get(\"time\")\n            _value = int((entry.get(\"v\", 1) or 1)) # or 1 - in case value is None\n\n            if _timestamp >= start_time:\n\n                # calculate carts per robots\n                totals_per_robot.update({_robot: totals_per_robot.get(_robot, 0) + _value})\n                _values = carts_per_robot.setdefault(_robot, [{'t': start_time, 'y': 0}])\n                _values.append({'t': _timestamp, 'y': totals_per_robot.get(_robot)})\n\n                # update totals\n                totals = totals + _value\n                total_timeseries.append({'t': _timestamp, 'y': totals})\n\n        # add final point\n        current_time = time.time()\n\n        for _robot, _values in carts_per_robot.items():\n            _values.append({'t': current_time, 'y': totals_per_robot.get(_robot, 0)})\n\n        total_timeseries.append({'t': current_time, 'y': totals})\n\n        # response\n        response = {\"carts_per_robot\": carts_per_robot, \"total_timeseries\": total_timeseries, \"deliveriesNumber\": totals}\n\n    except Exception as e:\n        logger.error(e)\n        raise e\n\n    return response\n\ndef get_stats(blacklist):\n    \"\"\"\n        Get statistics to populate charts\n        Use case:\n            Gather information to populate/refresh values in charts in statistics page\n        \n        Parameters:\n            blacklist (array):The list of robots names to be used in line_chart function\n\n        Returns:\n            Collects results from internal functions to return data to populate charts\n    \"\"\"\n    GLOBAL_BLACKLIST = blacklist\n    bar1 = carts_per_robot_today()\n    bar2 = carts_per_robot()\n    bubble1 = time_km_per_robot_today()\n    bubble2 = time_km_per_robot()\n\n    # Compose response output \n    output = {}\n    output[BUBBLE_1] = bubble1\n    output[BUBBLE_2] = bubble2\n    output[BAR_1] = bar1\n    output[BAR_2] = bar2\n    output[LINE_CHART] = line_chart()\n\n    response = {\"success\": True}\n    response.update({\"result\": validate_statistics(output)})\n\n    return response\n\n# Callback functions routes\nroutes = {\n    \"getStats\": get_stats,\n    \"lastSessionStats\": last_session_stats,\n    'cacheSessionStats': cache_session_stats\n}\n\ntry:\n    response = {\"success\": False}\n\n    # get request arguments to pass to function\n    args = msg.get(\"args\", {})\n\n    # call function\n    result = routes[msg[\"func\"]](**args)\n    response.update(result)\n\nexcept Exception as e:\n    response = {\"success\": False, \"error\": str(e)}\n    logger.error(response)",
                    "Info": "",
                    "Label": "fleetDashboard.statistics",
                    "LastUpdate": {"date": "18/07/2022 at 16:00:43", "user": "movai"},
                    "Message": "",
                    "Py3Lib": {
                        "pytz": {"Class": False, "Module": "pytz"},
                        "time": {"Class": False, "Module": "time"},
                    },
                    "User": "movai",
                    "Version": "__UNVERSIONED__",
                    "VersionDelta": {},
                }
            }
        }
    )
    r.model_dump()
    pk = r.save()
    """
    # because Label is string, the 5 will be converted automatically to string "5"
    r.Label = 5
    pk = r.save()

    start = time.time()
    callbacks = Callback.select(ids=[pk])
    print(callbacks)
    cs = Callback.select()
    print("$$$$$$$$$$$$$$$$$$$")
    print(cs)
    if callbacks:
        callback: Callback = callbacks[0]
        print(callback.model_dump())
        end = time.time()
        print(f"Searching and Object Creation took {(end-start)*1000}ms")

        start = time.time()
        print("Fetching Data")
        print(
            callback.Code,
            callback.Info,
            callback.Label,
            callback.Message,
            callback.LastUpdate,
            callback.Version,
            callback.Py3Lib,
        )
        end = time.time()
        print(f"Fetching Fields (after object Creation) took {(end - start) * 1000}ms")

    print(Callback("annotations_init"))
    """
    """
    print("====================================================")
    print("the old ugly Scopes\n")

    from deprecated.api.models.callback import Callback as ScopesCallback

    start = time.time()
    callback = ScopesCallback("Choose_DS_start")
    end = time.time()
    print(f"Searching and Object Creation took {(end-start)*1000}ms")

    start = time.time()
    print("Fetching Data")
    print(
        callback.Code,
        callback.Info,
        callback.Label,
        callback.Message,
        callback.LastUpdate,
        callback.Version,
        callback.User,
    )
    end = time.time()
    print(f"Fetching Fields (after object Creation) took {(end - start) * 1000}ms")

    print("====================================================")
    print("the Models mechanism\n")

    from movai.models.callback import Callback as ModelsCallback

    start = time.time()
    callback = ModelsCallback("Choose_DS_start")
    end = time.time()
    print(f"Searching and Object Creation took {(end-start)*1000}ms")

    start = time.time()
    print("Fetching Data")
    print(
        callback.Code,
        callback.Info,
        callback.Label,
        callback.Message,
        callback.LastUpdate,
        callback.Version,
        callback.User,
    )
    end = time.time()

    print(f"Fetching Fields (after object Creation) took {(end - start) * 1000}ms")
    """
