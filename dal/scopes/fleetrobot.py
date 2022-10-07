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
from enum import Enum
from threading import Timer

from .scope import Scope
from dal.models.var import Var

RECOVERY_TIMEOUT_IN_SECS = 15
RECOVERY_STATE_KEY = "recovery_state"
RECOVERY_RESPONSE_KEY = "recovery_response"


class RecoveryStates(Enum):
    """Class for keeping recovery states. Values are stored in recovery_state fleet variable."""

    READY: str = "READY"
    IN_RECOVERY: str = "IN_RECOVERY"
    PUSHED: str = "PUSHED"
    NOT_AVAILABLE: str = "NOT_AVAILABLE"


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

    def trigger_recovery(self):
        """Set Var to trigger Recovery Robot"""
        var_scope = Var(scope="fleet", _robot_name=self.name)
        
        # TODO: To be refactored to use shared ENUM for recovery state
        value = RecoveryStates.PUSHED.name

        setattr(var_scope, RECOVERY_STATE_KEY, value)
        
        # If the state doesn't change after 15 secs, set a VAR to send a message to the interface
        timeout = Timer(RECOVERY_TIMEOUT_IN_SECS, self._recovery_timeout)
        timeout.start()


    def _recovery_timeout(self):
        """Handle recovery fail on timeout"""
        var_scope = Var(scope="fleet", _robot_name=self.name)
        recovery_state = var_scope.get(RECOVERY_STATE_KEY)

        if recovery_state == RecoveryStates.PUSHED.name:
            response = {
                "success": False,
                "message": "Failed to recover robot"
            }
            var_scope.set(RECOVERY_RESPONSE_KEY, response)
            var_scope.set(RECOVERY_STATE_KEY, RecoveryStates.NOT_AVAILABLE.name)
