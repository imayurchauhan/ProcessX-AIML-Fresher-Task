from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ResidentDayNote:
    resident: str
    day: str
    date: str | None
    staff_member: str | None
    note: str


@dataclass(slots=True)
class Issue:
    day: str
    flag_type: str
    field: str
    explanation: str
    evidence: str


@dataclass(slots=True)
class ResidentReport:
    resident: str
    issues: list[Issue] = field(default_factory=list)
