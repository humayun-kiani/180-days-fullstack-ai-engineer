# app/incidents/manager.py
# Incident management system

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class IncidentSeverity(Enum):
    SEV1 = "sev1"     # critical — wake everyone up
    SEV2 = "sev2"     # high — page on-call
    SEV3 = "sev3"     # medium — fix this business day
    SEV4 = "sev4"     # low — schedule it


class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"


@dataclass
class IncidentEvent:
    timestamp: float
    actor: str
    action: str
    details: str

    def to_dict(self) -> dict:
        return {
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
            "actor": self.actor,
            "action": self.action,
            "details": self.details
        }


@dataclass
class Incident:
    incident_id: str
    title: str
    severity: IncidentSeverity
    description: str
    status: IncidentStatus = IncidentStatus.OPEN
    opened_by: str = "alert-system"
    assigned_to: Optional[str] = None
    opened_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    events: list[IncidentEvent] = field(default_factory=list)
    affected_services: list[str] = field(default_factory=list)
    root_cause: str = ""
    resolution: str = ""

    @property
    def duration_minutes(self) -> Optional[float]:
        if self.resolved_at:
            return round((self.resolved_at - self.opened_at) / 60, 1)
        return None

    def add_event(self, actor: str, action: str, details: str):
        self.events.append(IncidentEvent(
            timestamp=time.time(),
            actor=actor,
            action=action,
            details=details
        ))

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "severity": self.severity.value,
            "description": self.description,
            "status": self.status.value,
            "opened_by": self.opened_by,
            "assigned_to": self.assigned_to,
            "opened_at": datetime.fromtimestamp(
                self.opened_at, tz=timezone.utc
            ).isoformat(),
            "resolved_at": datetime.fromtimestamp(
                self.resolved_at, tz=timezone.utc
            ).isoformat() if self.resolved_at else None,
            "duration_minutes": self.duration_minutes,
            "events": [e.to_dict() for e in self.events],
            "affected_services": self.affected_services,
            "root_cause": self.root_cause,
            "resolution": self.resolution
        }


class IncidentManager:
    """
    Manages production incidents from detection to resolution.

    In production: integrates with PagerDuty, Jira, Slack.
    """

    def __init__(self):
        self._incidents: dict[str, Incident] = {}
        self._counter = 0

    def open_incident(
        self,
        title: str,
        severity: str,
        description: str,
        affected_services: list[str] = None,
        opened_by: str = "alert-system"
    ) -> Incident:
        self._counter += 1
        incident_id = f"INC-{self._counter:04d}"

        sev = IncidentSeverity(severity.lower())
        incident = Incident(
            incident_id=incident_id,
            title=title,
            severity=sev,
            description=description,
            affected_services=affected_services or ["task-api"],
            opened_by=opened_by
        )
        incident.add_event(
            actor=opened_by,
            action="incident_opened",
            details=f"Incident opened: {title}"
        )

        self._incidents[incident_id] = incident

        sev_emoji = {"sev1": "🚨", "sev2": "⚠️", "sev3": "🔶", "sev4": "ℹ️"}
        print(f"\n  {sev_emoji.get(severity.lower(), '⚠️')} INCIDENT {incident_id}: [{severity.upper()}] {title}")

        return incident

    def assign(self, incident_id: str, assignee: str) -> Incident:
        incident = self._get_or_raise(incident_id)
        incident.assigned_to = assignee
        incident.status = IncidentStatus.INVESTIGATING
        incident.add_event(assignee, "assigned", f"Incident assigned to {assignee}")
        return incident

    def update_status(
        self,
        incident_id: str,
        status: str,
        actor: str,
        details: str
    ) -> Incident:
        incident = self._get_or_raise(incident_id)
        incident.status = IncidentStatus(status.lower())
        incident.add_event(actor, f"status_changed_to_{status}", details)
        return incident

    def resolve(
        self,
        incident_id: str,
        root_cause: str,
        resolution: str,
        resolved_by: str = "on-call"
    ) -> Incident:
        incident = self._get_or_raise(incident_id)
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = time.time()
        incident.root_cause = root_cause
        incident.resolution = resolution
        incident.add_event(
            resolved_by,
            "resolved",
            f"Root cause: {root_cause} | Resolution: {resolution}"
        )
        print(f"\n  ✅ INCIDENT {incident_id} RESOLVED in {incident.duration_minutes} minutes")
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self._incidents.get(incident_id)

    def get_active_incidents(self) -> list[dict]:
        return [
            i.to_dict() for i in self._incidents.values()
            if i.status != IncidentStatus.RESOLVED
        ]

    def get_all_incidents(self) -> list[dict]:
        return [i.to_dict() for i in reversed(list(self._incidents.values()))]

    def _get_or_raise(self, incident_id: str) -> Incident:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        return incident


# Global incident manager
incident_manager = IncidentManager()