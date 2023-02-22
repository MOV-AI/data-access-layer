from redis_om import Migrator, Field, JsonModel, get_redis_connection


class Model(JsonModel):
    a: str = Field(default="a", index=True)
    b: str = Field(index=True)
    c: str

    class Meta:
        global_key_prefix = "Mine"
        database = get_redis_connection(url="redis://172.17.0.2", db=0)
        model_key_prefix = "Model"


Migrator().run()
a1 = Model(**{"a": "a1", "b": "b1", "c": "c1"})
a2 = Model(**{"a": "a2", "b": "b1", "c": "c2"})
#a1.save()
#a2.save()
print(Model.find(Model.b == "b").all())
a=1
#print(Model.find(Model.b == "b1").all())
