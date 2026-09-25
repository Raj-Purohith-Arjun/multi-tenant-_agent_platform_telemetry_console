import re
from importlib.metadata import requires


def test_worker_declares_contracts_dependency() -> None:
    declared = {
        re.split(r"[\s<>=!~;\[(]", r, maxsplit=1)[0] for r in requires("worker") or []
    }
    assert "contracts" in declared
