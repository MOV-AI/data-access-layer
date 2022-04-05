# Mov.ai Database Module

This is part of Mov.ai and is responsible for implementing the access to the database layer. 

- [Block Diagram](../../../../architecture/2.0/datalayer/blocks.uxf)  
- [Class Diagram](../../../../architecture/2.0/datalayer/classes.uxf)

## Implementation

Interfaces:
- VersionObject
- PersistentObject
- SerializableObject
- WorkspaceObject

Classes Available:
- TreeNode, ListNode, DictNode, ObjectNode, PropertyNode, CallableNode
- VersionNode
- ObjectDeserializer, ObjectSerializer
- PersistencePlugin
- WorkspaceNode
- SchemaNode, SchemaVersionNode, SchemaObjectNode, SchemaPropertyNode, SchemasTree, SchemaDeserializer
- ScopeInstanceNode, ScopeInstanceVersionNode, ScopeDictNode, ScopeObjectNode, ScopePropertyNode, ScopeNode, ScopeWorkspace, ScopesTree, ScopeAttributeDeserializer, ScopeAttributeSerializer
  
Singletons:
- WorkspaceManager
- Persistence
- scopes
- schemas

## TreeNode, ListNode, DictNode, ObjectNode, PropertyNode, CallableNode

This classes represent generic nodes in a tree, with TreeNode as the most top abstract class, see [Block Diagram](../../../../architecture/2.0/datalayer/blocks.uxf)  

## VersionNode, VersionObject

- **VersionNode** : the base class for the version nodes, nothing special about this
- **VersionObject** : Interface for objects with the version attribute

## ObjectDeserializer, ObjectSerializer

This classes are the base classes for serialization and deserialization process of data inside the library.
- **ObjectDeserializer**: The base class for deserializer
- **ObjectSerializer**: The base class for serializers

## PersistencePlugin, Persistence, PersistentObject

- **PersistencePlugin**: Interface for the plugins for storing data in the persistent layers currently we just implement 2 plugins:
  - [Redis](../plugins/persistence/redis/README.md)
  - [Filesystem](../plugins/persistence/filesystem/README.md)
- **Persistence**: a Singleton to interact with the available plugins
- **PersistentObject**: a interface for objects that implement the ```serialize()``` method

## SchemaNode, SchemaVersionNode, SchemaObjectNode, SchemaPropertyNode, SchemasTree, SchemaDeserializer, schemas

This classes are implemented to support schemas in mov.ai, a schema is loaded to the schemas tree by a schema deserializer. A schema is a json file located in [schemas](../validation/schema/README.md). For now we just support the V1.0 deserialization which is based on the old API and has a very simple dialect, in the future we wish to support JSON schema format.

The [flow schema](../validation/schema/1.0/Flow.json) when deserialized takes a form of a tree:
```
schemas/1.0/Flow/Info
schemas/1.0/Flow/Label
schemas/1.0/Flow/Description
schemas/1.0/Flow/User
schemas/1.0/Flow/LastUpdate
schemas/1.0/Flow/Version
schemas/1.0/Flow/VersionDelta
schemas/1.0/Flow/NodeInst/Template
schemas/1.0/Flow/NodeInst/NodeLabel
schemas/1.0/Flow/NodeInst/Dummy
schemas/1.0/Flow/NodeInst/Persistent
schemas/1.0/Flow/NodeInst/Launch
schemas/1.0/Flow/NodeInst/Remappable
schemas/1.0/Flow/NodeInst/NodeLayers
schemas/1.0/Flow/NodeInst/CmdLine/Value
schemas/1.0/Flow/NodeInst/EnvVar/Value
schemas/1.0/Flow/NodeInst/Visualization/Value
schemas/1.0/Flow/NodeInst/Parameter/Value
schemas/1.0/Flow/Container/ContainerLabel
schemas/1.0/Flow/Container/ContainerFlow
schemas/1.0/Flow/Container/Visualization
schemas/1.0/Flow/Container/Parameter/Value
schemas/1.0/Flow/ExposedPorts
schemas/1.0/Flow/Links
schemas/1.0/Flow/Layers
schemas/1.0/Flow/Parameter/Value
schemas/1.0/Flow/Parameter/Description
```

