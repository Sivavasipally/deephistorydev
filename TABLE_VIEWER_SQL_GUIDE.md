# Table Viewer & SQL Executor Guide

## Overview

The dashboard now includes two powerful new features for direct database interaction:
1. **Table Viewer** - Browse and export data from all database tables
2. **SQL Executor** - Execute custom SQL queries with sample templates

## Table Viewer

### Features

✅ **Tables Overview**
- View all available tables with row counts
- Quick summary of database contents

✅ **Interactive Table Browser**
- Select any table from dropdown
- Configurable row limit (10 to 10,000 rows)
- Real-time data loading with progress indicator

✅ **Table Statistics**
- Total rows, columns, and memory usage
- Column-level information (data types, null counts)
- Expandable column details panel

✅ **Data Export**
- Download table data as CSV
- Timestamped filenames for versioning

### Available Tables

| Table Name | Description |
|------------|-------------|
| **repositories** | Git repositories with project keys and clone URLs |
| **commits** | All commits with author, date, lines changed, files |
| **pull_requests** | PRs with title, description, state, branches |
| **pr_approvals** | PR approval records with approver and timestamp |
| **staff_details** | Staff information with 71 fields (HR data) |

### Usage

1. Navigate to **Table Viewer** from sidebar
2. Review the tables overview to see row counts
3. Select a table from the dropdown
4. Set row limit (default: 1,000)
5. Click **Load Table Data**
6. Review statistics and column information
7. Download as CSV if needed

### Example Workflow

```
1. Select "commits" table
2. Set limit to 500 rows
3. Click "Load Table Data"
4. Review column information to understand schema
5. Download commits_20250106_143022.csv
```

## SQL Executor

### Features

✅ **Custom SQL Queries**
- Execute any SQL query against the database
- Full SQLite syntax support
- Real-time query execution

✅ **Sample Query Templates**
- 6 pre-built query examples
- One-click loading of sample queries
- Learn SQL patterns from examples

✅ **Database Schema Reference**
- Complete schema documentation
- Table relationships and foreign keys
- Field types and constraints

✅ **Safety Features**
- Warning for destructive queries (UPDATE, DELETE, INSERT, DROP)
- Read-only queries recommended
- Error handling with detailed messages

✅ **Results Analysis**
- Row/column/memory statistics
- Downloadable results as CSV
- Full dataframe display

### Sample Queries

#### 1. Select All Repositories
```sql
SELECT * FROM repositories LIMIT 10;
```

#### 2. Top 10 Authors by Commits
```sql
SELECT author_name, COUNT(*) as commit_count
FROM commits
GROUP BY author_name
ORDER BY commit_count DESC
LIMIT 10;
```

#### 3. PRs with Most Approvals
```sql
SELECT pr.pr_number, pr.title, pr.author_name,
       COUNT(pa.id) as approval_count
FROM pull_requests pr
LEFT JOIN pr_approvals pa ON pr.id = pa.pull_request_id
GROUP BY pr.id
ORDER BY approval_count DESC
LIMIT 10;
```

#### 4. Commits by Month
```sql
SELECT strftime('%Y-%m', commit_date) as month,
       COUNT(*) as commits,
       SUM(lines_added) as total_added,
       SUM(lines_deleted) as total_deleted
FROM commits
GROUP BY month
ORDER BY month DESC;
```

#### 5. Staff by Department
```sql
SELECT tech_unit, COUNT(*) as staff_count
FROM staff_details
GROUP BY tech_unit
ORDER BY staff_count DESC;
```

#### 6. Join Commits with Repositories
```sql
SELECT r.project_key, r.slug_name,
       COUNT(c.id) as commit_count,
       SUM(c.lines_added + c.lines_deleted) as total_lines_changed
FROM repositories r
LEFT JOIN commits c ON r.id = c.repository_id
GROUP BY r.id
ORDER BY commit_count DESC;
```

### Database Schema

