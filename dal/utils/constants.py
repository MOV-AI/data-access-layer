"""DAL constants.

Attributes:
    REST_SCOPES: Scopes supported via REST API.
    SCOPES_TO_TRACK: Scopes for which we update LastUpdate (user and time).

"""
REST_SCOPES = (
    "(Alert|Callback|Form|Flow|Node|GraphicScene|Package|StateMachine|Layout|Annotation|Application|"
    "Configuration|SharedDataTemplate|SharedDataEntry|TaskTemplate|TaskEntry|Translation)"
)
SCOPES_TO_TRACK = [
    "Node",
    "Callback",
    "Flow",
    "StateMachine",
    "Configuration",
    "Annotation",
    "Layout",
    "GraphicScene",
    "Translation",
    "Alert",
]
