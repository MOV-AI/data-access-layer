import pytest
from movai_core_shared.consts import (
    ADMIN_ROLE,
    OPERATOR_ROLE,
    DEPLOYER_ROLE,
    CREATE_PERMISSION,
    READ_PERMISSION,
    UPDATE_PERMISSION,
    DELETE_PERMISSION,
    EXECUTE_PERMISSION,
    RESET_PERMISSION,
)

DEFAULT_PERMISSIONS = [
    CREATE_PERMISSION,
    READ_PERMISSION,
    UPDATE_PERMISSION,
    DELETE_PERMISSION,
]

# Execute and Reset permissions are added to specific resources only
EXECUTE_PERMISSIONS = DEFAULT_PERMISSIONS + [EXECUTE_PERMISSION]
USER_PERMISSIONS = DEFAULT_PERMISSIONS + [RESET_PERMISSION]

EXECUTE_RESOURCES = ["Application", "Callback"]
RESET_RESOURCES = ["InternalUser"]

EXISTING_RESOURCES = [
    "AclObject",
    "Alert",
    "Annotation",
    "Applications",
    "Callback",
    "Configuration",
    "Flow",
    "GraphicScene",
    "InternalUser",
    "Layout",
    "Node",
    "Package",
    "Role",
    "SharedDataEntry",
    "SharedDataTemplate",
    "TaskEntry",
    "TaskTemplate",
    "Translation",
]

EXISTING_APPLICATIONS = [
    "AdminBoard",
    "FleetBoard",
    "mov-fe-app-ide",
    "mov-fe-app-launcher",
    "mov-fe-app-taskmanager",
]


@pytest.fixture()
def models_role(global_db):
    from dal.models.role import Role

    return Role


@pytest.fixture()
def create_applications(global_db):
    """Create test Application objects in the database using the proper API"""
    from dal.scopes.application import Application

    created_apps = []
    for app_name in EXISTING_APPLICATIONS:
        try:
            app = Application(app_name, new=True)
            app.Label = app_name
            app.Type = "web"
            app.write()
            created_apps.append(app_name)
        except Exception:
            # Application might already exist or creation failed
            pass

    yield created_apps

    # Cleanup - remove created applications
    for app_name in created_apps:
        try:
            app = Application(app_name)
            app.remove()
        except Exception:
            # Application might have been already removed
            pass


@pytest.fixture()
def create_default_roles(models_role):
    """Create default roles after applications exist in DB"""
    # Now create_default_roles will dynamically get the applications from DB
    models_role.create_default_roles()


@pytest.fixture()
def create_defaults(create_applications, create_default_roles):
    """Fixture to create all defaults: applications and roles"""
    yield


@pytest.fixture()
def create_internal_user(global_db):
    from dal.models.internaluser import InternalUser

    return InternalUser


@pytest.fixture()
def user_factory(create_internal_user):
    """Factory fixture that creates users and tracks them for cleanup"""
    created_users = []

    def _create_user(account_name, password="StrongPassw0rd!", roles=[]):
        """Create a user and track it for cleanup"""

        user = create_internal_user.create(
            account_name=account_name, password=password, roles=roles
        )
        created_users.append(user)
        return user

    yield _create_user

    # Cleanup all created users
    for user in created_users:
        try:
            user.remove()
        except Exception:
            # User might have been already removed
            pass


