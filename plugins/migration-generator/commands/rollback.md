# /rollback - Rollback Database Migration

Roll back the most recent database migration or to a specific version.

## Steps

1. Identify the current migration version from the migrations table
2. List recent migrations with their status (applied, pending, failed)
3. If no target version specified, default to rolling back the last applied migration
4. Read the down migration logic for the target migration
5. Check for data loss risks: dropping tables, removing columns with data
6. Warn the user about any irreversible changes and data loss potential
7. Ask for explicit confirmation before proceeding with rollback
8. Execute the down migration within a transaction
9. Verify the migration table is updated to reflect the rollback
10. Run a schema diff to confirm the rollback matches the expected state
11. Report: migration rolled back, current version, tables affected

## Rules

- Always warn about potential data loss before executing rollback
- Require explicit user confirmation for destructive rollbacks
- Use transactions to ensure atomic rollback (all or nothing)
- Never rollback in production without a backup confirmation
- Log the rollback action with timestamp and reason
- Verify foreign key constraints are satisfied after rollback
- Test the rollback on a development database first when possible
