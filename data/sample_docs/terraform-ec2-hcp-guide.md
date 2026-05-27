# Provisioning EC2 Instances with Terraform in HCP

## Overview

HashiCorp Cloud Platform (HCP) provides a managed Terraform Cloud experience for teams. This guide covers how to provision AWS EC2 instances using Terraform workspaces hosted on HCP Terraform (formerly Terraform Cloud).

## Prerequisites

- An HCP Terraform account (https://app.terraform.io)
- AWS credentials configured (Access Key + Secret Key or IAM Role)
- Terraform CLI installed locally (v1.5+)
- A VCS connection (GitHub, GitLab, or Bitbucket) linked to your HCP org

## Step 1: Create an HCP Terraform Workspace

1. Log into https://app.terraform.io
2. Navigate to your Organization → Workspaces → "New Workspace"
3. Choose **Version Control Workflow** (recommended) or CLI-driven
4. Connect your repository containing Terraform config
5. Set the working directory if your `.tf` files are in a subdirectory

## Step 2: Configure AWS Credentials as Variables

In your HCP workspace settings, add the following **Environment Variables** (mark as Sensitive):

| Variable Name | Category | Sensitive |
|---------------|----------|-----------|
| `AWS_ACCESS_KEY_ID` | env | Yes |
| `AWS_SECRET_ACCESS_KEY` | env | Yes |
| `AWS_DEFAULT_REGION` | env | No |

Alternatively, use **Dynamic Provider Credentials** with OIDC for keyless authentication (recommended for production):

```hcl
# In your workspace settings, enable "Dynamic Provider Credentials"
# HCP Terraform will assume an IAM role via OIDC — no static keys needed
```

## Step 3: Write the EC2 Terraform Configuration

```hcl
terraform {
  cloud {
    organization = "my-org"
    workspaces {
      name = "ec2-production"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "instance_type" {
  default     = "t3.micro"
  description = "EC2 instance type"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {
    Name        = "hcp-managed-ec2"
    Environment = "production"
    ManagedBy   = "terraform-cloud"
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  metadata_options {
    http_tokens   = "required"  # IMDSv2 enforced
    http_endpoint = "enabled"
  }
}

output "instance_id" {
  value = aws_instance.web.id
}

output "public_ip" {
  value = aws_instance.web.public_ip
}
```

## Step 4: Plan and Apply via HCP

### Option A: VCS-Driven (Automatic)

1. Push your code to the connected branch
2. HCP Terraform automatically runs `terraform plan`
3. Review the plan in the HCP UI
4. Click **"Confirm & Apply"** to provision

### Option B: CLI-Driven

```bash
# Login to HCP Terraform
terraform login

# Initialize (connects to remote workspace)
terraform init

# Plan (runs remotely on HCP)
terraform plan

# Apply (runs remotely, streams output locally)
terraform apply
```

## Step 5: Use Run Triggers for Multi-Workspace Pipelines

HCP Terraform supports **Run Triggers** — when a source workspace applies successfully, it triggers a plan in downstream workspaces:

- `networking-workspace` → triggers → `ec2-workspace`
- This ensures VPC/subnets exist before EC2 instances are provisioned

## Best Practices for EC2 on HCP Terraform

1. **Use Sentinel Policies** — Enforce instance type restrictions, tagging requirements, and encryption at the organization level
2. **Use Variable Sets** — Share AWS credentials across multiple workspaces without duplicating them
3. **Enable Cost Estimation** — HCP shows estimated monthly cost in plan output before you apply
4. **Use Private Registry** — Publish reusable EC2 modules to your org's private module registry
5. **State Locking** — HCP automatically locks state during applies; no S3 backend config needed
6. **Drift Detection** — Enable health assessments to detect when EC2 instances drift from declared config
7. **Dynamic Credentials** — Use OIDC-based trust instead of static AWS keys for better security

## Troubleshooting

### Common Issues

- **"Error: No valid credential sources found"** — Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set as environment variables (not Terraform variables) in the workspace
- **"Error: timeout waiting for state"** — Increase timeout in lifecycle block or check instance health
- **"Error: UnauthorizedOperation"** — Your IAM user/role lacks `ec2:RunInstances` permission. Attach the `AmazonEC2FullAccess` policy or a scoped custom policy
- **Plan runs but never applies** — Check if auto-apply is disabled; manual confirmation may be required in workspace settings

## References

- [HCP Terraform Documentation](https://developer.hashicorp.com/terraform/cloud-docs)
- [AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Dynamic Provider Credentials](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/dynamic-provider-credentials)
