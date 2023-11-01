"""
{
  "_version": "1.0",
  "schema": {
    "$name": {
      "Label": "str",
      "Msg": {
        "$name": {
          "Source": "str",
          "Compiled": "file"
        }
      },
      "Srv": {
        "$name": {
          "Source": "str",
          "Compiled": "file"
        }
      },
      "Action": {
        "$name": {
          "Source": "str",
          "Compiled": "str"
        }
      }
    }
  }
}
"""
from .base import MovaiBaseModel
from pydantic import Field, BaseModel
from collections import deque
from typing import Dict, List
import genmsg
import rosmsg
import rospkg

from .system import System

from movai_core_shared.logger import Log


logger = Log.get_logger(__name__)


class MessageValue(BaseModel):
    Source: str
    Compiled: str
    count: int = 0


class Message(MovaiBaseModel):
    Msg: Dict[str, MessageValue] = Field(default_factory=dict)
    Srv: Dict[str, MessageValue] = Field(default_factory=dict)
    Action: Dict[str, MessageValue] = Field(default_factory=dict)

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ['Msg', 'Srv', 'Action']

    def is_valid(self):
        """ Returns True """
        return True

    @staticmethod
    def fetch_portdata_api(db='local') -> Dict:
        """ Retrieve data from database """
        system: System = System.select(ids=['PortsData'], db=db)[0]
        return system.Value

    # was a classmethod, no references found
    @staticmethod
    def get_packages(msg_type: str = 'all', db: str = 'global') -> List:
        """ Get a list of all packages containing messages of type `msg_type` """

        if msg_type not in ('all', 'msg', 'srv', 'action'):
            raise ValueError("Invalid message type, allowed: 'all', 'msg', 'srv', 'action'")

        rospack = rospkg.RosPack()

        msg_packs = []
        srv_packs = []
        action_packs = []
        action_names = ('ActionFeedback', 'ActionGoal', 'ActionResult')

        db_packs: List[Message] = Message.select()

        if msg_type in ('msg', 'all'):
            msg_packs = [*(
                pkg for pkg, _ in rosmsg.iterate_packages(rospack, '.msg')
            ), *(
                pkg.ref
                for pkg in db_packs
                if len(pkg.Msg) > 0
            )]

        if msg_type in ('srv', 'all'):
            srv_packs = [*(
                pkg for pkg, _ in rosmsg.iterate_packages(rospack, '.srv')
            ), *(
                pkg.ref
                for pkg in db_packs
                if len(pkg.Srv) > 0
            )]

        if msg_type == 'action':
            for pkg, direc in rosmsg.iterate_packages(rospack, '.msg'):
                temp_list = rosmsg._list_types(direc, 'msg', '.msg')
                for msg in action_names:
                    if not any(elem.endswith(msg) for elem in temp_list):
                        break
                else:
                    action_packs.append(pkg)
            for pkg in db_packs:
                if len(pkg.Action) > 0:
                    action_packs.append(pkg.ref)

        return list(set(msg_packs+srv_packs+action_packs))

    @staticmethod
    def get_msgs(package: str, msg_type: str = 'all', db: str = 'global') -> List:
        """ Get a list of all messages inside a package, filtered by `msg_type` """

        if msg_type not in ('all', 'msg', 'srv', 'action'):
            raise ValueError("Invalid message type, allowed: 'all', 'msg', 'srv', 'action'")

        rospack = rospkg.RosPack()

        pkg_len = len(package) + 1
        msg_list = []
        srv_list = []
        action_list = []

        if msg_type in ('msg', 'all'):
            try:
                msg_list = [msg[pkg_len:] for msg in rosmsg.list_msgs(package, rospack)]
            except rospkg.common.ResourceNotFound:
                # check on DB
                try:
                    msg_object = Message(package)
                    msg_list = list(msg_object.Msg)
                except KeyError:
                    # package not found
                    logger.warning("package not found")
                    pass
        if msg_type in ('srv', 'all'):
            try:
                srv_list = [msg[pkg_len:] for msg in rosmsg.list_srvs(package, rospack)]
            except rospkg.common.ResourceNotFound:
                # check on DB
                try:
                    msg_object = Message(package)
                    srv_list = list(msg_object.Srv)
                except KeyError:
                    # package not found
                    logger.warning("package not found")
                    pass
        if msg_type == 'action':
            try:
                temp_msg_list = [msg[pkg_len:] for msg in rosmsg.list_msgs(package, rospack)]
                for msg in temp_msg_list:
                    if msg.endswith('Action'):
                        action_list.append(msg)
            except rospkg.common.ResourceNotFound:
                # check on DB
                try:
                    msg_object = Message(package)
                    action_list = list(msg_object.Action)
                except KeyError:
                    # not found
                    logger.warning("KeyError after rospkg.common.ResourceNotFound")
                    pass

        return list(set(msg_list+srv_list+action_list))

    @staticmethod
    def get_all(db='global') -> Dict[str, List]:
        """ Get a map of package -> messages from all packages """

        db_packs: List[str] = [tup[1] for tup in Message.model_fetch_ids(db=db)]

        base_dict = {
            package: Message.get_msgs(package, db=db)
            for package in Message.get_packages(db=db)
        }

        for pack in db_packs:
            base_dict[pack] = base_dict.get('pack', []) + Message.get_msgs(pack, 'action', db)

        return base_dict

    @staticmethod
    def export_portdata(db='global') -> Dict:
        """ Store all messages, by type, on `db` """

        value = {
            "ROS1_msg": {},
            "ROS1_srv": {},
            "ROS1_action": {}
        }

        for mtype in ('msg', 'srv', 'action'):
            dkey = f'ROS1_{mtype}'
            for pack in Message.get_packages(mtype, db):
                value[dkey][pack] = Message.get_msgs(pack, mtype, db)

        # remove actions from messages
        for pack, msgs in value['ROS1_msg'].items():
            while True:
                for msg in msgs:
                    if msg.endswith('ActionGoal'):
                        base = msg[:-10]
                        break
                else:
                    # not found, exit
                    break

                for suffix in ('Action', 'ActionGoal', 'ActionFeedback', 'ActionResult'):
                    msgs.remove(base+suffix)

        system = System("PortsData")
        system.Value = value
        system.save(db=db)

    @staticmethod
    def fetch_portdata_messages() -> Dict:
        """ Get all messages and services available for callbacks """

        portdata = Message.fetch_portdata_api()
        ret = {}
        for key in set.union(set(portdata['ROS1_msg']), set(portdata['ROS1_srv'])):
            ret[key] = list(set(
                portdata['ROS1_msg'].get(key, [])
                +
                portdata['ROS1_srv'].get(key, [])
            ))
        return ret

    @staticmethod
    def get_structure(message: str) -> Dict:
        """ Gives the full structure of a message fiven 'package/message' input """

        package, name = message.split('/')

        try:    # message
            return Message._parse_msg(rosmsg.get_msg_text(message))
        except rosmsg.ROSMsgException:
            # not there
            pass

        try:    # service
            return Message._parse_msg(rosmsg.get_srv_text(message))
        except rosmsg.ROSMsgException:
            # not there either
            pass

        # DB
        mobj = Message(package)
        context = genmsg.MsgContext()
        # message
        if name in mobj.Msg:
            return Message._parse_msg(
                rosmsg.spec_to_str(
                    context,
                    rosmsg.load_msg_from_string(context, mobj.Msg[name].Source, message)
                )
            )
        elif name in mobj.Srv:
            spec = rosmsg.load_srv_from_string(context, mobj.Srv[name].Source, message)
            parts = (
                rosmsg.spec_to_str(context, spec.request),
                rosmsg.spec_to_str(context, spec.response)
            )
            return Message._parse_msg(
                str.join('---\n', parts)
            )
        # else
        return {}

    @staticmethod
    def _parse_msg(text: str) -> Dict:

        if '---' in text:
            req, res = text.split('---\n')
            return {
                'srv': {
                    'request': Message._parse_part(deque(req.splitlines())),
                    'response': Message._parse_part(deque(res.splitlines()))
                }
            }
        # else
        return {
            'msg': Message._parse_part(deque(text.splitlines()))
        }

    @staticmethod
    def _parse_part(lines, _pre=''):
        _next_pre = _pre+'  '
        msg = {}
        current = None
        line = lines.popleft().rstrip()
        while line.startswith(_pre):
            if line.startswith(_next_pre):
                lines.appendleft(line)
                msg[current]['content'] = Message._parse_part(lines, _next_pre)
                try:
                    line = lines.popleft()
                    continue
                except IndexError:
                    break
            t, current = line.strip().split(' ')
            msg[current] = {'type': t}
            try:
                line = lines.popleft()
            except IndexError:
                break
        if line != '':
            lines.appendleft(line)
        return msg
