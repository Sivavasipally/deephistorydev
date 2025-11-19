# Quick Start Guide

## 1. Install Dependencies

```bash
pip install pymysql
```

## 2. Set Database Connection

### Windows:
```cmd
set MARIADB_URL=mysql+pymysql://username:password@host:3306/gpt
```

### Linux/Mac:
```bash
export MARIADB_URL=mysql+pymysql://username:password@host:3306/gpt
```

## 3. Test Connection

```bash
python datasync/quick_setup.py
```

This will check:
- ✓ SQLite connection
- ✓ MariaDB connection
- ✓ Required tables exist

## 4. Run Sync

```bash
python datasync/sync_sqlite_to_mariadb.py
```

## 5. Verify

Check the console output for:
- Number of records synced
- Any errors or warnings
- Location of `id_mappings.json`

## Example Output

```
================================================================================
STARTING FULL SYNCHRONIZATION
SQLite -> MariaDB/MySQL
================================================================================

Started at: 2025-01-19 10:30:00

================================================================================
SYNCING REPOSITORIES
================================================================================

Found 50 repositories to sync
  [SYNC] Repository 'my-repo' (ID: 1 -> 101)
  [SYNC] Repository 'another-repo' (ID: 2 -> 102)

Repositories: 50 synced, 0 skipped, 0 failed

...

================================================================================
SYNCHRONIZATION SUMMARY
================================================================================

OVERALL: 15000 records synced, 0 failed
================================================================================

Completed at: 2025-01-19 10:35:00

[SUCCESS] Full synchronization completed successfully!
```

## Common Issues

### Issue 1: Connection Refused
**Solution:** Check MariaDB is running
```bash
mysql -h host -u user -p
```

### Issue 2: Table Doesn't Exist
**Solution:** Run migrations
```bash
python cli/migrate_current_year_table.py
```

### Issue 3: Access Denied
**Solution:** Check credentials and user permissions
```sql
GRANT ALL PRIVILEGES ON gpt.* TO 'username'@'%';
FLUSH PRIVILEGES;
```

## Next Steps

After sync completes:
1. Update your `.env` or config to use MariaDB
2. Run: `python -m cli calculate-metrics --staff`
3. Test the web application
