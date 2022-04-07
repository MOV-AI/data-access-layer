"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires (alexandre.pires@mov.ai) - 2020

"""
import argparse

# TODO those classes does not exist in data
from dal.data import SchemaManager, ScopeSerializer, ScopeManager

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="DiffTool Mov.AI Data")
    parser.add_argument("-p", "--project", help="Folder to export to or import from.",
                        type=str, required=True, metavar='')
    parser.add_argument("-s", "--scope", help="Object type. Options: Flow, StateMachine, Node, Callback, Annotation",
                        type=str, required=True, default=None)
    parser.add_argument("-n", "--name", help="Object name",
                        type=str, required=True, default=None)

    args, _ = parser.parse_known_args()

    ScopeManager.load(args.scope, name=args.name, workspace="project")


    flows = ScopeManager.get("Flow")
    mapping = flows["mapping"]
    mapping.NodeInst["wait_save"].NodeLabel = "as"
    mapping.NodeInst["wait_save"].NodeLayers = ["as"]
    mapping.NodeInst["wait_save"].Parameter["wait_time"].Value = "10"

    flow_schema_v1 = SchemaManager.get_schema(args.scope, "1.0")
    json_data = ScopeSerializer(args.scope, flow_schema_v1, name=args.name).serialize(
        flows)

    # print(json.dumps(json_data, indent=4, sort_keys=True))
    print(flow_schema_v1.to_path())
