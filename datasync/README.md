# Data Synchronization Tool

SQLite to MariaDB/MySQL data migration tool with proper ID mapping and foreign key constraint handling.

## Features

- ✅ **Automatic ID Remapping**: Creates new IDs in MariaDB and maintains mapping tables
- ✅ **Foreign Key Handling**: Preserves all relationships between tables
- ✅ **Duplicate Detection**: Skips existing records to allow incremental syncs
- ✅ **Transaction Safety**: Uses transactions for data integrity
- ✅ **Batch Processing**: Optimized bulk operations for large datasets
- ✅ **ID Mapping Export**: Saves ID mappings to JSON for reference
- ✅ **Detailed Logging**: Comprehensive sync statistics and error reporting

## Prerequisites

1. **MariaDB/MySQL Database** must exist with proper schema
2. **Run migrations first** to create all required tables:
   ```bash
   python cli/migrate_current_year_table.py
   ```

3. **Install PyMySQL** if not already installed:
   ```bash
   pip install pymysql
   ```

## Configuration

### Option 1: Environment Variable

Set the `MARIADB_URL` environment variable:

```bash
# Windows
set MARIADB_URL=mysql+pymysql://username:password@host:port/database

# Linux/Mac
export MARIADB_URL=mysql+pymysql://username:password@host:port/database
```

### Option 2: Configuration File

1. Copy the example configuration:
   ```bash
   copy config_example.py config.py
   ```

2. Edit `config.py` with your database credentials:
   ```python
   MARIADB_CONFIG = {
       'host': 'your_host',
       'port': 3306,
       'database': 'gpt',
       'user': 'your_username',
       'password': 'your_password',
   }
   ```

## Usage

### Full Synchronization

Run the complete sync process:

```bash
python datasync/sync_sqlite_to_mariadb.py
```

This will sync all tables in the following order:
1. Repositories
2. Authors
3. Commits
4. Pull Requests
5. PR Approvals
6. Staff Details
7. Author-Staff Mappings
8. Staff Metrics
9. Current Year Staff Metrics

### Incremental Sync

The tool automatically detects existing records and skips them, making it safe to run multiple times for incremental updates.

## Synchronization Process

### 1. ID Mapping Strategy

The tool maintains a mapping between old SQLite IDs and new MariaDB IDs:

```
SQLite DB                    MariaDB DB
---------                    ----------
Repository ID: 1    --->     Repository ID: 101
Repository ID: 2    --->     Repository ID: 102

Commit(repo_id=1)   --->     Commit(repo_id=101)
Commit(repo_id=2)   --->     Commit(repo_id=102)
```

### 2. Foreign Key Handling

All foreign key relationships are preserved:
- Commits reference the correct new Repository IDs
- Pull Requests reference the correct new Repository IDs
- PR Approvals reference the correct new Pull Request IDs

### 3. Duplicate Detection

Records are identified as duplicates using unique identifiers:
- **Repositories**: `slug`
- **Commits**: `hash` + `repository_id`
- **Pull Requests**: `pr_id` + `repository_id`
- **Authors**: `email`
- **Staff**: `bank_id_1`

### 4. Transaction Management

Each table sync operates in its own transaction:
- Successful: Changes are committed
- Failed: Changes are rolled back
- Partial failures don't affect other tables

## Output

### Console Output

Real-time progress with statistics:
```
================================================================================
SYNCING REPOSITORIES
================================================================================

Found 50 repositories to sync
  [SYNC] Repository 'my-repo' (ID: 1 -> 101)
  [SYNC] Repository 'another-repo' (ID: 2 -> 102)
  [SKIP] Repository 'existing-repo' already exists (ID: 3 -> 103)

Repositories: 2 synced, 1 skipped, 0 failed
```

### ID Mappings File

Generated `id_mappings.json` contains all ID mappings:
```json
{
  "repositories": {
    "1": 101,
    "2": 102,
    "3": 103
  },
  "commits": {
    "100": 1001,
    "101": 1002
  }
}
```

