# Incident Response Playbook

## Purpose

This playbook defines the process for responding to production incidents. It covers severity classification, roles, communication, and resolution steps. Every engineer on the on-call rotation must be familiar with this document.

## Severity Levels

### SEV-1 (Critical)
- **Definition**: Complete service outage or data loss affecting all users.
- **Response time**: 15 minutes.
- **Communication**: Immediate page to engineering lead + VP notification within 30 minutes.
- **Examples**: Primary database down, payment processing failure, data breach.

### SEV-2 (Major)
- **Definition**: Significant degradation affecting >25% of users or a critical business function.
- **Response time**: 30 minutes.
- **Communication**: Page on-call team, Slack notification to #incidents.
- **Examples**: API latency >5s, partial outage of booking system, authentication failures.

### SEV-3 (Minor)
- **Definition**: Limited impact, workaround available.
- **Response time**: 4 hours (business hours).
- **Communication**: Slack notification to #incidents.
- **Examples**: Non-critical dashboard unavailable, batch job delayed, single-region degradation.

## Roles During an Incident

| Role | Responsibility |
|------|---------------|
| **Incident Commander (IC)** | Owns the incident. Makes decisions, delegates tasks, manages communication. |
| **Technical Lead** | Diagnoses and fixes the issue. Reports findings to IC. |
| **Communications Lead** | Posts status updates to stakeholders every 15 minutes (SEV-1) or 30 minutes (SEV-2). |
| **Scribe** | Documents timeline, actions taken, and decisions in the incident channel. |

## Response Steps

### 1. Acknowledge and Classify

- Acknowledge the alert within the required response time.
- Classify severity based on the definitions above.
- Create a dedicated Slack channel: `#incident-YYYY-MM-DD-brief-description`.

### 2. Assemble the Team

- For SEV-1: Page all on-call engineers, notify engineering lead.
- For SEV-2: Page primary on-call, notify backup.
- For SEV-3: Primary on-call handles during business hours.

### 3. Diagnose

Check the following in order:

1. **CloudWatch dashboards**: Look for anomalies in error rates, latency, and throughput.
2. **Application logs**: Check for exceptions or error patterns in CloudWatch Logs Insights.
3. **Infrastructure metrics**: CPU, memory, disk, network in Grafana.
4. **Recent deployments**: Check if a deployment happened in the last 4 hours. If yes, consider rollback.
5. **External dependencies**: Verify AWS service health, third-party API status pages.

### 4. Mitigate

Priority is to restore service, not to find root cause.

- **Rollback**: If a recent deployment is suspected, rollback immediately. Don't wait for confirmation.
- **Scale up**: If resource exhaustion, add capacity.
- **Failover**: If a single component is down, failover to healthy region/AZ.
- **Circuit breaker**: If an external dependency is down, enable circuit breaker.

### 5. Resolve and Verify

- Confirm the mitigation resolved the issue (error rates back to baseline).
- Monitor for 30 minutes to ensure stability.
- Update the incident channel with resolution status.

### 6. Post-Incident

Within 48 hours of resolution:

1. Write a post-incident review (PIR) using the template in Confluence.
2. Identify root cause and contributing factors.
3. Create action items with owners and due dates.
4. Share PIR in the weekly engineering all-hands.

## Communication Templates

### Initial Status Update
> **[SEV-X] Brief description**
> **Status**: Investigating
> **Impact**: [Who is affected and how]
> **Started**: [Time in EST]
> **Next update**: [Time]

### Resolution Update
> **[SEV-X] Brief description — RESOLVED**
> **Duration**: [Start time] to [End time]
> **Root cause**: [Brief description]
> **Action items**: PIR scheduled for [date]

## Escalation Contacts

| Level | Contact | Method |
|-------|---------|--------|
| On-call engineer | Rotation schedule in PagerDuty | PagerDuty alert |
| Engineering lead | Director of Engineering | Phone + Slack DM |
| VP Engineering | VP of Platform | Phone (SEV-1 only) |

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-11-01 | M. Johnson | Initial version |
| 2026-02-15 | E. Nguyen | Added communication templates |
| 2026-04-30 | S. Lee | Updated escalation contacts |
