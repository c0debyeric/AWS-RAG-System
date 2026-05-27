# AWS Account Onboarding Guide

## Purpose

This document describes the process for onboarding new AWS accounts into our multi-account organization. All new accounts must follow this standard process to ensure proper governance, security baselines, and network connectivity.

## Prerequisites

Before requesting a new account:

1. Business justification approved by VP-level sponsor.
2. Budget code assigned by Finance team.
3. Account naming convention confirmed with Cloud Team.

## Account Naming Convention

Format: `{business-unit}-{environment}-{purpose}`

Examples:
- `engineering-prod-booking-api`
- `analytics-dev-data-lake`
- `security-prod-guardduty`

## Onboarding Steps

### Step 1: Account Creation via Control Tower

New accounts are created through AWS Control Tower Account Factory:

1. Navigate to AWS Control Tower → Account Factory in the management account.
2. Fill in the account details:
   - Account name: follow naming convention above
   - Account email: aws+{account-name}@example.com (unique per account)
   - Organizational Unit: select the appropriate OU (Prod, Non-Prod, Sandbox, Security)
3. Submit and wait for provisioning (typically 15-20 minutes).

### Step 2: Apply SCPs

Service Control Policies are applied automatically based on the OU:

| OU | SCPs Applied |
|----|-------------|
| Production | Deny region outside us-east-1/us-west-2, deny root user actions, require encryption, deny public S3 |
| Non-Production | Deny region outside us-east-1, deny root user actions, budget limit enforcement |
| Sandbox | Deny region outside us-east-1, auto-cleanup after 72 hours, $100/month budget cap |
| Security | Full access (managed by security team) |

### Step 3: Network Connectivity

All accounts are connected to the Transit Gateway for internal communication:

1. Cloud Team creates a VPC in the new account (standard CIDR allocation from IPAM).
2. VPC is attached to the Transit Gateway in the network account.
3. Route tables are updated to allow traffic to shared services (DNS, monitoring, bastion).
4. Security groups are created with default deny-all ingress, allow internal egress.

Standard VPC CIDR allocation:
- Production: 10.1.0.0/16 - 10.50.0.0/16
- Non-Production: 10.100.0.0/16 - 10.150.0.0/16
- Sandbox: 10.200.0.0/16 - 10.250.0.0/16

### Step 4: Security Baselines

The following services are enabled automatically via Terraform:

- **GuardDuty**: Threat detection (findings sent to security account).
- **CloudTrail**: API logging (logs sent to centralized logging account).
- **Config**: Resource compliance monitoring.
- **SecurityHub**: Aggregated security findings.
- **IAM Access Analyzer**: External access monitoring.

### Step 5: Monitoring Setup

1. CloudWatch cross-account observability is configured.
2. Default dashboards are created for compute, storage, and network metrics.
3. Budget alerts are set up (50%, 80%, 100% thresholds).
4. SNS topics for alerts are connected to PagerDuty.

### Step 6: IAM Configuration

1. SSO roles are configured via AWS IAM Identity Center:
   - `AdministratorAccess`: Account owner only (1-2 people).
   - `PowerUserAccess`: Engineers who need to deploy resources.
   - `ReadOnlyAccess`: Auditors, managers, support staff.
2. Service roles are created via Terraform modules.
3. All human access must go through SSO — no IAM users with long-lived credentials.

### Step 7: Cost Management

1. Cost allocation tags are enforced: `Environment`, `Team`, `Project`, `CostCenter`.
2. Untagged resources trigger a Config rule violation.
3. Monthly cost reports are sent to the account owner and finance team.
4. Anomaly detection alerts trigger when daily spend exceeds 150% of the 7-day average.

## Post-Onboarding Checklist

- [ ] Account created and accessible via SSO.
- [ ] VPC created and connected to Transit Gateway.
- [ ] Security baselines verified (GuardDuty, CloudTrail, Config active).
- [ ] Budget alerts configured and tested.
- [ ] At least one test deployment successful.
- [ ] Account documented in the account registry (Confluence).

## Account Decommissioning

When an account is no longer needed:

1. Notify all account users 30 days in advance.
2. Export any data that needs to be retained.
3. Remove the Transit Gateway attachment.
4. Move the account to the "Suspended" OU (all SCPs deny everything).
5. After 90 days, close the account via Organizations.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-06-01 | Cloud Team | Initial version |
| 2025-12-15 | E. Nguyen | Added IPAM allocation ranges |
| 2026-03-01 | J. Park | Updated SCP descriptions |
| 2026-05-15 | Cloud Team | Added decommissioning section |
