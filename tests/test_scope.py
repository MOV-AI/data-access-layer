import json

import pytest

from dal.new_models.callback import Callback as PydanticCallback
from dal.new_models.flow import Flow as FlowPydantic
from dal.scopes import Callback as ScopeCallback
from dal.scopes.flow import Flow as FlowScope

from pytest_mock.plugin import MockerFixture


path = "/opt/mov.ai/dev/data-access-layer/tests/"


def export_to_file(d: dict, file_name: str):
    file_name = path + file_name
    try:
        obj = json.dumps(d, indent=4)
        with open(file_name, "w") as outfile:
            outfile.write(obj)
    except Exception as exc:
        print(exc)


#export_to_file(scope.get_dict(recursive=True), "scope_dict_recursive.json")
#export_to_file(scope.get_dict(recursive=False), "scope_dict_non_recursive.json")

#export_to_file(pydantic.get_dict(recursive=True), "pydantic_dict_recursive.json")
#export_to_file(pydantic.get_dict(recursive=False), "pydantic_dict_non_recursive.json")

def convert_callback(callback_name:str):
    original_cb = ScopeCallback(callback_name).get_dict()
    convert_callback = PydanticCallback.model_validate(original_cb, strict=True)
    convert_callback.save()


@pytest.mark.xfail
def test_convert_callback(mocker: MockerFixture):
    from dal.new_models.base_model.redis_model import RedisModel
    mocker.patch.object(RedisModel, "db_handler")
    
    flow_name = "movai_lab_loop_sim"
    pydantic = FlowPydantic(flow_name)
    scope = FlowScope(flow_name)

    convert_callback("calibration_manager_init")