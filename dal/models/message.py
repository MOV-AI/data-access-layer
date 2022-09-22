"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Message Model
"""

# pylint: disable=invalid-name
from collections import deque
from typing import Dict, List
import genmsg
import rosmsg
import rospkg

from dal.models.scopestree import scopes
from dal.scopes.system import System
from dal.models.model import Model

from movai_core_shared.logger import Log


logger = Log.get_logger('')


class Message(Model):
    """ Message Model implementation

        use Deprecated one instead
    """

    # default __init__

    def is_valid(self):
        """ Returns True """
        return True

    @staticmethod
    def fetch_portdata_api(db='local') -> Dict:
        """ Retrieve data from database """
        return System('PortsData', db=db).Value #scopes().System['PortsData'].Value

    # was a classmethod, no references found
    @staticmethod
    def get_packages(msg_type: str = 'all', db: str = 'global') -> List:
        """ Get a list of all packages containing messages of type `msg_type` """

        if msg_type not in ('all', 'msg', 'srv', 'action'):
            raise ValueError("Invalid message type, allowed: 'all', 'msg', 'srv', 'action'")

        rospack = rospkg.RosPack()

        db_scopes = scopes()    # always global TODO change in future

        msg_packs = []
        srv_packs = []
        action_packs = []
        action_names = ('ActionFeedback', 'ActionGoal', 'ActionResult')

        # [{url:, scope:, ref:}, ...]
        db_packs = db_scopes.list_scopes(scope='Message')

        if msg_type in ('msg', 'all'):
            msg_packs = [*(
                pkg for pkg, _ in rosmsg.iterate_packages(rospack, '.msg')
            ), *(
                pkg['ref']
                for pkg in db_packs
                if db_scopes.Message[pkg['ref']].Msg.count > 0
            )]

        if msg_type in ('srv', 'all'):
            srv_packs = [*(
                pkg for pkg, _ in rosmsg.iterate_packages(rospack, '.srv')
            ), *(
                pkg['ref']
                for pkg in db_packs
                if db_scopes.Message[pkg['ref']].Srv.count > 0
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
                if db_scopes.Message[pkg['ref']].Action.count > 0:
                    action_packs.append(pkg['ref'])

        return list(set(msg_packs+srv_packs+action_packs))

    @staticmethod
    def get_msgs(package: str, msg_type: str = 'all', db: str = 'global') -> List:
        """ Get a list of all messages inside a package, filtered by `msg_type` """

        if msg_type not in ('all', 'msg', 'srv', 'action'):
            raise ValueError("Invalid message type, allowed: 'all', 'msg', 'srv', 'action'")

        rospack = rospkg.RosPack()

        db_scopes = scopes()    # also global

        pkg_len = len(package) +1
        msg_list = []
        srv_list = []
        action_list = []

        if msg_type in ('msg', 'all'):
            try:
                msg_list = [msg[pkg_len:] for msg in rosmsg.list_msgs(package, rospack)]
            except rospkg.common.ResourceNotFound:
                # check on DB
                try:
                    msg_list = list(db_scopes.Message[package].Msg)
                except KeyError:
                    # package not found
                    logger.warning(f"package not found")
                    pass
        if msg_type in ('srv', 'all'):
            try:
                srv_list = [msg[pkg_len:] for msg in rosmsg.list_srvs(package, rospack)]
            except rospkg.common.ResourceNotFound:
                # check on DB
                try:
                    srv_list = list(db_scopes.Message[package].Srv)
                except KeyError:
                    # package not found
                    logger.warning(f"package not found")
                    pass
        if msg_type == 'action':
            try:
                temp_msg_list = [msg[pkg_len:] for msg in rosmsg.list_msgs(package, rospack)]
                for msg in temp_msg_list:
                    if msg.endswith('Action'):
                        action_list.append(msg)
            except rospkg.common.ResourceNotFound:
                try:
                    action_list = list(db_scopes.Message[package].Action)
                except KeyError:
                    # not found
                    logger.warning(f"KeyError after rospkg.common.ResourceNotFound")
                    pass

        return list(set(msg_list+srv_list+action_list))

    @staticmethod
    def get_all(db='global') -> Dict[str, List]:
        """ Get a map of package -> messages from all packages """

        db_scopes = scopes()    # global for now
        db_packs = db_scopes.list_scopes(scope='Message')

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

        db_scopes = scopes()    # fetch from global

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

        try:
            ports_data = System('PortsData', db=db) #db_scopes.System['PortsData']
        except Exception:   # pylint: disable=broad-except
            ports_data = System('PortsData', new=True, db=db) # db_scopes.create('System', 'PortsData')

        ports_data.Value = value

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
        mobj = scopes().Message[package]
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


Model.register_model_class('Message', Message)
