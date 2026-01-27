"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module that implements a Message scope class
   For Reference: https://github.com/ros/ros_comm/blob/6a0672c0189024e38bfe51d917dea148f76fccf7/tools/rosmsg/src/rosmsg/__init__.py
"""

import os
import rospkg
import genmsg
import rosmsg
from dal.scopes.scope import Scope
from dal.movaidb import MovaiDB


class Message(Scope):
    """Message class"""

    scope = "Message"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Message", name=name, version=version, new=new, db=db)

    def is_valid(self):
        # what is in db is valid to run
        return True

    @classmethod
    def get_packages(cls, msg_type="all", db="global") -> list:
        """Gives a list of all packages containing messages of a type"""

        if msg_type not in ["all", "msg", "srv", "action"]:
            raise Exception(
                'Invalid message type. Valid ones are: "msg", "srv", "action" and "all"'
            )

        rospack = rospkg.RosPack()

        msg_packs = []
        srv_packs = []
        action_packs = []
        action_names = ["ActionFeedback", "ActionGoal", "ActionResult"]

        db_packs = [x for x in MovaiDB(db).search_by_args(cls.scope, Name="*")[0][cls.scope]]

        if msg_type in ("msg", "all"):
            msg_packs = [x for x, _ in rosmsg.iterate_packages(rospack, ".msg")]
            for package in db_packs:
                if [key for key in Message(package).Msg]:
                    msg_packs.append(package)

        if msg_type in ("srv", "all"):
            srv_packs = [x for x, _ in rosmsg.iterate_packages(rospack, ".srv")]
            for package in db_packs:
                if [key for key in Message(package).Srv]:
                    srv_packs.append(package)

        if msg_type == "action":
            temp_msg_packs = [x for x in rosmsg.iterate_packages(rospack, ".msg")]

            for package, direc in temp_msg_packs:
                temp_list = [msg for msg in rosmsg._list_types(direc, "msg", ".msg")]

                for msg in action_names:
                    if not any(msg in elem for elem in temp_list):
                        break  # leave this package
                else:  # this was only reached if no break was done
                    action_packs.append(package)

            for package in db_packs:
                if [key for key in Message(package).Action]:
                    action_packs.append(package)

        return list(set(msg_packs + srv_packs + action_packs))

    @classmethod
    def get_msgs(cls, package: str, msg_type="all", db="global") -> list:
        """Gives a list of all messages of some type in a package"""

        if msg_type not in ["all", "msg", "srv", "action"]:
            raise Exception(
                'Invalid message type. Valid ones are: "msg", "srv", "action" and "all"'
            )

        rospack = rospkg.RosPack()

        msg_list = []
        srv_list = []
        action_list = []

        if msg_type in ("msg", "all"):
            try:  # check in ROS packages
                # path = os.path.join(rospack.get_path(package), 'msg') #gets msgs, not actions in custom pkgs
                # msg_list = rosmsg._list_types(path, 'msg', '.msg')
                path = rosmsg._get_package_paths(package, rospack)
                for p in path:
                    msg_list.extend(rosmsg._list_types(p + "/msg", "msg", ".msg"))
            except:  # check in DB packages
                try:
                    msg_list = [key for key in Message(package).Msg]
                except:
                    print('Package "%s" is non existent' % package)

        if msg_type in ("srv", "all"):
            try:  # check in ROS packages
                path = os.path.join(rospack.get_path(package), "srv")
                srv_list = rosmsg._list_types(path, "srv", ".srv")
            except:  # check in DB packages
                try:
                    srv_list = [key for key in Message(package).Srv]
                except:
                    print('Package "%s" is non existent' % package)

        if msg_type == "action":
            try:  # check in ROS packages
                path = rosmsg._get_package_paths(package, rospack)
                temp_msg_list = []
                for p in path:
                    temp_msg_list.extend(rosmsg._list_types(p + "/msg", "msg", ".msg"))

                for message in temp_msg_list:
                    if message[-6:] == "Action":
                        action_list.append(message)
            except:  # check in DB packages
                try:
                    action_list = [key for key in Message(package).Action]
                except:
                    print('Package "%s" is non existent' % package)
        print(action_list)
        return list(set(msg_list + srv_list + action_list))

    @classmethod
    def get_all(cls, db="global") -> dict:
        """Gives the all available messages of all types organized by package"""
        rospack = rospkg.RosPack()

        full_dict = {}

        msg_packs = [x for x in rosmsg.iterate_packages(rospack, ".msg")]
        srv_packs = [x for x in rosmsg.iterate_packages(rospack, ".srv")]
        db_packs = [x for x in MovaiDB(db).search_by_args(cls.scope, Name="*")[0][cls.scope]]

        for package, direc in msg_packs:
            full_dict[package] = [msg for msg in rosmsg._list_types(direc, "msg", ".msg")]

        for package, direc in srv_packs:
            full_dict[package] = full_dict.get(package, []) + [
                srv for srv in rosmsg._list_types(direc, "srv", ".srv")
            ]

        for package in db_packs:
            msgs = [key for key in Message(package).Msg]
            srvs = [key for key in Message(package).Srv]
            actions = [key for key in Message(package).Action]
            full_dict[package] = msgs + srvs + actions

        return full_dict

    @classmethod
    def export_portdata(cls, db="global") -> dict:
        """Gives all messages/services available organized by type. Possibly intended to replace get_all(), but kept for legacy reasons"""

        rospack = rospkg.RosPack()

        root = {"ROS1_msg": {}, "ROS1_srv": {}, "ROS1_action": {}}

        # get the messages
        msg_packs = [x for x in rosmsg.iterate_packages(rospack, ".msg")]

        for pkg, path in msg_packs:
            # possibly...
            if pkg == "actionlib":
                # don't put this as a 'message'
                continue

            root["ROS1_msg"][pkg] = root["ROS1_msg"].get(pkg, []) + [
                msg for msg in rosmsg._list_types(path, "msg", ".msg")
            ]

        # save some memory
        del msg_packs

        # now the services
        srv_packs = [x for x in rosmsg.iterate_packages(rospack, ".srv")]

        for pkg, path in srv_packs:
            root["ROS1_srv"][pkg] = root["ROS1_srv"].get(pkg, []) + [
                srv for srv in rosmsg._list_types(path, "srv", ".srv")
            ]

        # memory
        del srv_packs

        # now ... actions
        db_packs = [x for x in MovaiDB(db).search_by_args(cls.scope, Name="*")[0][cls.scope]]
        for pkg in db_packs:
            # so ... all or just actions ?
            mm = Message(pkg)
            if len(mm.Msg):
                root["ROS1_msg"][pkg] = root["ROS1_msg"].get(pkg, []) + [k for k in mm.Msg]
            if len(mm.Srv):
                root["ROS1_srv"][pkg] = root["ROS1_srv"].get(pkg, []) + [k for k in mm.Srv]
            if len(mm.Action):
                root["ROS1_action"][pkg] = root["ROS1_action"].get(pkg, []) + [k for k in mm.Action]

        del db_packs

        # we actually need to parse actions from the messages?
        for pkg in root["ROS1_msg"]:
            pkg_msgs = root["ROS1_msg"][pkg]
            # check for any message with '*ActionGoal'
            loop = True
            while loop:
                loop = False
                base = None
                for msg in pkg_msgs:
                    if msg.endswith("ActionGoal"):
                        # we have one
                        base = msg[:-10]
                        break
                if base is None:
                    break
                # otherwise, we got an action to parse
                # delete messages that end with:
                """
                _to_delete = [base+x for x in ('Action','ActionGoal','ActionFeedback','ActionResult','Goal','Feedback','Result')]
                i = 0
                while True:
                    if pkg_msgs[i] in _to_delete:
                        pkg_msgs.pop(i)
                    else:
                        i += 1
                    if i == len(pkg_msgs):
                        break
                """
                for suffix in (
                    "Action",
                    "ActionGoal",
                    "ActionFeedback",
                    "ActionResult",
                ):
                    pkg_msgs.remove(base + suffix)
                # add to the ROS1_action
                root["ROS1_action"][pkg] = root["ROS1_action"].get(pkg, []) + [base + "Action"]
                # and look for more actions
                loop = True
        # all parsed,

        # save to DB
        MovaiDB("local").set({"System": {"PortsData": {"Value": root}}})

        # this could not return
        return root

        # is there no need for a retrieve function ?

    @staticmethod
    def fetch_portdata_api() -> dict:
        """Retrieve data from database -> Called from a cloud function"""
        return MovaiDB("local").get({"System": {"PortsData": "**"}})["System"]["PortsData"]["Value"]

    @staticmethod
    def fetch_portdata_messages() -> dict:
        """Retrieve all the messages and services available for callbacks"""
        portdata = Message.fetch_portdata_api()
        msgs = portdata["ROS1_msg"]
        srvs = portdata["ROS1_srv"]
        merged_msgs = {**msgs, **srvs}
        for key, value in merged_msgs.items():
            if key in msgs and key in srvs:
                merged_msgs[key] = list(set(value + msgs[key]))
        return merged_msgs

    @staticmethod
    def get_structure(message: str) -> dict:
        """Gives the full structure of a message given the 'package/message' input"""
        rospack = rospkg.RosPack()
        package, msg_name = message.split("/")
        try:  # MESSAGE
            # print(rosmsg.get_msg_text(message))
            search_path = {}

            for p in rospack.list():
                package_paths = rosmsg._get_package_paths(p, rospack)
                search_path[p] = [os.path.join(d, "msg") for d in package_paths]

            context = genmsg.MsgContext.create_default()

            spec = genmsg.load_msg_by_type(context, message, search_path)

            genmsg.load_depends(context, spec, search_path)

            msg_structure = {"msg": {}}
            iterate_message(context, spec, msg_structure["msg"])

        except:  # SERVICE
            try:
                srv_search_path = {}
                msg_search_path = {}

                for p in rospack.list():
                    package_paths = rosmsg._get_package_paths(p, rospack)
                    msg_search_path[p] = [os.path.join(d, "msg") for d in package_paths]
                    srv_search_path[p] = [os.path.join(d, "srv") for d in package_paths]

                context = genmsg.MsgContext.create_default()

                spec = genmsg.load_srv_by_type(context, message, srv_search_path)
                genmsg.load_depends(context, spec, msg_search_path)
                msg_structure = {"srv": {"request": {}, "response": {}}}
                iterate_message(context, spec.request, msg_structure["srv"]["request"])
                iterate_message(context, spec.response, msg_structure["srv"]["response"])

            except:  # LETS TRY IN REDIS
                try:  # MESSAGE
                    context = genmsg.MsgContext()
                    try:
                        text = Message(package).Msg[msg_name].Source
                        spec = genmsg.msg_loader.load_msg_from_string(context, text, msg_name)
                        msg_structure = {"msg": {}}
                        iterate_message(context, spec, msg_structure["msg"])
                    except:  # SERVICE
                        text = Message(package).Srv[msg_name].Source
                        text_in, text_out = text.split("---")
                        msg_in = genmsg.msg_loader.load_msg_from_string(
                            context, text_in, "%sRequest" % (msg_name)
                        )
                        msg_out = genmsg.msg_loader.load_msg_from_string(
                            context, text_out, "%sResponse" % (msg_name)
                        )
                        spec = genmsg.srvs.SrvSpec(msg_in, msg_out, text, msg_name)
                        msg_structure = {"srv": {"request": {}, "response": {}}}
                        iterate_message(context, spec.request, msg_structure["srv"]["request"])
                        iterate_message(context, spec.response, msg_structure["srv"]["response"])

                except:
                    print('Cannot locate structure for Message or Service "%s"' % message)
                    return {}

        return msg_structure


def iterate_message(context, spec, struct):
    for type_, name in zip(spec.types, spec.names):
        struct[name] = {"type": type_, "content": {}}
        base_type = genmsg.msgs.bare_msg_type(type_)
        if not base_type in genmsg.msgs.BUILTIN_TYPES:
            subspec = context.get_registered(base_type)
            iterate_message(context, subspec, struct[name]["content"])
