"""Eigene Tests ohne laufende Dienste: Operationsbeschreibung, Werkzeuge, RRULE, Zeittypen."""
from datetime import UTC, datetime

import pytest

from chronos import catalog  # noqa: F401
from chronos.core.errors import InvalidRrule
from chronos.domain import series
from chronos.ops.registry import OPERATIONS, describe, params_schema, tool_definition


def test_every_operation_has_one_complete_description():
    assert len(OPERATIONS) >= 18
    for op in OPERATIONS.values():
        d = describe(op)
        assert d["params_schema"]["type"] == "object"
        assert d["params_schema"]["additionalProperties"] is False
        assert d["result_schema"]["type"] == "object"
        assert d["description"]


def test_tools_derive_from_operations():
    for op in OPERATIONS.values():
        t = tool_definition(op)
        assert t["name"] == op.name.replace(".", "_")
        assert t["input_schema"] == params_schema(op)


def test_field_named_title_survives_schema_cleanup():
    assert "title" in params_schema(OPERATIONS["appointment.create"])["properties"]


def test_optional_params_are_plain_types():
    p = params_schema(OPERATIONS["team.create"])
    assert p["required"] == ["name"]
    assert "anyOf" not in p["properties"]["parent_id"]


@pytest.mark.parametrize("rule", ["FREQ=FOO", "FREQ=WEEKLY;BYDAY=XX", "FREQ=WEEKLY;COUNT=3;UNTIL=20270101T000000Z",
                                  "FREQ=MONTHLY;BYMONTHDAY=0", "FREQ=DAILY;INTERVAL=0", "INTERVAL=2;COUNT=3"])
def test_invalid_rrules(rule):
    with pytest.raises(InvalidRrule):
        series.build_rule(rule, datetime(2026, 3, 2, 18), "Europe/Berlin")


def test_wall_clock_over_dst():
    rule = series.build_rule("FREQ=WEEKLY;BYDAY=MO;COUNT=8", datetime(2026, 3, 2, 18), "Europe/Berlin")
    occ = series.expand(rule, "Europe/Berlin", [], datetime(2026, 1, 1, tzinfo=UTC), datetime(2041, 1, 1, tzinfo=UTC))
    assert occ[3].hour == 17 and occ[4].hour == 16  # Umstellung am 29.03.2026