#### repositories
```sql
id              INTEGER PRIMARY KEY
project_key     VARCHAR(255)
slug_name       VARCHAR(255)
clone_url       VARCHAR(500)
created_at      DATETIME
```

#### commits
```sql
id              INTEGER PRIMARY KEY
repository_id   INTEGER (FK -> repositories.id)
commit_hash     VARCHAR(40) UNIQUE
author_name     VARCHAR(255)
author_email    VARCHAR(255)
committer_name  VARCHAR(255)
committer_email VARCHAR(255)
commit_date     DATETIME
message         TEXT
lines_added     INTEGER
lines_deleted   INTEGER
files_changed   INTEGER
branch          VARCHAR(255)
```

#### pull_requests
```sql
id              INTEGER PRIMARY KEY
repository_id   INTEGER (FK -> repositories.id)
pr_number       INTEGER
title           VARCHAR(500)
description     TEXT
author_name     VARCHAR(255)
author_email    VARCHAR(255)
created_date    DATETIME
merged_date     DATETIME
state           VARCHAR(50)
source_branch   VARCHAR(255)
target_branch   VARCHAR(255)
lines_added     INTEGER
lines_deleted   INTEGER
commits_count   INTEGER
```

#### pr_approvals
```sql
id              INTEGER PRIMARY KEY
pull_request_id INTEGER (FK -> pull_requests.id)
approver_name   VARCHAR(255)
approver_email  VARCHAR(255)
approval_date   DATETIME
```

#### staff_details
```sql
id                          INTEGER PRIMARY KEY
bank_id_1                   VARCHAR(50)
staff_id                    VARCHAR(50)
staff_name                  VARCHAR(255)
email_address               VARCHAR(255)
staff_start_date            DATE
staff_end_date              DATE
tech_unit                   VARCHAR(255)
platform_name               VARCHAR(255)
staff_type                  VARCHAR(100)
... (71 fields total - see models.py for complete list)
```

## Advanced SQL Examples

### Find Active Contributors in Last 6 Months
```sql
SELECT
    author_name,
    COUNT(*) as commits,
    SUM(lines_added + lines_deleted) as total_lines,
    MIN(commit_date) as first_commit,
    MAX(commit_date) as last_commit
FROM commits
WHERE commit_date >= date('now', '-6 months')
GROUP BY author_name
HAVING commits >= 5
ORDER BY commits DESC;
```

### PR Approval Rate by Repository
```sql
SELECT
    r.project_key || '/' || r.slug_name as repository,
    COUNT(DISTINCT pr.id) as total_prs,
    COUNT(DISTINCT pa.pull_request_id) as prs_with_approvals,
    ROUND(100.0 * COUNT(DISTINCT pa.pull_request_id) / COUNT(DISTINCT pr.id), 2) as approval_rate
FROM repositories r
LEFT JOIN pull_requests pr ON r.id = pr.repository_id
LEFT JOIN pr_approvals pa ON pr.id = pa.pull_request_id
GROUP BY r.id
ORDER BY total_prs DESC;
```

### Top PR Approvers with Details
```sql
SELECT
    pa.approver_name,
    pa.approver_email,
    COUNT(*) as total_approvals,
    COUNT(DISTINCT pr.repository_id) as repos_reviewed,
    MIN(pa.approval_date) as first_approval,
    MAX(pa.approval_date) as last_approval
FROM pr_approvals pa
JOIN pull_requests pr ON pa.pull_request_id = pr.id
GROUP BY pa.approver_name
ORDER BY total_approvals DESC
LIMIT 20;
```

### Commit Activity Heatmap Data
```sql
SELECT
    strftime('%Y', commit_date) as year,
    strftime('%m', commit_date) as month,
    strftime('%w', commit_date) as day_of_week,
    COUNT(*) as commits
FROM commits
GROUP BY year, month, day_of_week
ORDER BY year DESC, month DESC;
```