class TestUserPermissions:
    """
    Test User Permissions for different roles and resources

    Existing Roles:
        - ADMIN_ROLE
        - OPERATOR_ROLE
        - DEPLOYER_ROLE

    Existing Permissions:
        - CREATE_PERMISSION
        - READ_PERMISSION
        - UPDATE_PERMISSION
        - DELETE_PERMISSION
        - EXECUTE_PERMISSION (only for Application and Callback resources)
        - RESET_PERMISSION (only for InternalUser resource)

    """

    def test_deployer_role_permissions(self, models_role, user_factory, create_defaults, global_db):
        """
        Test that InternalUser with DEPLOYER_ROLE has correct permissions on resources:
            1. Create InternalUser with DEPLOYER_ROLE
            2. Verify that the user has correct permissions on all resources
        """

        base_user = user_factory("deployer_user", roles=[DEPLOYER_ROLE])
        for resource, permissions in models_role.DEPLOYER_RESOURCES.items():
            if resource == "Applications":
                # Deployer role has only specific application permissions
                for app in EXISTING_APPLICATIONS:
                    if app in permissions:
                        assert (
                            base_user.has_permission(resource, app) is True
                        ), f"Deployer user should have {app} permission on {resource}"
                    else:
                        assert (
                            base_user.has_permission(resource, app) is False
                        ), f"Deployer user should NOT have {app} permission on {resource}"
                # Check a non-existing application permission
                assert (
                    base_user.has_permission(resource, "NonExistingApp") is False
                ), f"Deployer user should NOT have NonExistingApp permission on {resource}"
                continue
            for permission in DEFAULT_PERMISSIONS:
                if permission in permissions:
                    assert (
                        base_user.has_permission(resource, permission) is True
                    ), f"Deployer user should have {permission} permission on {resource}"
                else:
                    assert (
                        base_user.has_permission(resource, permission) is False
                    ), f"Deployer user should NOT have {permission} permission on {resource}"

            # Test execute permission for resources that support it
            if resource in EXECUTE_RESOURCES:
                if EXECUTE_PERMISSION in permissions:
                    assert (
                        base_user.has_permission(resource, EXECUTE_PERMISSION) is True
                    ), f"Deployer user should have {EXECUTE_PERMISSION} permission on {resource}"
                else:
                    assert (
                        base_user.has_permission(resource, EXECUTE_PERMISSION) is False
                    ), f"Deployer user should NOT have {EXECUTE_PERMISSION} permission on {resource}"

            # Test reset permission for resources that support it
            if resource in RESET_RESOURCES:
                if RESET_PERMISSION in permissions:
                    assert (
                        base_user.has_permission(resource, RESET_PERMISSION) is True
                    ), f"Deployer user should have {RESET_PERMISSION} permission on {resource}"
                else:
                    assert (
                        base_user.has_permission(resource, RESET_PERMISSION) is False
                    ), f"Deployer user should NOT have {RESET_PERMISSION} permission on {resource}"

    def test_operator_role_permissions(
        self, models_role, create_internal_user, create_defaults, global_db
    ):
        """
        Test that InternalUser with OPERATOR_ROLE has correct permissions on resources:
            1. Create InternalUser with OPERATOR_ROLE
            2. Verify that the user has correct permissions on all resources
        """

        base_user = create_internal_user.create(
            account_name="operator_user", password="StrongPassw0rd!", roles=[OPERATOR_ROLE]
        )
        for resource, permissions in models_role.OPERATOR_RESOURCES.items():
            if resource == "Applications":
                # Operator role has only specific application permissions
                for app in EXISTING_APPLICATIONS:
                    if app in permissions:
                        assert (
                            base_user.has_permission(resource, app) is True
                        ), f"Operator user should have {app} permission on {resource}"
                    else:
                        assert (
                            base_user.has_permission(resource, app) is False
                        ), f"Operator user should NOT have {app} permission on {resource}"
                # Check a non-existing application permission
                assert (
                    base_user.has_permission(resource, "NonExistingApp") is False
                ), f"Operator user should NOT have NonExistingApp permission on {resource}"
                continue
            for permission in DEFAULT_PERMISSIONS:
                if permission in permissions:
                    assert (
                        base_user.has_permission(resource, permission) is True
                    ), f"Operator user should have {permission} permission on {resource}"
                else:
                    assert (
                        base_user.has_permission(resource, permission) is False
                    ), f"Operator user should NOT have {permission} permission on {resource}"

            # Test execute permission for resources that support it
            if resource in EXECUTE_RESOURCES:
                if EXECUTE_PERMISSION in permissions:
                    assert (
                        base_user.has_permission(resource, EXECUTE_PERMISSION) is True
                    ), f"Operator user should have {EXECUTE_PERMISSION} permission on {resource}"
                else:
                    assert (
                        base_user.has_permission(resource, EXECUTE_PERMISSION) is False
                    ), f"Operator user should NOT have {EXECUTE_PERMISSION} permission on {resource}"

            # Test reset permission for resources that support it
            if resource in RESET_RESOURCES:
                if RESET_PERMISSION in permissions:
                    assert (
                        base_user.has_permission(resource, RESET_PERMISSION) is True
                    ), f"Operator user should have {RESET_PERMISSION} permission on {resource}"
                else:
                    assert (
                        base_user.has_permission(resource, RESET_PERMISSION) is False
                    ), f"Operator user should NOT have {RESET_PERMISSION} permission on {resource}"

    def test_admin_role_permissions(self, create_internal_user, create_defaults, global_db):
        """
        Test that InternalUser with ADMIN_ROLE has all permissions on all resources:
            1. Create InternalUser with ADMIN_ROLE
            2. Verify that the user has all permissions on all resources
            3. For Applications resource, verify that the user has all application permissions
        """

        base_user = create_internal_user.create(
            account_name="admin_user", password="StrongPassw0rd!", roles=[ADMIN_ROLE]
        )
        for resource in EXISTING_RESOURCES:
            if resource == "Applications":
                # Admin role has only specific application permissions
                for app in EXISTING_APPLICATIONS:
                    assert (
                        base_user.has_permission(resource, app) is True
                    ), f"Admin user should have {app} permission on {resource}"
                # Check a non-existing application permission
                assert (
                    base_user.has_permission(resource, "NonExistingApp") is False
                ), f"Admin user should NOT have NonExistingApp permission on {resource}"
                continue
            for permission in DEFAULT_PERMISSIONS:
                assert (
                    base_user.has_permission(resource, permission) is True
                ), f"Admin user should have {permission} permission on {resource}"

    def test_multiple_roles_permissions(
        self, models_role, create_internal_user, create_defaults, global_db
    ):
        """
        Test that InternalUser with multiple roles has combined permissions from all roles:
            1. Create InternalUser with both OPERATOR_ROLE and DEPLOYER_ROLE
            2. Verify that the user has permissions for OPERATOR_ROLE
            3. Verify that the user has permissions for DEPLOYER_ROLE

        Only assert for permissions that are granted by the roles
        to avoid false negatives caused by other role.
        """

        base_user = create_internal_user.create(
            account_name="multi_role_user",
            password="StrongPassw0rd!",
            roles=[OPERATOR_ROLE, DEPLOYER_ROLE],
        )
        # Check DEPLOYER permissions
        for resource, permissions in models_role.DEPLOYER_RESOURCES.items():
            for permission in DEFAULT_PERMISSIONS:
                if permission in permissions:
                    assert (
                        base_user.has_permission(resource, permission) is True
                    ), f"Multi-role user should have {permission} permission on {resource} from DEPLOYER role"

            # Test execute permission for resources that support it
            if resource in EXECUTE_RESOURCES and EXECUTE_PERMISSION in permissions:
                assert (
                    base_user.has_permission(resource, EXECUTE_PERMISSION) is True
                ), f"Multi-role user should have {EXECUTE_PERMISSION} permission on {resource} from DEPLOYER role"

            # Test reset permission for resources that support it
            if resource in RESET_RESOURCES and RESET_PERMISSION in permissions:
                assert (
                    base_user.has_permission(resource, RESET_PERMISSION) is True
                ), f"Multi-role user should have {RESET_PERMISSION} permission on {resource} from DEPLOYER role"

        # Check OPERATOR permissions
        for resource, permissions in models_role.OPERATOR_RESOURCES.items():
            for permission in DEFAULT_PERMISSIONS:
                if permission in permissions:
                    assert (
                        base_user.has_permission(resource, permission) is True
                    ), f"Multi-role user should have {permission} permission on {resource} from OPERATOR role"

            # Test execute permission for resources that support it
            if resource in EXECUTE_RESOURCES and EXECUTE_PERMISSION in permissions:
                assert (
                    base_user.has_permission(resource, EXECUTE_PERMISSION) is True
                ), f"Multi-role user should have {EXECUTE_PERMISSION} permission on {resource} from OPERATOR role"

            # Test reset permission for resources that support it
            if resource in RESET_RESOURCES and RESET_PERMISSION in permissions:
                assert (
                    base_user.has_permission(resource, RESET_PERMISSION) is True
                ), f"Multi-role user should have {RESET_PERMISSION} permission on {resource} from OPERATOR role"

    def test_no_roles_permissions(self, create_internal_user, create_defaults, global_db):
        """
        Test that InternalUser with no roles has no permissions on any resource
        """

        base_user = create_internal_user.create(
            account_name="no_role_user", password="StrongPassw0rd!", roles=[]
        )
        for resource in EXISTING_RESOURCES:
            if resource == "Applications":
                # User with no roles should not have any application permissions
                for app in EXISTING_APPLICATIONS:
                    assert (
                        base_user.has_permission(resource, app) is False
                    ), f"No-role user should NOT have {app} permission on {resource}"
                # Check a non-existing application permission
                assert (
                    base_user.has_permission(resource, "NonExistingApp") is False
                ), f"No-role user should NOT have NonExistingApp permission on {resource}"
                continue
            for permission in DEFAULT_PERMISSIONS:
                assert (
                    base_user.has_permission(resource, permission) is False
                ), f"No-role user should NOT have {permission} permission on {resource}"

            # Test execute permission for resources that support it
            if resource in EXECUTE_RESOURCES:
                assert (
                    base_user.has_permission(resource, EXECUTE_PERMISSION) is False
                ), f"No-role user should NOT have {EXECUTE_PERMISSION} permission on {resource}"

            # Test reset permission for resources that support it
            if resource in RESET_RESOURCES:
                assert (
                    base_user.has_permission(resource, RESET_PERMISSION) is False
                ), f"No-role user should NOT have {RESET_PERMISSION} permission on {resource}"

    def test_non_existing_resource_permission(
        self, create_internal_user, create_defaults, global_db
    ):
        """
        Test that InternalUser does not have valid permissions on non-existing resources
        """

        base_user = create_internal_user.create(
            account_name="invalid_resource_user", password="StrongPassw0rd!", roles=[ADMIN_ROLE]
        )
        # Test non-existing resource
        for permission in DEFAULT_PERMISSIONS + [EXECUTE_PERMISSION, RESET_PERMISSION]:
            assert (
                base_user.has_permission("NonExistingResource", permission) is False
            ), "User should NOT have permission on non-existing resource"

    def test_non_existing_permission(self, create_internal_user, create_defaults, global_db):
        """
        Test that InternalUser does not have non-existing permissions on existing resources
        """

        base_user = create_internal_user.create(
            account_name="invalid_permission_user", password="StrongPassw0rd!", roles=[ADMIN_ROLE]
        )
        # Test non-existing permission on existing resources
        for resource in EXISTING_RESOURCES:
            assert (
                base_user.has_permission(resource, "non_existing_permission") is False
            ), f"User should NOT have non-existing permission on {resource}"

    def test_internal_user_permission_to_itself(
        self, create_internal_user, create_defaults, global_db
    ):
        """
        Test that InternalUser has appropriate permissions on itself:
            1. InternalUser without ADMIN_ROLE should have all permissions except delete on itself
            2. InternalUser with ADMIN_ROLE should have all permissions including delete on itself
        """
        internal_user = create_internal_user.create(
            account_name="self_permission_user", password="StrongPassw0rd!", roles=[OPERATOR_ROLE]
        )
        # InternalUser should have all permissions on itself
        for permission in USER_PERMISSIONS:
            if permission == DELETE_PERMISSION:
                # InternalUser should not have delete permission on itself
                assert (
                    internal_user.has_permission(
                        "InternalUser", permission, "self_permission_user@internal"
                    )
                    is False
                ), f"InternalUser should NOT have {permission} permission on itself"
                continue
            assert (
                internal_user.has_permission(
                    "InternalUser", permission, "self_permission_user@internal"
                )
                is True
            ), f"InternalUser should have {permission} permission on itself"

        internal_user_admin = create_internal_user.create(
            account_name="self_permission_admin", password="StrongPassw0rd!", roles=[ADMIN_ROLE]
        )
        # InternalUser with ADMIN_ROLE should have all permissions on itself including delete
        for permission in USER_PERMISSIONS:
            assert (
                internal_user_admin.has_permission(
                    "InternalUser", permission, "self_permission_admin@internal"
                )
                is True
            ), f"InternalUser with ADMIN_ROLE should have {permission} permission on itself"
