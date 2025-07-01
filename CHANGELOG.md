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
