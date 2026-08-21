from __future__ import annotations

import yaml

__version__ = "0.1.1"


def _keep_yaml_timestamps_as_strings() -> None:
    """Keep date-like YAML scalars as strings across CareerVault.

    PyYAML otherwise converts values such as ``2026-08-21`` into
    ``datetime.date`` objects. CareerVault stores dates as user-editable text,
    and mixed date/string values can break sorting and JSON-facing APIs.
    """
    timestamp_tag = "tag:yaml.org,2002:timestamp"
    resolvers = yaml.SafeLoader.yaml_implicit_resolvers
    for key, entries in list(resolvers.items()):
        resolvers[key] = [(tag, regexp) for tag, regexp in entries if tag != timestamp_tag]


_keep_yaml_timestamps_as_strings()
