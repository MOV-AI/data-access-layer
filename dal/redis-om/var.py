from redis_om import JsonModel, Field, EmbeddedJsonModel, HashModel, get_redis_connection, Migrator
from typing import Dict, Any
from pydantic import constr


class Var(JsonModel):
    scope: str = Field(default="Node", index=True)
    vars: Dict[constr(regex=r"^[a-zA-Z_0-9-]+$"), Any] = {}

    class Meta:
        global_key_prefix = "Movai"
        model_key_prefix = "Var"
        database = get_redis_connection(url="redis://172.17.0.2", db=0)

    def set(self, name, value):
        old_vars = self.vars
        old_vars.update({"name": name, "Value": value})
        print(old_vars)
        self.update(vars=old_vars)
        self.save()

    def get(self, key):
        return self.vars.get(key)


Migrator().run()
v = Var()

v.set("a", False)
#v.save()
v.set("b", "hello")
print(v.get("b"))
print(v.get("a"))