To better understand the class behind each node, ```schemas/1.0/Flow/Parameter/Description``` is translated to:
```
<SchemasTree>/<SchemaVersionNode>/<SchemaNode>/<SchemaObjectNode>/<SchemaPropertyNode>
```
- **SchemasTree** : The root of all schemas, all loaded schemas will be under this tree
- **SchemaVersionNode**: A version node, we may have multiple versions at the same time
- **SchemaNode** : A schema node, represents a Schema that is defined in ```schemas```
- **SchemaObjectNode**: a node that represents a object and always have children attributes, more SchemaObjectNode or SchemaPropertyNode
- **SchemaPropertyNode**: the leaf of a branch, all terminal elements are SchemaPropertyNode
- **SchemaDeserializer**: A manager that uses the right plugin to deserialize a schema
- **schemas** : Access to the schemas is done by this singleton

### Code Snippets

```
from movai.data import schemas
flow_schema = schemas("Flow")
print(flow_schema)
```

### Notes:
- Once a schema is loaded into the schema tree it's cached until the execution of the application ends

## WorkspaceManager, WorkspaceNode, WorkspaceObject

- **WorkspaceNode**: the base class for a workspace node, a workspace is where data is store
- **WorkspaceManager** : a Singleton class that provides a easy way to interact with workspaces
- **WorkspaceObject** : Interface for objects with the workspace attributr

### Notes:
- The ```global``` is the Redis workspace and is a builtin workspace it cannot be deleted. 
- A workspace has always a persistent plugin associated with:
  - ```global``` : Redis
  - ```All other workspaces``` : Filesystem 

Code Snippets:
```
# List all available workspace
WorkspaceManager.list_workspaces()

# Creates a new workspace
WorkspaceManager.create_workspace("myworkspace")

# Delete a workspace
WorkspaceManager.delete_workspac("myworkspace")
```
## ScopesTree, ScopeWorkspace, ScopeNode, ScopeInstanceNode, ScopeInstanceVersionNode, ScopeDictNode, ScopeObjectNode, ScopePropertyNode, ScopeAttributeDeserializer, ScopeAttributeSerializer, scopes

This classes are the responsible for interacting with the stored data in the persistent layer, following the same pattern of the ```schemas```, the data is loaded into a tree structure, this will make the data available as cache after the first read.

A ```Flow``` opened from the ```global``` workspace will turn into a tree as this:
```
scopes/global/Flow/mapping/__UNVERSIONED__/Label
scopes/global/Flow/mapping/__UNVERSIONED__/LastUpdate
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_upload/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_upload/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_upload/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_upload/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/lights_ready/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/lights_ready/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/lights_ready/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/lights_ready/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/lights_ready/Parameter/leds/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait_save/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait_save/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait_save/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait_save/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait_save/Parameter/wait_time/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wheels_controller_ghost/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wheels_controller_ghost/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wheels_controller_ghost/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wheels_controller_ghost/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wheels_controller_ghost/Parameter/_namespace/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wheels_controller_ghost/Parameter/_launch/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/mapping_main/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/mapping_main/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/mapping_main/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/mapping_main/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/wait/Parameter/wait_time/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/tugbot_ghost/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/tugbot_ghost/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/tugbot_ghost/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/tugbot_ghost/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_upload/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_upload/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_upload/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_upload/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/gmapping/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/gmapping/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/gmapping/Persistent
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/gmapping/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/gmapping/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/gmapping/Parameter/maxRange/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/gmapping/Parameter/maxUrange/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_upload_map/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_upload_map/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_upload_map/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_upload_map/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/um7_ghost/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/um7_ghost/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/um7_ghost/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/um7_ghost/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/um7_ghost/Parameter/_launch/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_saver/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_saver/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_saver/CmdLine/cmdline/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_saver/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/map_saver/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/imu_filter/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/imu_filter/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/imu_filter/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/imu_filter/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/upload_map/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/upload_map/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/upload_map/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/upload_map/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_saver/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_saver/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_saver/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/trigger_map_saver/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/rosbag_record/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/rosbag_record/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/rosbag_record/CmdLine/cmdline/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/rosbag_record/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/rosbag_record/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/ekf_odom/Template
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/ekf_odom/NodeLabel
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/ekf_odom/Visualization/x/Value
scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/ekf_odom/Visualization/y/Value
scopes/global/Flow/mapping/__UNVERSIONED__/Container/drivers/ContainerLabel
scopes/global/Flow/mapping/__UNVERSIONED__/Container/drivers/ContainerFlow
scopes/global/Flow/mapping/__UNVERSIONED__/Container/drivers/Visualization
scopes/global/Flow/mapping/__UNVERSIONED__/Container/actuators/ContainerLabel
scopes/global/Flow/mapping/__UNVERSIONED__/Container/actuators/ContainerFlow
scopes/global/Flow/mapping/__UNVERSIONED__/Container/actuators/Visualization
scopes/global/Flow/mapping/__UNVERSIONED__/Container/spawn_on/ContainerLabel
scopes/global/Flow/mapping/__UNVERSIONED__/Container/spawn_on/ContainerFlow
scopes/global/Flow/mapping/__UNVERSIONED__/Container/spawn_on/Visualization
scopes/global/Flow/mapping/__UNVERSIONED__/Links
```