### Staff and Commit Correlation
```sql
SELECT
    sd.staff_name,
    sd.tech_unit,
    sd.email_address,
    COUNT(c.id) as commit_count,
    SUM(c.lines_added) as total_added,
    SUM(c.lines_deleted) as total_deleted
FROM staff_details sd
LEFT JOIN commits c ON sd.email_address = c.author_email
WHERE sd.staff_status = 'Active'
GROUP BY sd.staff_id
HAVING commit_count > 0
ORDER BY commit_count DESC;
```

## Best Practices

### Table Viewer
1. **Start Small**: Use low row limits (100-500) for initial exploration
2. **Check Statistics**: Review memory usage before loading large tables
3. **Export Wisely**: Download only the data you need
4. **Column Info**: Expand column information to understand data types

### SQL Executor
1. **Test Queries**: Start with LIMIT clause to test query logic
2. **Use Samples**: Learn from sample queries before writing custom ones
3. **Check Schema**: Reference schema information when joining tables
4. **Safe Queries**: Prefer SELECT over UPDATE/DELETE/INSERT
5. **Download Results**: Save query results for further analysis

## Troubleshooting

### Table Viewer Issues

**Empty Table**
- Verify data has been imported for that table
- Check row count in overview (might be 0)

**Slow Loading**
- Reduce row limit
- Large tables (staff_details with 71 columns) take longer

**Memory Warning**
- Use smaller row limits for tables with many columns
- Download and process externally if needed

### SQL Executor Issues

**Query Error**
- Check SQL syntax (SQLite-specific)
- Verify table and column names
- Review schema in expander

**Slow Query**
- Add WHERE clause to filter data
- Use LIMIT to restrict results
- Avoid complex joins on large tables

**No Results**
- Query may be valid but return empty set
- Check WHERE conditions
- Verify data exists in tables

## Security Notes

⚠️ **Important**:
- The SQL Executor has full database access
- Destructive queries (UPDATE, DELETE, DROP) are allowed but warned
- In production, consider restricting to read-only access
- Always backup database before running destructive queries

## Integration with Other Features

### Workflow Example 1: Research Before Analysis
```
1. Use Table Viewer to explore commits table
2. Identify interesting patterns in data
3. Switch to SQL Executor to write custom query
4. Export results for external analysis
5. Return to "Authors Analytics" for visual insights
```

### Workflow Example 2: Staff-Commit Linking
```
1. Import staff details via CLI: python cli.py import-staff staff.xlsx
2. Use Table Viewer to verify staff_details imported correctly
3. Use SQL Executor to run staff-commit correlation query
4. Download results to identify active developers
5. Cross-reference with "Detailed Commits View"
```

### Workflow Example 3: PR Analysis
```
1. View PRs in "Detailed PRs View"
2. Notice patterns in approval rates
3. Switch to SQL Executor for deeper analysis
4. Run "PRs with Most Approvals" query
5. Export results and share with team
```

## Performance Tips

### For Large Datasets (10K+ rows)

1. **Use Pagination**
   ```sql
   SELECT * FROM commits ORDER BY commit_date DESC LIMIT 1000 OFFSET 0;
   ```

2. **Filter Early**
   ```sql
   SELECT * FROM commits WHERE commit_date >= '2024-01-01' LIMIT 5000;
   ```

3. **Aggregate Instead of Raw Data**
   ```sql
   SELECT author_name, COUNT(*) FROM commits GROUP BY author_name;
   ```

4. **Index-Friendly Queries**
   - Use indexed columns (id, commit_hash, etc.) in WHERE clauses
   - Avoid functions on indexed columns

## Future Enhancements

Potential additions for future versions:
- Query history and favorites
- Visual query builder
- Export to Excel with formatting
- Scheduled query execution
- Query result caching
- Database backup/restore via UI

---

**Quick Start**:
```bash
streamlit run dashboard.py
```

Navigate to "Table Viewer" or "SQL Executor" from the sidebar to get started!
