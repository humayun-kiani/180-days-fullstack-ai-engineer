# Day 48 — Infrastructure as Code with Terraform

> **Phase 6 — DevOps & Infrastructure** | Week 9 | Day 48 of 180

---

## 📌 What I Learned Today

- IaC: define infrastructure in code, not through cloud console clicks
- Terraform is the most widely used IaC tool (AWS CDK, Pulumi are alternatives)
- HCL: HashiCorp Configuration Language — declarative, human-readable
- Provider: plugin that talks to cloud/service API (aws, google, kubernetes, local)
- Resource: a piece of infrastructure to manage (VPC, EC2, security group)
- Data source: read existing infra without creating it
- Variable: input parameter with type, description, validation, default
- Output: export values after apply (like function return values)
- Local: computed values derived within the config
- `terraform init`: download providers, initialize backend
- `terraform plan`: show what will change — NEVER makes changes
- `terraform apply`: execute the plan, update state
- `terraform destroy`: destroy all resources in state
- State file: maps .tf resource → real cloud resource ID
- State drift: real infra changed outside Terraform → mismatch
- Remote backend: S3 + DynamoDB for team state management
- State locking: DynamoDB lock prevents concurrent apply corruption
- Module: packaged, reusable infrastructure component
- source: local path or Terraform Registry URL for modules
- module.name.output_name: access a module's output
- count: create N copies of a resource
- for_each: create resources from a map/set
- Conditional: `condition ? true_value : false_value`
- For expression: transform lists/maps inline
- validation block: enforce variable constraints
- workspace: manage multiple environments with one config
- terraform.workspace: current workspace name as string
- Naming convention: {project}-{environment}-{resource_type}
- Environment configs: use locals to define per-env defaults
- depends_on: explicit dependency between resources
- merge(): combine maps (for tags)

## 🔨 Project Built

**Complete Task API Infrastructure:**

**3 Terraform modules:**

- network: VPC, public/private subnets, internet gateway
- security: security group (ports 80/443/8000), IAM role
- compute: EC2 instances (1-N), ALB load balancer, health check

**Root module:**

- Orchestrates all 3 modules
- locals.tf: env-specific config (dev=t3.micro 1x, prod=t3.medium 3x)
- Generates deployment-summary.json with all resource IDs

**2 environment configs:**

- development: 1 AZ, 1 instance, DEBUG logs, 100 max tasks
- production: 3 AZ, 3 instances, WARNING logs, 100K max tasks

**Python simulator:**

- engine.py: plan/apply/destroy with disk-persisted state
- resources.py: dev + prod infrastructure definitions
- visualizer.py: colorized plan and apply output
- 5 scenarios: fresh deploy → update → scale → prod → destroy

## 🚀 How to Run

```bash
cd Day-48-Terraform

# Python simulator (no cloud needed)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m simulator.main

# Real Terraform (requires installation)
cd terraform
terraform init
terraform plan -var="environment=development"
terraform apply -var="environment=development" -auto-approve
terraform output
terraform destroy -auto-approve
```

## 🧠 Key Commands

```bash
terraform init      # download providers
terraform plan      # preview changes (SAFE — no changes made)
terraform apply     # make changes
terraform destroy   # delete everything
terraform fmt       # format .tf files
terraform validate  # check syntax
terraform output    # show output values
terraform show      # show full state
terraform state list # list resources in state
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
