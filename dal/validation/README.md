# Static validations

Static validation inspects the metadata installed in a workspace and reports the issues found, without running the project.
It analyses the project as it is actually deployed, so the platform can run it at any point after installation.

## Running the validations

Two entry points are available:

| Validator | Scope | Entry point |
| --------- | ----- | ----------- |
| `ProjectValidator` | Every object installed in the workspace | `dal.validation.project_validator.ProjectValidator().validate()` |
| `FlowValidator` | A single Flow and every subflow it contains | `dal.validation.flow_validator.FlowValidator(flow_ref).validate_flow()` |

```python
from dal.validation.project_validator import ProjectValidator
from dal.validation.flow_validator import FlowValidator

project_result = ProjectValidator().validate()
flow_result = FlowValidator("my_flow").validate_flow()
```

Both are also exposed by the backend REST API:

```
GET /api/v2/validate/project
GET /api/v2/validate/flow/{flow}
```

### Result format

Both entry points return a `ProjectValidationResult`:

```json
{
    "summary": {
        "total_issues": 1,
        "error_count": 1,
        "warning_count": 0,
        "scopes_checked": ["Annotation", "Callback", "..."]
    },
    "issues": [
        {
            "category": "Formating",
            "iss_type": "Missing Flow or Node",
            "severity": "ERROR",
            "msg": "Node 'test_any' missing, required by Flow 'test_missing_node' (instance 'test_any')",
            "json_path": "test_missing_node.json",
            "document_type": "Flow",
            "document_name": "test_missing_node",
            "line_start": 27
        }
    ]
}
```

`line_start` refers to the document rendered with the MOV.AI standard JSON formatting (`indent=4`, `sort_keys=True`), which is how documents are exported from Redis.
`json_path`, `document_type` and `document_name` identify the document the issue should be reported on, which is not always the Flow being validated: a parameter defined in a Node template, for example, is reported on the Node metadata.

## Validations

The following table describes each issue, its category, its default severity and the data it applies to.
The severity is the one reported when the issue is found on a reachable path; see [Reachability](#reachability) for when it is downgraded.

| Issue category | Issue type                               | Issue severity | Applicable to      |
| -------------- | ---------------------------------------- | -------------- | ------------------ |
| Formating      | Duplicated metadata                      | Error          | All scopes         |
| Formating      | Missing Flow or Node                     | Error          | Flow               |
| Formating      | Missing flow instance referenced by link | Error          | Flow links         |
| Formating      | Missing node instance referenced by link | Error          | Flow links         |
| Formating      | Missing Node port                        | Error          | Flow links         |
| Formating      | Non matching link ports                  | Error          | Flow links         |
| Formating      | Missing referenced parameter             | Error          | Flow, Node         |

### Formating - Duplicated metadata

Issue triggered when the same metadata name is found in more than one package installed in the same workspace.
Duplicated names are ambiguous: which of the documents is used depends on installation order.

See example [proj-duplicated-metadata](../../tests/unit/data/invalid/proj-duplicated-metadata/).

### Formating - Missing Flow or Node

Issue triggered when a Flow declares a container or a node instance whose template (a Flow or a Node) does not exist in the project.

See examples [proj-missing-flow](../../tests/unit/data/invalid/proj-missing-flow/) and [proj-missing-node](../../tests/unit/data/invalid/proj-missing-node/).

### Formating - Missing flow instance referenced by link

Issue triggered when a link path mentions a container (subflow instance) that no longer exists in the Flow.

See example [proj-missing-flow-instance](../../tests/unit/data/invalid/proj-missing-flow-instance/).

### Formating - Missing node instance referenced by link

Issue triggered when a link path mentions a node instance that no longer exists in the Flow.

See example [proj-missing-node-instance](../../tests/unit/data/invalid/proj-missing-node-instance/).

### Formating - Missing Node port

Issue triggered when a link connects to a port that does not exist on the referenced Node template.
Reported separately for the source and the destination of the link.

See example [proj-missing-port](../../tests/unit/data/invalid/proj-missing-port/).

### Formating - Non matching link ports

Issue triggered when both ports of a link exist but are not compatible, and therefore should not be connected.

Compatible combinations are:

- A `movai_msgs/Any` publisher to any subscriber, and any publisher to a `movai_msgs/Any` subscriber, except transitions.
- Publisher to subscriber of the same package and message, in any combination of ROS1 and ROS2 implementations.
- `MovAI/Depends` to `MovAI/Dependency`.
- `MovAI/TransitionFor` to `MovAI/TransitionTo`.
- `ROS1/NodeletClient` to `ROS1/NodeletServer`, `ROS1/PluginClient` to `ROS1/PluginServer`, `ROS1/ReconfigureClient` to `ROS1/ReconfigureServer`.
- `ROS1/ServiceClient` to `ROS1/ServiceServer` of the same package and message.
- `ROS1/ActionClient` and `ROS1/ActionServer`, in both directions.
- `ROS1/Publisher` to `ROS1/TopicHz`.

See example [proj-non-matching-ports](../../tests/unit/data/invalid/proj-non-matching-ports/).

### Formating - Missing referenced parameter

Issue triggered when a parameter expression references a value that cannot be resolved by the runtime parameter parser.
The message names the kind of reference that could not be resolved:

| Reference | Expression | Resolved from |
| --------- | ---------- | ------------- |
| `flow`    | `$(flow <name>)`   | Parameters of the Flow the instance belongs to |
| `config`  | `$(config <name>)` | A Configuration document |
| `param`   | `$(param <name>)`  | Parameters of the node instance itself |

Parameters are parsed the same way the runtime parses them: each Flow is validated in the context of the runnable Flow that contains it, with the full container path of the instance, so that a subflow parameter bound by an ancestor container resolves exactly as it will at runtime.
This means the same subflow can be reported as valid in one parent Flow and invalid in another.

`$(var ...)` references are not reported, since fleet and robot variables can be created by nodes during execution and therefore cannot be checked statically. They still raise an error when parsed at runtime.

See examples [proj-missing-referenced-params](../../tests/unit/data/invalid/proj-missing-referenced-params/), [proj-subflow-missing-referenced-params](../../tests/unit/data/invalid/proj-subflow-missing-referenced-params/) and [proj-node-template-missing-referenced-param](../../tests/unit/data/invalid/proj-node-template-missing-referenced-param/).

## Reachability

Metadata that cannot be reached when the project runs cannot break it, so issues found on unreachable paths are reported as warnings (`NORMAL`) instead of errors.
They are still reported, because they usually indicate leftovers from an incomplete edit and could cause errors if the unreachable paths become reachable in the future.
