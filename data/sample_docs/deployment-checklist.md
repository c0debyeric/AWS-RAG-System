# Deployment Checklist

## Purpose

This checklist must be completed before, during, and after every production deployment. No exceptions. Skip a step, and you own the incident that follows.

## Pre-Deployment

- [ ] All unit tests pass in CI (green build on `main`).
- [ ] Integration tests pass in staging environment.
- [ ] Code review approved by at least 2 engineers.
- [ ] Security scan (Trivy, Checkov) shows no critical or high vulnerabilities.
- [ ] Database migrations tested in staging (if applicable).
- [ ] Rollback plan documented and tested.
- [ ] Deployment window confirmed (not during peak hours: 9 AM - 5 PM EST).
- [ ] Stakeholders notified in #deployments Slack channel.

## Deployment Steps

### 1. Pre-Flight Check

```bash
# Verify you're deploying the correct commit
git log --oneline -5

# Verify staging matches what you're deploying
kubectl get pods -n staging -o wide

# Check current production health
curl -f https://api.internal/health
```

### 2. Deploy to Production

We use a blue-green deployment strategy:

1. Deploy the new version to the green environment:
   ```bash
   kubectl apply -f k8s/production/ --dry-run=client
   kubectl apply -f k8s/production/
   ```

2. Wait for all pods to be ready:
   ```bash
   kubectl rollout status deployment/app-server -n production --timeout=300s
   ```

3. Run smoke tests against the green environment:
   ```bash
   ./scripts/smoke-test.sh --env production-green
   ```

4. Switch traffic to green:
   ```bash
   kubectl patch service app-lb -n production -p '{"spec":{"selector":{"version":"green"}}}'
   ```

### 3. Verify

- [ ] Health endpoint returns 200 on all pods.
- [ ] Error rate in Grafana is at or below baseline.
- [ ] Latency P95 is within acceptable range (<500ms).
- [ ] No new errors in CloudWatch Logs for 10 minutes.
- [ ] Database connections are stable (no connection pool exhaustion).

### 4. Post-Deployment

- [ ] Update #deployments Slack channel with deployment status.
- [ ] Monitor Grafana dashboards for 30 minutes.
- [ ] If any anomaly detected, initiate rollback immediately.
- [ ] Close the deployment ticket in Jira.

## Rollback Procedure

If any post-deployment check fails:

1. Switch traffic back to the blue (previous) environment:
   ```bash
   kubectl patch service app-lb -n production -p '{"spec":{"selector":{"version":"blue"}}}'
   ```
2. Verify health checks pass on the blue environment.
3. Notify #deployments and #incidents channels.
4. Create a post-deployment incident ticket.

**Rule**: Never attempt to fix forward during a failed deployment. Rollback first, fix later.

## Database Migration Guidelines

- Migrations must be backward-compatible (no column drops, no renames in same deploy).
- Run migrations BEFORE deploying the application code.
- Always test migrations against a production-size dataset in staging.
- Keep a rollback migration script ready.

## Emergency Deployments

Emergency deployments (hotfixes) bypass the normal deployment window but NOT the checklist:

1. Get verbal approval from the engineering lead.
2. Complete all pre-deployment checks.
3. Deploy with at least 1 other engineer watching.
4. Post-deployment monitoring extended to 1 hour.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-09-01 | T. Williams | Initial version |
| 2026-01-10 | E. Nguyen | Added blue-green deployment steps |
| 2026-04-15 | A. Garcia | Added database migration guidelines |
