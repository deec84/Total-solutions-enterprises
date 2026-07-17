# Database backup and restore runbook

## Production policy

Use managed PostgreSQL with encrypted automated backups, point-in-time recovery, cross-zone replication, and a retention policy approved by security and legal. Backup credentials must be separate, read-only where possible, stored in the managed secret service, and never passed in source code or logs.

Targets: recovery point objective of 15 minutes and recovery time objective of 60 minutes for the initial launch tier. Revisit these targets after usage and municipal/enterprise contracts establish stricter needs.

## Logical backup

With credentials provided through a protected `.pgpass` file or an ephemeral secret-injected environment:

```sh
pg_dump --host DB_HOST --username BACKUP_USER --dbname parkshield --format custom --file parkshield.dump
```

Encrypt the artifact using the cloud KMS, record its checksum, creation time, schema revision, PostgreSQL/PostGIS versions, and retention expiry, then upload it to versioned object storage with deletion protection.

## Restore drill

Restore only into an isolated, access-restricted database. Never overwrite production during a drill.

```sh
createdb --host RESTORE_HOST --username RESTORE_USER parkshield_restore
pg_restore --host RESTORE_HOST --username RESTORE_USER --dbname parkshield_restore --no-owner parkshield.dump
psql --host RESTORE_HOST --username RESTORE_USER --dbname parkshield_restore -c "SELECT version_num FROM alembic_version"
```

Then run the migration status check, repository integration suite, row-count reconciliation, representative PostGIS queries, and application smoke tests. Record actual RPO/RTO, checksum results, operator, date, and any remediation. Destroy the isolated copy through the approved retention workflow.

GitHub Actions performs a backup/restore drill for every backend change against disposable PostGIS databases. Production restores must be exercised at least quarterly and after material schema or infrastructure changes.
