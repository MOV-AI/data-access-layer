"""Tests for dal.models.role module."""
import pytest


@pytest.fixture()
def models_role(global_db):
    from dal.models.role import Role

    return Role


@pytest.fixture()
def create_default_roles(models_role):
    models_role.create_default_roles()


class TestRole:
    def test_create_default_roles(self, models_role, create_default_roles):
        """Test that default roles are created correctly."""
        default_roles = set(["ADMIN", "DEPLOYER", "OPERATOR"])
        assert set(models_role.list_roles_names()) == default_roles

        for role in default_roles:
            assert models_role.is_exist(role)

    def test_remove(self, models_role, create_default_roles):
        """Test removing a role."""
        models_role.remove("DEPLOYER")
        assert set(models_role.list_roles_names()) == set(["ADMIN", "OPERATOR"])

    def test_create(self, models_role):
        """Test creating a new role."""
        role_name = "TEST_ROLE"
        resources = {}
        role = models_role.create(role_name, resources)

        assert role.Label == role_name
        assert role.Resources == resources
        assert models_role.is_exist(role_name)

    def test_is_exist_negative(self, models_role):
        """Test is_exist method for a non-existing role."""
        assert not models_role.is_exist("NON_EXISTING_ROLE")
