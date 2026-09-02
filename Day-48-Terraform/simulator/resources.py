# simulator/resources.py
# Simulated Task API infrastructure definition

from simulator.engine import TerraformEngine


def define_development_infrastructure(engine: TerraformEngine, version: str = "latest"):
    """Define the development infrastructure."""
    name_prefix = "task-api-development"

    engine.define("VPC", f"{name_prefix}-vpc", {
        "cidr_block":          "10.0.0.0/16",
        "enable_dns_hostnames": True,
        "tags": {"Environment": "development", "ManagedBy": "Terraform"}
    })

    engine.define("Subnet", f"{name_prefix}-public-1", {
        "vpc_name":         f"{name_prefix}-vpc",
        "cidr_block":       "10.0.1.0/24",
        "availability_zone": "us-east-1a",
        "public":           True
    })

    engine.define("Subnet", f"{name_prefix}-private-1", {
        "vpc_name":         f"{name_prefix}-vpc",
        "cidr_block":       "10.0.10.0/24",
        "availability_zone": "us-east-1a",
        "public":           False
    })

    engine.define("SecurityGroup", f"{name_prefix}-sg", {
        "vpc_name":    f"{name_prefix}-vpc",
        "ingress":     [{"port": 8000, "protocol": "tcp", "source": "0.0.0.0/0"}],
        "egress":      [{"port": 0, "protocol": "all", "dest": "0.0.0.0/0"}]
    })

    engine.define("ComputeInstance", f"{name_prefix}-api-1", {
        "instance_type": "t3.micro",
        "subnet":        f"{name_prefix}-private-1",
        "sg":            f"{name_prefix}-sg",
        "image":         f"task-api:{version}",
        "env": {
            "ENVIRONMENT": "development",
            "LOG_LEVEL":   "DEBUG",
            "MAX_TASKS":   "100"
        }
    })

    engine.define("LoadBalancer", f"{name_prefix}-alb", {
        "type":    "application",
        "scheme":  "internet-facing",
        "subnets": [f"{name_prefix}-public-1"],
        "targets": [f"{name_prefix}-api-1"],
        "health_check_path": "/health"
    })


def define_production_infrastructure(engine: TerraformEngine, version: str = "1.0.0"):
    """Define the production infrastructure (HA, multi-AZ)."""
    name_prefix = "task-api-production"
    azs = ["us-east-1a", "us-east-1b", "us-east-1c"]
    instance_count = 3

    engine.define("VPC", f"{name_prefix}-vpc", {
        "cidr_block":           "10.0.0.0/16",
        "enable_dns_hostnames": True,
        "flow_logs":            True,
        "tags": {"Environment": "production", "ManagedBy": "Terraform", "SLA": "99.99%"}
    })

    for i, az in enumerate(azs):
        engine.define("Subnet", f"{name_prefix}-public-{i+1}", {
            "vpc_name":         f"{name_prefix}-vpc",
            "cidr_block":       f"10.0.{i+1}.0/24",
            "availability_zone": az,
            "public":           True
        })
        engine.define("Subnet", f"{name_prefix}-private-{i+1}", {
            "vpc_name":         f"{name_prefix}-vpc",
            "cidr_block":       f"10.0.{i+10}.0/24",
            "availability_zone": az,
            "public":           False
        })

    engine.define("SecurityGroup", f"{name_prefix}-sg", {
        "vpc_name": f"{name_prefix}-vpc",
        "ingress":  [
            {"port": 80,   "protocol": "tcp", "source": "0.0.0.0/0"},
            {"port": 443,  "protocol": "tcp", "source": "0.0.0.0/0"},
            {"port": 8000, "protocol": "tcp", "source": "10.0.0.0/8"}
        ],
        "egress": [{"port": 0, "protocol": "all", "dest": "0.0.0.0/0"}]
    })

    for i in range(instance_count):
        engine.define("ComputeInstance", f"{name_prefix}-api-{i+1}", {
            "instance_type": "t3.medium",
            "subnet":        f"{name_prefix}-private-{(i%3)+1}",
            "sg":            f"{name_prefix}-sg",
            "image":         f"task-api:{version}",
            "env": {
                "ENVIRONMENT": "production",
                "LOG_LEVEL":   "WARNING",
                "MAX_TASKS":   "100000"
            }
        })

    engine.define("LoadBalancer", f"{name_prefix}-alb", {
        "type":    "application",
        "scheme":  "internet-facing",
        "subnets": [f"{name_prefix}-public-{i+1}" for i in range(3)],
        "targets": [f"{name_prefix}-api-{i+1}" for i in range(instance_count)],
        "health_check_path":     "/health",
        "deletion_protection":   True,
        "access_logs":           True,
        "waf_enabled":           True
    })