# simulator/main.py
# Main simulation runner — demonstrates the full Terraform workflow

import sys
import json
import time
from pathlib import Path

from simulator.engine import TerraformEngine
from simulator.resources import define_development_infrastructure, define_production_infrastructure
from simulator.visualizer import (
    print_banner, print_plan, print_apply, print_state
)


def run_development_demo():
    """Demonstrate infrastructure deployment for development environment."""
    print("\n" + "─" * 65)
    print("  SCENARIO 1: First-time development deployment")
    print("─" * 65)

    engine = TerraformEngine()
    engine._state.clear()    # fresh state for demo

    # Step 1: terraform init (load provider plugins)
    print("\n  $ terraform init")
    print("  Initializing provider plugins...")
    time.sleep(0.2)
    print("  ✅ Terraform initialized")

    # Step 2: Define infrastructure (read .tf files)
    define_development_infrastructure(engine, version="latest")

    # Step 3: terraform plan
    print("\n  $ terraform plan")
    plan = engine.plan()
    print_plan(plan, "development")

    # Step 4: terraform apply
    print("\n  $ terraform apply -auto-approve")
    results = engine.apply(auto_approve=True)
    print_apply(results)

    # Step 5: terraform output
    print("\n  $ terraform output")
    state = engine.show_state()
    print_state(state)

    return engine


def run_update_demo(engine: TerraformEngine):
    """Demonstrate updating infrastructure (new version)."""
    print("\n" + "─" * 65)
    print("  SCENARIO 2: Deploy new version (v1.1.0)")
    print("─" * 65)

    # Update the app version
    engine._desired.clear()
    define_development_infrastructure(engine, version="1.1.0")

    print("\n  $ terraform plan")
    plan = engine.plan()
    print_plan(plan, "development")

    print("\n  $ terraform apply -auto-approve")
    results = engine.apply(auto_approve=True)
    print_apply(results)


def run_scale_demo(engine: TerraformEngine):
    """Demonstrate scaling (add second instance)."""
    print("\n" + "─" * 65)
    print("  SCENARIO 3: Scale up (add second API instance)")
    print("─" * 65)

    # Add a second instance
    engine._desired.clear()
    define_development_infrastructure(engine, version="1.1.0")

    # Add extra instance
    engine.define("ComputeInstance", "task-api-development-api-2", {
        "instance_type": "t3.micro",
        "subnet":        "task-api-development-private-1",
        "sg":            "task-api-development-sg",
        "image":         "task-api:1.1.0",
        "env": {"ENVIRONMENT": "development", "LOG_LEVEL": "DEBUG", "MAX_TASKS": "100"}
    })

    print("\n  $ terraform plan")
    plan = engine.plan()
    print_plan(plan, "development (scaled)")

    print("\n  $ terraform apply -auto-approve")
    results = engine.apply(auto_approve=True)
    print_apply(results)
    print(f"\n  State now has {engine.show_state()['total']} resources")


def run_production_demo():
    """Demonstrate production environment."""
    print("\n" + "─" * 65)
    print("  SCENARIO 4: Production deployment (3 instances, multi-AZ)")
    print("─" * 65)

    prod_engine = TerraformEngine()
    prod_engine._state.clear()

    define_production_infrastructure(prod_engine, version="1.0.0")

    print("\n  $ terraform plan (production workspace)")
    plan = prod_engine.plan()
    print_plan(plan, "production")

    summary = plan["summary"]
    print(f"\n  Production will create {summary['create']} resources across 3 AZs")
    print("  (Multi-AZ provides high availability — no single point of failure)")

    print("\n  $ terraform apply -auto-approve")
    results = prod_engine.apply(auto_approve=True)
    print_apply(results)

    state = prod_engine.show_state()
    instance_count = sum(
        1 for k in state["resources"]
        if state["resources"][k]["type"] == "ComputeInstance"
    )
    print(f"\n  Production: {instance_count} instances + 1 load balancer ✅")

    return prod_engine


def run_destroy_demo(engine: TerraformEngine, env: str):
    """Demonstrate terraform destroy."""
    print("\n" + "─" * 65)
    print(f"  SCENARIO 5: Destroy {env} environment (terraform destroy)")
    print("─" * 65)

    state_before = engine.show_state()
    print(f"\n  Current state: {state_before['total']} resources")
    print("\n  $ terraform destroy -auto-approve")

    results = engine.destroy()
    print(f"\n  {len(results['destroyed'])} resources destroyed")
    print("  💡 This is why IaC is powerful — recreate identical infra anytime with 'terraform apply'")


def compare_environments():
    """Show difference between dev and prod configs side by side."""
    print("\n" + "─" * 65)
    print("  COMPARISON: Development vs Production")
    print("─" * 65)

    configs = {
        "development": {
            "instance_type": "t3.micro",
            "instance_count": 1,
            "multi_az": False,
            "deletion_protection": False,
            "log_level": "DEBUG",
            "max_tasks": 100,
            "estimated_monthly_cost": "$18"
        },
        "production": {
            "instance_type": "t3.medium",
            "instance_count": 3,
            "multi_az": True,
            "deletion_protection": True,
            "log_level": "WARNING",
            "max_tasks": 100000,
            "estimated_monthly_cost": "$280"
        }
    }

    print(f"\n  {'Setting':<25} {'Development':>15} {'Production':>15}")
    print(f"  {'─' * 56}")

    for key in [
        "instance_type", "instance_count", "multi_az",
        "deletion_protection", "log_level", "max_tasks",
        "estimated_monthly_cost"
    ]:
        dev_val = str(configs["development"][key])
        prod_val = str(configs["production"][key])
        print(f"  {key:<25} {dev_val:>15} {prod_val:>15}")

    print(f"\n  Same Terraform code, different variables = different environments")
    print(f"  This is the power of IaC parameterization!")


def main():
    print_banner()

    # Run all scenarios
    dev_engine = run_development_demo()

    run_update_demo(dev_engine)

    run_scale_demo(dev_engine)

    prod_engine = run_production_demo()

    compare_environments()

    run_destroy_demo(prod_engine, "production")

    print("\n" + "═" * 65)
    print("  Day 48 Complete!")
    print("  Key takeaways:")
    print("  • Terraform plan shows changes without applying them")
    print("  • State tracks what actually exists in the cloud")
    print("  • Modules package reusable infrastructure patterns")
    print("  • Same config + different variables = different environments")
    print("  • Destroy is instant — rebuild is just 'terraform apply'")
    print("═" * 65 + "\n")


if __name__ == "__main__":
    main()