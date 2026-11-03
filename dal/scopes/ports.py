"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""

import json
import os

from dal.scopes.scope import Scope
from dal.utils.project_metadata import ProjectSource, from_path
from movai_core_shared.consts import (
    TRANSITION_TYPE,
    ROS1_NODELETCLIENT,
    ROS1_NODELETSERVER,
)

from movai_core_shared.logger import Log

LOGGER = Log.get_logger(__name__)


class Ports(Scope):
    """Ports model"""

    scope = "Ports"

    def __init__(self, name, version="latest", new=False, db="global"):
        """Initializes the object"""

        super().__init__(scope="Ports", name=name, version=version, new=new, db=db)

    def is_transition(self, port_type: str, port_name: str) -> bool:
        """Check if a port is of type transition"""

        port = getattr(self, port_type)[port_name]

        if (
            port.Protocol == TRANSITION_TYPE["Protocol"]
            and port.Transport == TRANSITION_TYPE["Transport"]
        ):
            return True

        return False

    def is_nodelet_client(self) -> bool:
        """Returns True if the port is a nodelet client"""
        return self.Template == ROS1_NODELETCLIENT

    def is_nodelet_server(self) -> bool:
        """Returns True if the port is a nodelet server"""
        return self.Template == ROS1_NODELETSERVER

    @classmethod
    def import_metadata(cls, names, source: ProjectSource, recursive=False):
        ret = []
        scope_name = cls.__name__

        files = source.get_files(scope_name, names)
        for name, file_path in files:
            json_data = source._read_json(file_path)

            for name in json_data[scope_name]:
                data = {"Ports": {name: json_data["Ports"][name]}}
                ret.append((name, data, file_path, None))

        return ret

    @classmethod
    def export_metadata(cls, names, recursive=False):
        failed = []
        exported = {}
        scope_name = cls.__name__

        for name in names:
            name = from_path(name)

            first_part = name.split("/", 1)[0]
            json_path = os.path.join(scope_name, f"{first_part}.json")

            try:
                obj = cls(name)  # pylint: disable=no-value-for-parameter
            except Exception as e:
                LOGGER.error(f"Can't find {scope_name}:{name} - (Exc: {e})")
                failed.append(
                    {
                        "scope": scope_name,
                        "name": name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )

            data = json.loads(cls.clean_data(obj.get_dict()))

            # Remove Info from each port.
            for port in data.get("Ports", {}).values():
                port.pop("Info", None)

            if json_path not in exported:
                exported[json_path] = {}

            # Merge metadata entries into the existing structure.
            for key, value in data.items():
                if isinstance(value, dict):
                    exported[json_path].setdefault(key, {}).update(value)
                else:
                    exported[json_path][key] = value

        return {
            path: json.dumps(data, sort_keys=True, indent=4) for path, data in exported.items()
        }, failed
