# Server Restart Procedure

## Purpose

This document describes the standard operating procedure for restarting application servers in the production environment. All team members performing server restarts must follow this procedure to ensure minimal disruption to services.

## Pre-Restart Checklist

Before restarting any server, complete the following checks:

1. **Verify the restart window**: Server restarts should only be performed during approved maintenance windows (Tuesdays and Thursdays, 2:00 AM - 4:00 AM EST) unless an emergency restart is approved by the on-call lead.
2. **Check active connections**: Run `netstat -an | grep ESTABLISHED | wc -l` to verify the current connection count. If connections exceed 500, notify the load balancer team to drain the server first.
3. **Verify backup status**: Confirm that the most recent backup completed successfully by checking the backup dashboard in CloudWatch. Never restart a server with a failed or in-progress backup.
4. **Notify stakeholders**: Post in the #ops-notifications Slack channel with the server name, reason for restart, and expected duration.

## Restart Steps

### Standard Application Server Restart

1. SSH into the server using the bastion host:
   ```
   ssh -J bastion.internal app-server-01.internal
   ```
2. Stop the application gracefully:
   ```
   sudo systemctl stop app-service
   ```
3. Wait for all in-flight requests to complete (max 30 seconds):
   ```
   while [ $(curl -s localhost:8080/health | jq '.active_requests') -gt 0 ]; do sleep 5; done
   ```
4. Verify the application has stopped:
   ```
   sudo systemctl status app-service
   ```
5. Start the application:
   ```
   sudo systemctl start app-service
   ```
6. Verify health check passes:
   ```
   curl -f localhost:8080/health
   ```
7. Monitor logs for 5 minutes:
   ```
   sudo journalctl -u app-service -f --since "5 minutes ago"
   ```

### Database Server Restart

Database server restarts require additional approval from the DBA team. Contact the on-call DBA before proceeding.

1. Ensure all replication is caught up: check replication lag is < 1 second.
2. Failover to the standby server first.
3. Restart the primary after confirming the standby is serving traffic.
4. After restart, verify replication resumes within 60 seconds.

## Post-Restart Verification

After any server restart:

1. Verify the application health endpoint returns 200 OK.
2. Check that the server appears healthy in the load balancer target group.
3. Monitor error rates in Grafana for 15 minutes post-restart.
4. Update the #ops-notifications Slack channel with completion status.

## Escalation

If the server does not come back healthy within 10 minutes:

1. Page the on-call engineering lead via PagerDuty.
2. Do NOT attempt more than 2 restart cycles without escalation.
3. If the issue persists, engage the incident response process (see Incident Response Playbook).

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-01-15 | J. Smith | Initial version |
| 2026-03-20 | E. Nguyen | Added database restart section |
| 2026-05-10 | K. Patel | Updated maintenance windows |