### Summary Report

Final statistics for all tables:
```
================================================================================
SYNCHRONIZATION SUMMARY
================================================================================

REPOSITORIES:
  Total:   50
  Synced:  45
  Skipped: 5
  Failed:  0

COMMITS:
  Total:   5000
  Synced:  4950
  Skipped: 50
  Failed:  0

================================================================================
OVERALL: 10000 records synced, 0 failed
================================================================================
```

## Table Sync Order

Tables are synced in dependency order:

```
1. repositories          (no dependencies)
2. authors              (no dependencies)
3. commits              (depends on: repositories)
4. pull_requests        (depends on: repositories)
5. pr_approvals         (depends on: pull_requests)
6. staff_details        (no dependencies)
7. author_mappings      (depends on: staff_details)
8. staff_metrics        (depends on: staff_details)
9. current_year_metrics (depends on: staff_details)
```

## Error Handling

### Common Issues

1. **Table doesn't exist**
   - Solution: Run migrations first
   ```bash
   python cli/migrate_current_year_table.py
   ```

2. **Connection refused**
   - Solution: Check MariaDB is running and credentials are correct
   ```bash
   mysql -h host -u user -p database
   ```

3. **Foreign key constraint failed**
   - Solution: Ensure parent records exist before child records
   - The sync order handles this automatically

4. **Duplicate key error**
   - Solution: Tool skips duplicates automatically
   - Check `id_mappings.json` for existing mappings

### Recovery

If sync fails partway through:
1. Check the console output to see which table failed
2. Fix the issue (database connection, credentials, etc.)
3. Re-run the sync - it will skip already-synced records

## Verification

After sync completes, verify data:

```sql
-- Check record counts
SELECT COUNT(*) FROM repositories;
SELECT COUNT(*) FROM commits;
SELECT COUNT(*) FROM pull_requests;
SELECT COUNT(*) FROM staff_details;
SELECT COUNT(*) FROM staff_metrics;
SELECT COUNT(*) FROM current_year_staff_metrics;

-- Check foreign key relationships
SELECT c.id, c.repository_id, r.slug
FROM commits c
JOIN repositories r ON c.repository_id = r.id
LIMIT 10;

-- Check staff metrics
SELECT bank_id_1, staff_name, total_commits, total_prs_created
FROM staff_metrics
WHERE total_commits > 0
LIMIT 10;
```

## Performance

- **Batch Processing**: Commits are processed in batches of 1000 for optimal performance
- **Index Usage**: Duplicate detection uses indexed columns for fast lookups
- **Transaction Efficiency**: Each table is committed once after all records are processed

### Estimated Sync Times

| Records    | Estimated Time |
|-----------|----------------|
| 1K        | < 1 minute     |
| 10K       | 2-5 minutes    |
| 100K      | 10-20 minutes  |
| 1M+       | 1+ hours       |

## Troubleshooting

### Enable Debug Mode

Add verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check ID Mappings

If relationships seem broken:
```python
import json
with open('datasync/id_mappings.json') as f:
    mappings = json.load(f)
    print(mappings['repositories'])
```

### Manual Verification

Compare record counts:
```bash
# SQLite
sqlite3 git_history.db "SELECT COUNT(*) FROM commits;"

# MariaDB
mysql -u user -p -e "SELECT COUNT(*) FROM gpt.commits;"
```

## Notes

- **Primary Keys**: All tables use auto-incrementing primary keys in MariaDB
- **Unique Constraints**: Natural keys (slug, hash, email, bank_id) are used for duplicate detection
- **Data Integrity**: Foreign key constraints are maintained throughout the process
- **Idempotent**: Safe to run multiple times - skips existing records

## Support

For issues or questions:
1. Check the console output for specific error messages
2. Verify database connection and credentials
3. Check `id_mappings.json` for relationship tracking
4. Review MariaDB error logs for database-specific issues
