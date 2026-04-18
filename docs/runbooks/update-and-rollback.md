# Update and Rollback Runbook

## Update

1. Back up the database first.
2. Pull the new git revision.
3. Review the changelog or commit diff.
4. Redeploy the stack.
5. Run the smoke checks.

```bash
cd /opt/endurasync
git pull
cd deploy
docker compose up -d --build
```

## Rollback

1. Stop the stack.
2. Check out the previous known-good commit.
3. Restore the prior backup if the schema or data changed.
4. Start the stack again.

```bash
cd /opt/endurasync
git checkout <previous-commit>
cd deploy
docker compose up -d --build
```

## Rollback rule

If the update included a schema change and the new migration is not reversible in place, restore the matching database backup instead of trying to hand-edit tables.
