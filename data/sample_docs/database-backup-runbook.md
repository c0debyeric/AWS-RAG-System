# Database Backup and Recovery Runbook

## Purpose

This runbook covers the procedures for database backup, verification, and recovery for all production PostgreSQL databases. It is intended for the database administration team and on-call engineers.

## Backup Strategy

### Automated Backups

All production databases use the following automated backup strategy:

| Backup Type | Frequency | Retention | Storage |
|------------|-----------|-----------|---------|
| Automated RDS snapshots | Daily at 3:00 AM EST | 30 days | RDS managed |
| Point-in-time recovery (PITR) | Continuous (5-minute RPO) | 7 days | RDS transaction logs |
| Cross-region snapshot copy | Daily at 5:00 AM EST | 14 days | us-west-2 |
| Logical backup (pg_dump) | Weekly (Sunday 2:00 AM) | 90 days | S3 (versioned bucket) |

### Manual Backup Procedure

Before any maintenance operation (schema changes, major upgrades, data migrations), take a manual snapshot:

```bash
# Create a manual RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier prod-postgres-primary \
  --db-snapshot-identifier manual-pre-migration-$(date +%Y%m%d-%H%M) \
  --profile shared --region us-east-1

# Verify snapshot creation
aws rds describe-db-snapshots \
  --db-snapshot-identifier manual-pre-migration-$(date +%Y%m%d-%H%M) \
  --profile shared --region us-east-1
```

Wait for the snapshot status to change from "creating" to "available" before proceeding with maintenance. This typically takes 5-15 minutes depending on database size.

## Backup Verification

### Weekly Verification Process

Every Monday, the on-call DBA must verify backup integrity:

1. **Check automated snapshot**: Verify the most recent automated snapshot exists and is in "available" state.
2. **Check PITR**: Verify the latest restorable time is within the last 5 minutes.
3. **Restore test**: Restore the latest snapshot to a test instance and run the verification query suite.

```bash
# Check latest automated snapshot
aws rds describe-db-snapshots \
  --db-instance-identifier prod-postgres-primary \
  --snapshot-type automated \
  --query 'DBSnapshots | sort_by(@, &SnapshotCreateTime) | [-1]' \
  --profile shared --region us-east-1

# Check latest restorable time
aws rds describe-db-instances \
  --db-instance-identifier prod-postgres-primary \
  --query 'DBInstances[0].LatestRestorableTime' \
  --profile shared --region us-east-1
```

### Verification Query Suite

After restoring a snapshot to a test instance, run:

```sql
-- Check total row counts for critical tables
SELECT 'bookings' as table_name, COUNT(*) as row_count FROM bookings
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'inventory', COUNT(*) FROM inventory;

-- Verify data freshness
SELECT MAX(updated_at) as latest_update FROM bookings;
SELECT MAX(created_at) as latest_customer FROM customers;

-- Check for data corruption
SELECT COUNT(*) FROM bookings WHERE total_amount < 0;
SELECT COUNT(*) FROM customers WHERE email IS NULL;
```

## Recovery Procedures

### Scenario 1: Point-in-Time Recovery (Data Corruption)

Use when: Accidental data deletion or corruption is detected, and you need to recover to a specific point in time.

1. Identify the exact time before the corruption occurred (check CloudWatch logs, application logs).
2. Create a new instance from PITR:
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier prod-postgres-primary \
     --target-db-instance-identifier prod-postgres-recovery \
     --restore-time "2026-05-25T14:30:00Z" \
     --db-instance-class db.r6g.xlarge \
     --profile shared --region us-east-1
   ```
3. Verify the recovered data is correct using the verification query suite.
4. Extract the needed data from the recovery instance.
5. Apply the extracted data to the production database.
6. Terminate the recovery instance.

### Scenario 2: Full Database Failure

Use when: The primary database instance is unrecoverable.

1. Promote the read replica to primary (if available):
   ```bash
   aws rds promote-read-replica \
     --db-instance-identifier prod-postgres-replica \
     --profile shared --region us-east-1
   ```
2. Update the application connection string to point to the new primary.
3. If no replica is available, restore from the latest automated snapshot.
4. Monitor replication lag and application health.

### Scenario 3: Cross-Region Recovery (Regional Outage)

Use when: The entire us-east-1 region is unavailable.

1. Copy the latest cross-region snapshot to a new instance in us-west-2.
2. Update DNS to point to the us-west-2 endpoint.
3. Accept that data since the last cross-region copy (up to 24 hours) may be lost.
4. Document the data loss window in the incident report.

## Connection Strings

| Environment | Endpoint | Port | Database |
|------------|----------|------|----------|
| Production (primary) | prod-postgres-primary.cluster-xxxxx.us-east-1.rds.amazonaws.com | 5432 | production |
| Production (read replica) | prod-postgres-replica.cluster-ro-xxxxx.us-east-1.rds.amazonaws.com | 5432 | production |
| Staging | staging-postgres.cluster-xxxxx.us-east-1.rds.amazonaws.com | 5432 | staging |

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-08-15 | DBA Team | Initial version |
| 2026-01-20 | E. Nguyen | Added cross-region recovery section |
| 2026-03-15 | R. Kumar | Updated retention policies |