Again if we want to map the tree nodes from ```scopes/global/Flow/mapping/__UNVERSIONED__/NodeInst/upload_map/Template``` to the class types it will be:
```
<ScopesTree>/<ScopesWorkspace>/<ScopeNode>/<ScopeInstanceNode>/<ScopeInstanceVersionNode>/<ScopeDict>/<ScopeObjectNode>/<ScopePropertyNode>
```
- **ScopesTree** : the root of all data, all objects are loaded under this node
- **ScopeWorkspace** : a workspace inside mov.ai
- **ScopeNode**: A scope node (Flow, Node, etc)
- **ScopeInstanceNode**: A instance of a scopes, it must have a unique ```ref```
- **ScopeInstanceVersionNode**: A version of a instance, a instance might have multiple versions
- **ScopeDictNode**: A dict object in the schema, 
- **ScopeObjectNode**: A object in the schema, normally this objects are stored in the **ScopeDictNode**
- **ScopePropertyNode**: The leaf of branch, a terminal element is always of this type 
- **ScopeAttributeDeserializer** : The implementation of the deserialization of a scope
- **ScopeAttributeSerializer** : The implementation of the serialization of a scope
- **scopes** : Access to the schemas is done by this singleton

## Code Snippets
```
# Read flow from the global workspace
mapping = scopes().Flow["mapping"]

# write a version of the flow mapping into "myworkspace" 
scopes(workspace="myworkspace").write(mapping,version="1.2.3")

# Read flow with version 1.2.3 from "myworkspace"
mapping = scopes(workspace="myworkspace").Flow["mapping","1.2.3"]

# Read node AMCL from the global workspace
amcl = scopes().Node["amcl"]

# Change the template for the NodeInst["lights_ready"] 
mapping.NodeInst["lights_ready"].Template = "my_template"

# Write into the global database a flow using a dict as source, this will replace the data in the database ( only supported in REDIS )
scopes().write({
     "Flow": {
         "mapping": {
             "NodeInst": {
                 "lights_ready": {
                     "Template": "another_template"}}}}},
                scope="Flow", ref="mapping")

# Delete a part of the data in the database ( only supported in REDIS )
scopes().delete({
     "NodeInst": {
         "lights_ready": {
             "Template": "set_leds_buzzer"}}},
     scope="Flow", ref="mapping")

# Create a new Flow
flow = scopes().create(scope="Flow",ref="my_mapping")

# Add a new node_inst with the "amcl" template
flow.NodeInst["my_node"].Template = "amcl"
```

## Notes:
- In mov.ai data is created dynamically, when you create a new scope instance ie.```my_mapping```you just need to set the attributes according to the schema and the API will automatically add the correct nodes to the tree

