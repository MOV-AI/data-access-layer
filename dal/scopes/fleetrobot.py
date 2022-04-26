"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module that implements Robot namespace
"""
import pickle
from .scope import Scope


class FleetRobot(Scope):
    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Robot", name=name, version=version, new=new, db=db)

    def send_cmd(self, command, *, flow=None, node=None, port=None, data=None) -> None:
        """Send an action command to the Robot"""
        to_send = {}
        for key, value in locals().items():
            if value is not None and key in ("command", "flow", "node", "port", "data"):
                to_send.update({key: value})

        to_send = pickle.dumps(to_send)

        self.Actions.append(to_send)
