import pytest
from pytest_mock import MockerFixture
import dal.scopes
import dal.new_models
from dal.scopes import Robot, System
from dal.new_models import System as PydanticSystem
import movai_core_enterprise.scopes
import movai_core_enterprise.new_models

from movai_core_shared.logger import Log

LOGGER = Log.get_logger(__name__)

def validate_model(model: str, id: str, db: str = "global"):
    try:
        scopes_class = getattr(dal.scopes, model)
        pydantic_class = getattr(dal.new_models, model)
    except AttributeError:
        scopes_class = getattr(movai_core_enterprise.scopes, model)
        pydantic_class = getattr(movai_core_enterprise.new_models, model)

    if scopes_class is Robot:
        obj_dict = scopes_class().get_dict()
    elif scopes_class is System:
        obj_dict = scopes_class(id, db="local").get_dict()
    else:
        obj_dict = scopes_class(id).get_dict()
    obj = pydantic_class.model_validate(obj_dict)
    obj.save(db=db)


@pytest.mark.xfail
def test_migrate_system(mocker: MockerFixture):
    from dal.new_models.base_model.redis_model import RedisModel
    mocker.patch.object(RedisModel, "db_handler")

    model_name = "PyModules"
    validate_model("Robot", model_name, "local")
    s = PydanticSystem(model_name, db="local")
    print(s)