"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
import copy
import re
import time
from movai_core_shared.exceptions import AlreadyExist
from dal.movaidb import MovaiDB
from dal.helpers import Helpers


class List(list):
    """Custom list that overrides pop and append methods"""

    def __init__(self, name: str, init_value: list, db: str, prev_struct: str):
        self.db = db
        self.name = name
        self.prev_struct = prev_struct
        self.movaidb = MovaiDB(db)
        init_value = init_value or []
        super(List, self).__init__(init_value)
        methods = [
            "clear",
            "copy",
            "count",
            "extend",
            "index",
            "insert",
            "remove",
            "reverse",
            "sort",
        ]
        for elem in methods:
            self.__dict__[elem] = lambda self, *args, **kwargs: print(
                "Method not implemented for Redis lists"
            )

    def append(self, value):
        """Append both to python list and redis list"""
        # struct = copy.deepcopy(self.prev_struct)
        self.movaidb.push(Helpers.update_dict(self.prev_struct, {self.name: value}))

    def pop(self):
        """Pop from python list and redis list"""
        # struct = copy.deepcopy(self.prev_struct)
        return self.movaidb.pop(Helpers.update_dict(self.prev_struct, {self.name: ""}))


class Hash(dict):
    """Custom dict that overrides methods"""

    def __init__(self, name: str, init_value: dict, db: str, prev_struct: str):
        self.db = db
        self.name = name
        self.prev_struct = prev_struct
        init_value = init_value or {}
        self.movaidb = MovaiDB(db)
        super(Hash, self).__init__(init_value)

    def __setitem__(self, name, value):
        self.update({name: value})

    def __getitem__(self, name):
        return self.get(name)

    def __delitem__(self, name):
        self.pop(name)

    def update(self, value: dict):
        """Updates the hash with desired dict"""
        super(Hash, self).update(value)
        # struct = copy.deepcopy(self.prev_struct)
        # Helpers already do a deepcopy
        self.movaidb.hset(Helpers.update_dict(self.prev_struct, {self.name: value}))

    def get(self, var: str, default=None):
        """Gets a hash field and returns it"""
        # struct = copy.deepcopy(self.prev_struct)
        # Helpers already do a deepcopy
        result = self.movaidb.hget(Helpers.update_dict(self.prev_struct, {self.name: ""}), var)
        if result:
            # update python with db value
            super(Hash, self).__setitem__(var, result)
            return result
        return default

    def pop(self, var: str):
        """Deletes a hash field and returns it"""
        result = super(Hash, self).pop(var, None)
        if not result:
            raise Exception('Hash has no field with name "%s"' % var)
        # struct = copy.deepcopy(self.prev_struct)
        # Helpers already do a deepcopy
        self.movaidb.hdel(Helpers.update_dict(self.prev_struct, {self.name: ""}), var)
        return result

    def delete(self, var: str):
        """Deletes a hash field and returns True if successfully deleted"""
        try:
            self.pop(var)
        except:
            return False
        return True


