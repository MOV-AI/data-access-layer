import pytest


KEYS = [
    "Flow:main,Label:",
    "Flow:main,NodeInst:pub,Template:",
    "Flow:main,NodeInst:pub,Parameter:rate,Value:",
    "Flow:main,NodeInst:sub,Parameter:topic,Value:",
    "Flow:main,Container:child,Parameter:rate,Value:",
    "Flow:main,Links:a1b2,From:",
    "Flow:main,ExposedPorts:pub:pub/out/out",
    "Flow:main_other,Label:",
]


@pytest.mark.parametrize(
    "document, pattern",
    [
        ("Flow:main", "Flow:main,Label:"),
        ("Flow:main", "Flow:main,NodeInst:*,Template:"),
        ("Flow:main", "Flow:main,NodeInst:*,Parameter:*,Value:"),
        ("Flow:main", "Flow:main,*,Parameter:*,Value:"),
        ("Flow:main", "Flow:main,ExposedPorts:*"),
        ("Flow:main", "Flow:main,Links:*,From:"),
        ("Flow:main", "Flow:other,Label:"),
        ("Flow:ma*", "Flow:ma*,Label:"),
    ],
)
def test_filter_keys_matches_fnmatch(document, pattern):
    """Tests that keys are matched like fnmatch.filter, in the same order."""
    from dal.plugins.persistence.redis.redis import RedisPlugin
    import fnmatch

    plugin = RedisPlugin(workspace="global")
    assert plugin._filter_keys(KEYS, pattern, document) == fnmatch.filter(KEYS, pattern)
