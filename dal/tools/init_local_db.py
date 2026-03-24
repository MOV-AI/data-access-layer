"""Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Tiago Paulino (tiago@mov.ai) - 2020

Initialize redis local storage with:
    System:PortsData
"""
import os
import signal

# from dal.models.callback import Callback
from dal.models.message import Message
from dal.movaidb import MovaiDB
import json
from dal.scopes.system import System


def main():
    """initialize redis local db"""

    # Connect to DBs
    MovaiDB(db="global")
    MovaiDB(db="local")

    # Load data
    Message.export_portdata(db="local")

    # Temp fix for: https://movai.atlassian.net/browse/BP-1216
    # Comment out the full search and import of python modules
    # Callback.export_modules()

    # Here we upload the python modules that are already saved in the file
    # Get the path to the file
    # https://setuptools.readthedocs.io/en/latest/userguide/datafiles.html#accessing-data-files-at-runtime
    data_path = os.path.join(os.path.dirname(__file__), "python_imports.json")

    # This code is copy pasted from the Callback.export_modules() function
    try:
        # currently using the old api
        mods = System("PyModules", db="local")
    except Exception:  # pylint: disable=broad-except
        mods = System("PyModules", new=True, db="local")

    with open(data_path, "r") as f:
        mods.Value = json.load(f)
    ############################################################

    # TODO: this is a bit overkill,
    # we should change how we are getting all the python packages/modules (without actually executing)
    # export module is launching a set of processes that might run unwanted code => Security risk
    os.kill(os.getpid(), signal.SIGKILL)


if __name__ == "__main__":
    main()
