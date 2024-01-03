"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
from dal.movaidb import MovaiDB

SCOPES = ["callback", "node", "flow", "robot", "fleet", "global"]


class Var:
    """Class for user to write and read vars"""

    def __init__(self, scope: str = "Node", _robot_name="", _node_name="", _port_name=""):
        if scope.lower() not in SCOPES:
            scop = str(SCOPES)[1:-1]
            raise Exception("'" + scope + "' is not a valid scope. Choose between: " + scop)

        self.__dict__["scope"] = scope.lower()
        self.__dict__["_robot_name"] = _robot_name
        self.__dict__["_node_name"] = _node_name
        self.__dict__["_port_name"] = _port_name

    def __setattr__(self, name, value, expire: float = None):
        scope, prefix = self.__get_scope()

        milis = int((expire) * 1000) if expire else None
        MovaiDB(scope).set(
            {"Var": {self.scope: {"ID": {prefix + name: {"Value": value}}}}}, px=milis
        )

    def __getattr__(self, name):
        scope, prefix = self.__get_scope()
        try:
            return MovaiDB(scope).get_value(
                {"Var": {self.scope: {"ID": {prefix + name: {"Value": ""}}}}}, search=False
            )
        except KeyError:
            return None

    def __delattr__(self, name):
        try:
            scope, prefix = self.__get_scope()
            MovaiDB(scope).delete({"Var": {self.scope: {"ID": {prefix + name: {"Value": ""}}}}})
            return True
        except:
            return False

    def set(self, name, value, expire: float = None):
        """Same as setattr"""
        self.__setattr__(name, value, expire)

    def get(self, name):
        """Same as getattr"""
        return getattr(self, name)

    def delete(self, name):
        """Same as delattr"""
        return delattr(self, name)

    def __get_scope(self):
        """Get the Local or Global Scope"""
        if self.scope in ("fleet", "global"):
            scope = "global"
        else:
            scope = "local"

        prefixes = {
            "callback": self._node_name + "@" + self._port_name + "@",
            "node": self._node_name + "@",
            "robot": "@",
            "flow": "flow@",
            "fleet": self._robot_name + "@",
            "global": "@",
        }
        prefix = prefixes.get(self.scope, "@")
        return scope, prefix

    @staticmethod
    def delete_all(scope: str = "Node", _robot_name="", _node_name="", _port_name=""):
        """Delete all variables of a certain scope"""

        if scope.lower() not in SCOPES:
            scop = str(SCOPES)[1:-1]
            raise Exception("'" + scope + "' is not a valid scope. Choose between: " + scop)
        scope = scope.lower()

        prefixes = {
            "callback": _node_name + "@" + _port_name + "@",
            "node": _node_name + "@",
            "robot": "@",
            "flow": "flow@",
            "fleet": _robot_name + "@",
            "global": "@",
        }
        prefix = prefixes.get(scope, "@")

        if scope in ("fleet", "global"):
            scope_ = "global"
        else:
            scope_ = "local"

        MovaiDB(scope_).unsafe_delete({"Var": {scope: {"ID": {prefix + "*": {"Value": "*"}}}}})
        if scope == "node":  # also clean SM Vars
            MovaiDB(scope_).unsafe_delete(
                {"Var": {scope: {"ID": {prefix + "*": {"Parameter": "*"}}}}}
            )
