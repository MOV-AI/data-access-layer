""" Test imports of objects using the backup tool """


from pytest_mock import MockerFixture

from dal.tools.backup import Importer


def test_import_empty_value(mocker: MockerFixture):
    from dal.new_models.base_model.redis_model import RedisModel  # pylint: disable=import-outside-toplevel
    mocker.patch.object(RedisModel, "db_handler")
    
    importer = Importer(project="importer", root_path="tests/data")
    importer.import_node(["scene_events"])