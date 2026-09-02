# simulator/engine.py
# Terraform plan/apply engine simulation

import json
import time
import hashlib
from pathlib import Path
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

STATE_FILE = Path(".simulated/terraform.tfstate.json")
STATE_FILE.parent.mkdir(exist_ok=True)


@dataclass
class ResourceConfig:
    """Desired resource configuration (from .tf files)."""
    resource_type: str
    logical_name: str    # the name in .tf file
    config: dict


@dataclass
class ResourceState:
    """Tracked resource state."""
    resource_type: str
    logical_name: str
    real_id: str
    config: dict
    created_at: float


class TerraformEngine:
    """
    Simulates Terraform's plan/apply/destroy cycle.

    State is persisted to disk between runs.
    """

    def __init__(self):
        self._desired: dict[str, ResourceConfig] = {}
        self._state: dict[str, ResourceState] = self._load_state()
        self._id_counter = len(self._state)

    def _load_state(self) -> dict[str, ResourceState]:
        """Load state from disk."""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                raw = json.load(f)
            return {
                k: ResourceState(**v)
                for k, v in raw.items()
            }
        return {}

    def _save_state(self):
        """Persist state to disk."""
        raw = {
            k: {
                "resource_type": v.resource_type,
                "logical_name": v.logical_name,
                "real_id": v.real_id,
                "config": v.config,
                "created_at": v.created_at
            }
            for k, v in self._state.items()
        }
        with open(STATE_FILE, "w") as f:
            json.dump(raw, f, indent=2)

    def _generate_id(self, resource_type: str, name: str) -> str:
        """Generate a deterministic fake cloud resource ID."""
        seed = f"{resource_type}-{name}-{time.time()}"
        h = hashlib.md5(seed.encode()).hexdigest()[:8]
        prefixes = {
            "vpc": "vpc", "subnet": "subnet", "instance": "i",
            "security_group": "sg", "load_balancer": "lb",
            "iam_role": "role", "internet_gateway": "igw"
        }
        prefix = prefixes.get(resource_type.lower().replace(" ", "_"), "res")
        return f"{prefix}-{h}"

    def define(self, resource_type: str, name: str, config: dict):
        """Define a desired resource (equivalent to writing .tf file)."""
        key = f"{resource_type}.{name}"
        self._desired[key] = ResourceConfig(
            resource_type=resource_type,
            logical_name=name,
            config=config
        )

    def plan(self) -> dict:
        """
        Compute diff between desired and current state.
        Never makes changes — just shows what would happen.
        """
        to_create = []
        to_update = []
        to_destroy = []

        # Check desired resources against state
        for key, desired in self._desired.items():
            if key not in self._state:
                to_create.append({
                    "action": "create",
                    "key": key,
                    "type": desired.resource_type,
                    "config": desired.config
                })
            else:
                existing = self._state[key]
                # Find config differences
                changes = {}
                all_keys = set(list(desired.config.keys()) + list(existing.config.keys()))
                for k in all_keys:
                    old_val = existing.config.get(k)
                    new_val = desired.config.get(k)
                    if old_val != new_val:
                        changes[k] = {"old": old_val, "new": new_val}

                if changes:
                    to_update.append({
                        "action": "update",
                        "key": key,
                        "real_id": existing.real_id,
                        "changes": changes
                    })

        # Resources in state but not in desired → destroy
        for key in self._state:
            if key not in self._desired:
                r = self._state[key]
                to_destroy.append({
                    "action": "destroy",
                    "key": key,
                    "real_id": r.real_id,
                    "type": r.resource_type
                })

        return {
            "to_create": to_create,
            "to_update": to_update,
            "to_destroy": to_destroy,
            "summary": {
                "create": len(to_create),
                "update": len(to_update),
                "destroy": len(to_destroy)
            }
        }

    def apply(self, auto_approve: bool = False) -> dict:
        """Execute the plan and update state."""
        plan_result = self.plan()
        changes = plan_result["summary"]

        if not any(changes.values()):
            return {"message": "No changes. Infrastructure is up-to-date.", "changes": {}}

        if not auto_approve:
            print(f"\n  Plan: +{changes['create']} ~{changes['update']} -{changes['destroy']}")
            print("  Do you want to perform these actions? (auto-approved in simulator)")

        results = {"created": [], "updated": [], "destroyed": []}

        # Create
        for item in plan_result["to_create"]:
            r = self._desired[item["key"]]
            real_id = self._generate_id(r.resource_type, r.logical_name)
            self._state[item["key"]] = ResourceState(
                resource_type=r.resource_type,
                logical_name=r.logical_name,
                real_id=real_id,
                config=deepcopy(r.config),
                created_at=time.time()
            )
            results["created"].append({
                "key": item["key"],
                "real_id": real_id,
                "type": item["type"]
            })

        # Update
        for item in plan_result["to_update"]:
            r = self._desired[item["key"]]
            self._state[item["key"]].config = deepcopy(r.config)
            results["updated"].append({
                "key": item["key"],
                "real_id": item["real_id"],
                "changes": list(item["changes"].keys())
            })

        # Destroy
        for item in plan_result["to_destroy"]:
            del self._state[item["key"]]
            results["destroyed"].append({
                "key": item["key"],
                "real_id": item["real_id"]
            })

        self._save_state()
        return results

    def destroy(self) -> dict:
        """Destroy all resources in state."""
        destroyed = list(self._state.keys())
        self._state.clear()
        self._save_state()
        return {"destroyed": destroyed, "count": len(destroyed)}

    def show_state(self) -> dict:
        """Show current state."""
        return {
            "resources": {
                k: {
                    "type": v.resource_type,
                    "name": v.logical_name,
                    "id": v.real_id,
                    "config_keys": list(v.config.keys())
                }
                for k, v in self._state.items()
            },
            "total": len(self._state)
        }

    def output(self, outputs: dict) -> dict:
        """Compute output values from state."""
        result = {}
        for name, config in outputs.items():
            if "value" in config:
                result[name] = {
                    "value": config["value"],
                    "description": config.get("description", "")
                }
        return result