class Struct:

    """
    General structure... how to describe?
    """

    Name: str
    db: str
    movaidb: MovaiDB

    def __init__(self, name, struct_dict, prev_struct, db):
        self.__dict__["Name"] = name
        self.__dict__["db"] = db
        self.__dict__["movaidb"] = MovaiDB(db)

        nada = dict()
        for elem in struct_dict:
            nada[name] = dict()
            nada[name][elem] = ""
            break

        # need a way to get rid of theese variables...
        self.__dict__["prev_struct"] = Helpers.update_dict(prev_struct, nada)
        self.__dict__["struct_dict"] = dict()
        (
            self.__dict__["attrs"],
            self.__dict__["lists"],
            self.__dict__["hashs"],
        ) = self.get_attributes(struct_dict)

    def __getattribute__(self, name):
        if name in [
            "__dict__",
            "Name",
            "prev_struct",
            "struct_dict",
            "attrs",
            "lists",
            "hashs",
            "get_attributes",
            "get_ref",
            "db",
            "add",
            "delete",
        ]:
            return super().__getattribute__(name)

        db = self.__dict__["movaidb"]
        if name == "Value" and "TTL" in self.attrs:
            TTL = db.get_value(Helpers.join_first({"TTL": "*"}, self.prev_struct))
            if TTL:
                last_update = db.get_value(
                    Helpers.join_first({"_timestamp": "*"}, self.prev_struct)
                )
                if last_update is not None and last_update + TTL < time.time():
                    return None

        if name in self.attrs:
            return db.get_value(Helpers.join_first({name: "*"}, self.prev_struct))
        elif name in self.lists:
            list_value = db.get_list(Helpers.join_first({name: "*"}, self.prev_struct))
            return List(name, list_value, self.db, self.prev_struct)
        elif name in self.hashs:
            hash_value = db.get_hash(Helpers.join_first({name: "*"}, self.prev_struct))
            return Hash(name, hash_value, self.db, self.prev_struct)
        else:
            if self.__dict__["struct_dict"].get(name) is None:
                return super().__getattribute__(name)

            temp = copy.deepcopy(self.prev_struct)

            final = {}
            result = db.get2(Helpers.join_first({name: "*"}, self.prev_struct))
            if not result:
                return super().__getattribute__(name)

            def recursive(prev, res):
                for (k, v), (k1, v1) in zip(prev.items(), res.items()):
                    if isinstance(v, dict):
                        return recursive(v, v1)
                    return v1

            actual_result = recursive(temp, result)
            for elem in actual_result[name]:
                new_struct = {}
                for elem2 in self.struct_dict[name]:
                    new_struct[elem] = copy.deepcopy(self.struct_dict[name][elem2])
                final[elem] = Struct(name, new_struct, temp, self.db)

        return final

    def __getattr__(self, name):
        if self.__dict__.get("attrs", None) is None:
            raise Exception("This instance was removed and its no longer available")

        if name in self.attrs:  # it exists, just not defined yet
            return None
        raise AttributeError(f"Attribute '{name}' does not exist")

    def __delattr__(self, name):
        if getattr(self, name) is None:
            print("Attribute is not defined")
            return False
        result = self.movaidb.unsafe_delete(Helpers.join_first({name: "*"}, self.prev_struct))
        if name in self.lists:  # do some cleaver delete
            self.__dict__[name] = List(name, [], self.db, self.prev_struct)
        elif name in self.hashs:
            self.__dict__[name] = Hash(name, {}, self.db, self.prev_struct)
        else:
            del self.__dict__[name]
        return result

    def __setattr__(self, name, value):
        if name in self.attrs:
            self.__dict__[name] = value
            self.movaidb.set(Helpers.join_first({name: value}, self.prev_struct))
            if "TTL" in self.attrs:
                self.movaidb.set(Helpers.join_first({"_timestamp": time.time()}, self.prev_struct))
        elif name in self.lists:
            raise AttributeError(f"'{name}' is a list not an attribute")
        elif name in self.hashs:
            raise AttributeError(f"'{name}' is a hash not an attribute")
        else:
            raise AttributeError(f"Attribute '{name}' does not exist")

    def delete(self, key, name):
        args = Helpers.get_args(self.prev_struct)
        args[key] = name
        result = 0
        for scope_name in self.prev_struct:
            result = self.movaidb.delete_by_args(scope_name, **args)

        if key in self.__dict__ and name in self.__dict__[key]:
            del self.__dict__[key][name]

        return result

    def add(self, key, name, **kwargs):  # check if exixts and give error
        new_struct = dict()
        for elem in self.struct_dict[key]:
            # the value in the struct
            new_struct[name] = self.struct_dict[key][elem]

        temp = copy.deepcopy(self.prev_struct)

        self.__dict__[key][name] = Struct(key, new_struct, temp, self.db)

        for k, v in kwargs.items():
            setattr(self.__dict__[key][name], k, v)

        return self.__dict__[key][name]

    def rename(self, key: str, old_name: str, new_name: str) -> bool:
        part2 = getattr(self, key)[old_name].get_dict()

        try:  # check if new name already exists
            getattr(self, key)[new_name]
            raise AlreadyExist("{key} with name '{new_name}' already exists")
        except KeyError:
            pass

        part1_old = Helpers.join_first({key: {old_name: ""}}, self.prev_struct)
        part1_new = Helpers.join_first({key: {new_name: ""}}, self.prev_struct)

        old_struct = Helpers.join_first(part2, part1_old)
        new_struct = Helpers.join_first(part2, part1_new)

        MovaiDB().rename(old_struct, new_struct)
        return True

    def get_dict(self):
        args = Helpers.get_args(self.prev_struct)
        for elem in self.prev_struct:
            scope = elem
            break
        full_dict = self.movaidb.get_by_args(scope, **args)

        def iterate(d: dict, d2: dict):
            for k, v in d.items():
                if isinstance(v, dict):
                    partial = iterate(v, d2[k])
                else:
                    return d2[k]
                return partial

        partial_dict = iterate(self.prev_struct, full_dict)
        return partial_dict

    def get_attributes(self, d: dict):
        # an attribute of a dict is a key that the value is not a dict
        # only the first layer is considered
        for k in d:
            new_dict = d[k]

        attrs = []
        lists = []
        hashs = []
        for key, value in new_dict.items():
            if not isinstance(value, dict):
                if value == "list":
                    self.__dict__[key] = List(key, [], self.db, self.prev_struct)
                    lists.append(key)
                elif value == "hash":
                    self.__dict__[key] = Hash(key, {}, self.db, self.prev_struct)
                    hashs.append(key)
                else:
                    attrs.append(key)
            else:
                self.__dict__[key] = dict()
                self.__dict__["struct_dict"][key] = new_dict[key]
        return attrs, lists, hashs

    def get_ref(self, value: str):
        """Receives a value and returns the value with refs if they exist"""

        def iterate(_dict, _initial):
            for (_, value), (key, val) in zip(_dict.items(), _initial.items()):
                if isinstance(value, dict):
                    return iterate(value, val)
                if len(_dict) > 1 and key != "*":  # in case of hash
                    return _dict[key]
                return value

        def replace(group):
            key = eval(group[1:-1])
            return str(iterate(self.movaidb.get(key), key))

        if isinstance(value, str):
            if "$" in value and value.count("$") % 2 == 0:  # its a REF!!
                # only single ref
                if value.count("$") == 2 and value[0] == "$" and value[-1] == "$":
                    # the value type is maintained
                    value = iterate(self.movaidb.get(eval(value[1:-1])), eval(value[1:-1]))
                else:  # it has more stuff so lets make a nice string with everything
                    value = re.sub(r"\$([^\$]*)\$", lambda x: replace(x.group()), value)
                    # result always a string here
        return value
