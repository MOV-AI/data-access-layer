# vTBD
- [BP-1418](https://movai.atlassian.net/browse/BP-1418): Update GraphicScene PUT/POST to fullfil FE requirements

# v3.16.2
- [BP-1420](https://movai.atlassian.net/browse/BP-1420): Skip removal of Package:maps and Package:point_clouds on import

# v3.16.1
- [BP-1548](https://movai.atlassian.net/browse/BP-1548): Await check_permissions
  - InternalUser has permission to CREATE, READ, UPDATE, and RESET itself (but not DELETE or EXECUTE)
  -  Move extra callback execution permission check to Callback Scope
  - Add user permission tests.

# v3.16.0
- [BP-1471](https://movai.atlassian.net/browse/BP-1471): Create API to remove robot (Migrate old remove robot API)
  - Change FleetRobot.remove_entry vague exceptions to more specific ones

# v3.15.0
- [BP-1545](https://movai.atlassian.net/browse/BP-1545): Remove old Alerts implementation

# v3.14.0
- [BP-1460](https://movai.atlassian.net/browse/BP-1460): API to expose fleet information

# v3.13.0
- [BP-1539](https://movai.atlassian.net/browse/BP-1539): API for alert status and to get list of active alerts

# v3.12.2
- [BP-1115](https://movai.atlassian.net/browse/BP-1115): Losen aiohttp dep due to fixes in aiohttp==3.8.4
  - From [aiohttp==3.8.4](https://docs.aiohttp.org/en/latest/changes.html#id278):
    - Fixed ConnectionResetError not being raised after client disconnection in SSL environments.
      - This has impact server side, where the handler would remain running

# v3.12.1
- [BP-1531](https://movai.atlassian.net/browse/BP-1531): Failing to update alerts templates

# v3.12.0
- [BP-1530](https://movai.atlassian.net/browse/BP-1530): Add validation for alert placeholder arguments
  - Add tests

# v3.11.0
- [BP-1518](https://movai.atlassian.net/browse/BP-1518): Create alerts history API
  - Use pydantic classes
  - Add FleetRobot.name_to_id

# v3.10.1
- [BP-1519](https://movai.atlassian.net/browse/BP-1519): Edit Alert schema

# v3.10.0
- [BP-1521](https://movai.atlassian.net/browse/BP-1521): Logic to activate and deactivate alert
- [BP-1520](https://movai.atlassian.net/browse/BP-1520): Deactivate alerts on start / stop flow

# v3.9.1
- [BP-1488](https://movai.atlassian.net/browse/BP-1488): Translation PO file name separator is valid for metadata name

# v3.9.0
- [BP-1462](https://movai.atlassian.net/browse/BP-1462): Translation implementation
  - Add tool to collect logs to be translated

# v3.8.0
- [BP-1462](https://movai.atlassian.net/browse/BP-1462): Translation implementation
  - Singleton - lock only on first instantiation
  - Add `subscribe_by_args_decoded` to simplify subscription

# v3.7.1
- [BP-1470](https://movai.atlassian.net/browse/BP-1470): Move DEFAULT_LANGUAGE to central location

# v3.7.0
- [BP-1456](https://movai.atlassian.net/browse/BP-1456): Add support for user language configuration
  - Introduced `language` attribute for `BaseUser` and `InternalUser` models.
  - Added validation for `language` using `VALID_LANGUAGES` from `movai_core_shared.consts`.
  - Updated JSON schemas (`InternalUser.json` and `User.json`) to include the `Language` field.
  - Added getter and setter for the `language` property in `BaseUser`.

# v3.6.0
- [BP-1472](https://movai.atlassian.net/browse/BP-1472): Import / remove / remove Translation scope

# v3.5.1
- [BP-1476](https://movai.atlassian.net/browse/BP-1476): tools.backup root-path (-r) parameter is not working

# v3.5.0
- [BP-1463](https://movai.atlassian.net/browse/BP-1463): Create translation scope

# v3.4.1
- Fix mobdata usage (missing 1 required positional argument: 'args')

# v3.4.0
- Add pylint, remove deadcode (dalapi, protocols, packagefile)
- Remove Git classes

# v3.3.1
- Fix version number, the version still includes [BP-1441](https://movai.atlassian.net/browse/BP-1441): Operator does not have permission to get scene

# v3.2.10
- **Disregard version, the version number went from 3.3.0 to 3.2.10 by mistake**
- [BP-1441](https://movai.atlassian.net/browse/BP-1441): Operator does not have permission to get scene

# v3.3.0
- [DP-1843](https://movai.atlassian.net/browse/DP-1843): Create mobdata

# v3.2.9
- [BP-1429](https://movai.atlassian.net/browse/BP-1429): Enable tests using docker compose in dal

# v3.2.8
- [BP-1390](https://movai.atlassian.net/browse/BP-1434): Caching of flow's node dependencies.

# v3.2.7
- [BP-1434](https://movai.atlassian.net/browse/BP-1434): Duplicated logs on spawner

# v3.2.6
- [BP-1420](https://movai.atlassian.net/browse/BP-1420): Initial cleanup on backup tool

# v3.2.5
- [BP-1311](https://movai.atlassian.net/browse/BP-1311): Backend taking long to delete document / error in response

# v3.2.4
- Add tests using docker compose
- Only get TTL if already in attributes
- Allow setting TTL using add("Parameter", ...) syntax

# v3.2.3
- [BP-1365](https://movai.atlassian.net/browse/BP-1365): Fix call to get_param

# v3.2.2
- [BP-1328](https://movai.atlassian.net/browse/BP-1328): Improve TTL on Robot parameters

# v3.2.1
- [BP-1303](https://movai.atlassian.net/browse/BP-1303): Rosparam.get_param() of a disabled parameter returns the value instead of None

# v3.1.2
- [BP-1405](https://movai.atlassian.net/browse/BP-1405): Backeng logs an error if someone tries to login with a user that does not exist

# v3.1.1
- [BP-1399](https://movai.atlassian.net/browse/BP-1399): Format code

# v3.1.0
- [BP-1312](https://movai.atlassian.net/browse/BP-1312): Validation of ability for non-super user to run callbacks is broken

# v3.0.5
- Revert BP-1310
- [RP-3269](https://movai.atlassian.net/browse/RP-3269): Have HFM working on the real lab (v3.0.5.3)
  - Add robot type and robot model to robot class

# v3.0.4
- [BP-1371](https://movai.atlassian.net/browse/BP-1371): NameError: name 'gd' is not defined

# v3.0.3
- [BP-1360](https://movai.atlassian.net/browse/BP-1360): Metrics no longer available when running cloud function

# v3.0.2
- [BP-1339](https://movai.atlassian.net/browse/BP-1339): Migrate data-access-layer to py-workflow@v2
- [BP-1342](https://movai.atlassian.net/browse/BP-1342): Move the middleware and GD_Callback from gd-node (v3.0.2.3)
- Review Node set_type (v3.0.2.4)
- [BP-1310](https://movai.atlassian.net/browse/BP-1310): Cache configurations and flow dependencies (v3.0.2.5)
- [BP-1330](https://movai.atlassian.net/browse/BP-1330): Implement Async Callbacks (v3.0.2.6)
- [BP-1330](https://movai.atlassian.net/browse/BP-1330): Send commands to Robot async (v3.0.2.7)
- [BP-1310](https://movai.atlassian.net/browse/BP-1310): Enable fetching yamls directly from db instead of cached (v3.0.2.8)
- [BP-1328](https://movai.atlassian.net/browse/BP-1328): Add TTL to robot parameters (v3.0.2.9)

# v3.0.1
- [BP-1322](https://movai.atlassian.net/browse/BP-1322): Move WSRedisSub and Var_Subscriber

# v3.0.0 (same as v2.5.0.35)
- [BP-1319](https://movai.atlassian.net/browse/BP-1319): Move development to main branch
- Merge `releases/2.5.0` into `main` to bring history
