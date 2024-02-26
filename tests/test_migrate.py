""" Test migration of old scopes to new models """

import pytest
from pytest_mock import MockerFixture

try:
    import movai_core_enterprise.scopes
    import movai_core_enterprise.new_models

    ENTERPRISE_AVAILABLE = True
except ModuleNotFoundError:
    ENTERPRISE_AVAILABLE = False

from movai_core_shared.logger import Log

import dal.scopes
import dal.new_models
from dal.scopes import Robot, System
from dal.new_models import System as PydanticSystem


LOGGER = Log.get_logger(__name__)


def validate_model(model: str, object_id: str, db: str = "global"):
    try:
        scopes_class = getattr(dal.scopes, model)
        pydantic_class = getattr(dal.new_models, model)
    except AttributeError as e:
        if ENTERPRISE_AVAILABLE:
            scopes_class = getattr(movai_core_enterprise.scopes, model)
            pydantic_class = getattr(movai_core_enterprise.new_models, model)
        else:
            raise e

    if scopes_class is Robot:
        obj_dict = scopes_class().get_dict()
    elif scopes_class is System:
        obj_dict = scopes_class(object_id, db="local").get_dict()
    else:
        obj_dict = scopes_class(object_id).get_dict()
    obj = pydantic_class.model_validate(obj_dict)
    obj.save(db=db)


@pytest.mark.xfail
def test_migrate_system(mocker: MockerFixture):
    from dal.new_models.base_model.redis_model import (
        RedisModel,
    )  # pylint: disable=import-outside-toplevel

    mocker.patch.object(RedisModel, "db_handler")

    model_name = "PyModules"
    validate_model("Robot", model_name, "local")
    PydanticSystem(model_name, db="local")
