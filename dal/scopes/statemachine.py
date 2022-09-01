"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module to work with State Machines in GD_Nodes
"""
from dal.movaidb import MovaiDB
from dal.scopes.scope import Scope


class StateMachine(Scope):
    """StateMachine class"""
    scope = 'StateMachine'

    def __init__(self, name, version='latest', new=False, db='global'):
        super().__init__(scope="StateMachine", name=name, version=version, new=new, db=db)

    def delete(self, key, name):
        """ Delete object dependencies """
        result = super().delete(key, name)

        # delete State Links
        if result > 0 and key == "State":

            for link, value in self.Links.items():
                if value["From"].split("/", 1)[0] == name or \
                   value["To"].split("/", 1)[0] == name:
                    # delete the link if State is in From or To
                    del self.Links[link]

    def is_valid(self):
        return {}

    def add_link(self, source_node: str, source_port: str, target_node: str, target_port: str, **ignore) -> tuple:
        '''
            verifies if the links already exists if not add it to the Links hash
        '''

        # create the link
        source = "/".join([source_node, source_port])
        target = "/".join([target_node, target_port])
        new_link = {"From": source, "To": target}

        # check if link already exists
        for _, link in self.Links.items():
            if new_link == link:
                # link already exists
                raise Exception("Link already exists")

        _db_write = MovaiDB(self.db).db_write

        # get a new id from redis
        linksInc = 'System:StateMachine,LinksID'
        _id = _db_write.incr(linksInc)

        self.Links.update({_id: new_link})
        return (_id, new_link)

    def delete_link(self, link_id: str) -> bool:
        ''' delete link '''
        try:
            self.Links.delete(link_id)
            print("Link deleted", link_id)
            return True
        except Exception as e:
            print(e)
            return False

    def copy_node(self, copy_name: str, org_name: str, org_flow: str, org_type: str = "State", options: dict = None):
        """ copy a node instance """

        labels = {"State": "StateLabel"}

        try:
            _flow = self if org_flow == self.name else type(self)(org_flow)

            node_to_copy = getattr(_flow, org_type)[org_name]
            new_node = node_to_copy.get_dict()
            new_node[labels[org_type]] = copy_name

            if options:
                new_node.update(options)

            MovaiDB().set({self.__class__.__name__: {
                self.name: {org_type: {copy_name: new_node}}}})

            return (True, None)

        except Exception as error:

            return (False, repr(error))


class SMVars:
    """Class for user to write and read vars into a state machine"""

    def __init__(self, _sm_name, _node_name=''):

        self.__dict__['_sm_name'] = _sm_name
        self.__dict__['_node_name'] = _node_name
        self.__dict__['id'] = _node_name + '@' + _sm_name

    def __setattr__(self, name, value):
        MovaiDB('local').hset(
            {'Var': {'node': {'ID': {self.id: {'Parameter': {name: value}}}}}})

    def __getattr__(self, name):
        try:
            return MovaiDB('local').hget({'Var': {'node': {'ID': {self.id: {'Parameter': ''}}}}}, name, search=False)
        except KeyError:
            return None

    def __delattr__(self, name):
        try:
            MovaiDB('local').hdel(
                {'Var': {'node': {'ID': {self.id: {'Parameter': ''}}}}}, name, search=False)
            return True
        except:
            return False

    def set(self, name, value):
        '''Same as setattr'''
        setattr(self, name, value)

    def get(self, name):
        '''Same as getattr'''
        return getattr(self, name)

    def delete(self, name):
        '''Same as delattr'''
        return delattr(self, name)

    def get_dict(self):
        return MovaiDB('local').get_hash({'Var': {'node': {'ID': {self.id: {'Parameter': ''}}}}})

    '''
    @staticmethod
    def delete_all(scope: str = 'Node', _robot_name='', _node_name='', _port_name=''):
        """Delete all variables of a certain scope"""

        if scope.lower() not in SCOPES:
            scop = str(SCOPES)[1:-1]
            raise Exception("'" + scope + "' is not a valid scope. Choose between: " + scop)
        scope = scope.lower()

        prefixes = {'callback': _node_name + '@' + _port_name + '@',
                    'node': _node_name + '@', 'robot':'@',
                    'fleet': _robot_name + '@', 'global':'@'}
        prefix = prefixes.get(scope, '@')

        if scope in ('fleet', 'global'):
            scope_ = 'global'
        else:
            scope_ = 'local'

        res = MovaiDB(scope_).unsafe_delete({'Var':{scope:{'ID':{prefix+'*':{'Value': '*'}}}}})
        #print(res)
        '''


if __name__ == '__main__':

    pass
