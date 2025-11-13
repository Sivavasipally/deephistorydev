# CLI Usage Examples

## Extracting Repository Data

### Basic Extraction

```bash
# Extract commits from repositories listed in CSV
python -m cli extract repositories.csv
```

The CSV file should have the format:
```csv
project_key,slug_name,clone_url
PROJ1,repo-name,https://bitbucket.org/project/repo.git
```

### What Gets Extracted

For each commit, the following data is collected:

**Basic Information:**
- Commit hash (SHA-1)
- Author name and email
- Committer name and email
- Commit date
- Commit message
- Branch name

**Code Metrics:**
- Lines added
- Lines deleted
- Files changed
- **Characters added** (NEW)
- **Characters deleted** (NEW)
- **File types modified** (NEW)

### Example Output

```
============================================================
  Extracting Repository: PROJ1/my-repo
============================================================

Cloning repository...
  Repository cloned to: ./repositories/PROJ1_my-repo

Extracting commits from branch: main
  Found 150 commits

Extracting pull requests...
  Found 25 pull requests

Saving to database...
  Commits saved: 150
  Pull requests saved: 25

Cleaning up...
  Repository cleaned up

============================================================
  Extraction completed successfully!
============================================================
```

## Importing Staff Details

```bash
# Import staff data from Excel
python -m cli import-staff staff_data.xlsx
```

The Excel file should contain:
- Name
- Email
- Department
- Position/Rank
- Join Date
- Status (Active/Inactive)

## Database Migration

```bash
# Run migration to add new commit detail fields
python cli/migrate_add_commit_details.py
```

Output:
```
============================================================
  Database Migration: Add Commit Details
============================================================

Checking existing schema...
Adding chars_added column...
  [OK] Added chars_added column
Adding chars_deleted column...
  [OK] Added chars_deleted column
Adding file_types column...
  [OK] Added file_types column

============================================================
  Migration completed successfully!
============================================================
```

## Querying Commit Data

### Using Python

```python
from cli.models import get_engine, get_session, Commit, Repository
from cli.config import Config

# Setup
config = Config()
engine = get_engine(config.get_db_config())
session = get_session(engine)

# Query commits with file types
commits = session.query(Commit).filter(
    Commit.file_types.like('%py%')  # Python files
).limit(10).all()

for commit in commits:
    print(f"Hash: {commit.commit_hash[:7]}")
    print(f"Author: {commit.author_name}")
    print(f"Lines: +{commit.lines_added} -{commit.lines_deleted}")
    print(f"Chars: +{commit.chars_added} -{commit.chars_deleted}")
    print(f"Types: {commit.file_types}")
    print("---")

session.close()
```

### Using SQL

```bash
# SQLite command line
sqlite3 git_history.db

# Query commits by file type
SELECT
    commit_hash,
    author_name,
    chars_added,
    chars_deleted,
    file_types,
    DATE(commit_date) as date
FROM commits
WHERE file_types LIKE '%js%'
ORDER BY commit_date DESC
LIMIT 10;

# Aggregate statistics by file type
SELECT
    file_types,
    COUNT(*) as commit_count,
    SUM(chars_added) as total_chars_added,
    SUM(chars_deleted) as total_chars_deleted
FROM commits
WHERE file_types IS NOT NULL
GROUP BY file_types
ORDER BY commit_count DESC;

# Character churn analysis
SELECT
    author_name,
    COUNT(*) as commits,
    SUM(chars_added) as chars_added,
    SUM(chars_deleted) as chars_deleted,
    SUM(chars_added + chars_deleted) as total_churn
FROM commits
GROUP BY author_name
ORDER BY total_churn DESC;
```

## API Usage

### Starting the Backend

```bash
# Start FastAPI backend server
python cli/start_backend.py
```

Server will start on: `http://localhost:8000`
- API Docs: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Fetching Commits via API

```bash
# Get all commits (with new fields)
curl http://localhost:8000/api/commits | jq

# Filter by author
curl "http://localhost:8000/api/commits?author=john" | jq

# Filter by date range
curl "http://localhost:8000/api/commits?start_date=2024-01-01&end_date=2024-12-31" | jq
```

### Python API Client

```python
import requests

# Fetch commits
response = requests.get("http://localhost:8000/api/commits", params={
    "limit": 50,
    "offset": 0
})

commits = response.json()

for commit in commits:
    print(f"Hash: {commit['commit_hash']}")
    print(f"Author: {commit['author_name']}")
    print(f"Lines: +{commit['lines_added']} -{commit['lines_deleted']}")
    print(f"Chars: +{commit['chars_added']} -{commit['chars_deleted']}")
    print(f"File Types: {commit['file_types']}")
    print(f"Message: {commit['message'][:50]}...")
    print("---")
```

## Analytics Examples

### File Type Distribution

```python
from collections import Counter
from cli.models import get_engine, get_session, Commit
from cli.config import Config

config = Config()
engine = get_engine(config.get_db_config())
session = get_session(engine)

# Get all file types
commits = session.query(Commit.file_types).filter(
    Commit.file_types != None
).all()

# Parse and count file types
file_type_counter = Counter()
for (file_types_str,) in commits:
    if file_types_str:
        types = file_types_str.split(',')
        file_type_counter.update(types)

# Display top 10
print("Top 10 File Types Modified:")
for file_type, count in file_type_counter.most_common(10):
    print(f"  {file_type}: {count} commits")

session.close()
```

### Character Productivity by Developer

```python
from sqlalchemy import func
from cli.models import get_engine, get_session, Commit
from cli.config import Config

config = Config()
engine = get_engine(config.get_db_config())
session = get_session(engine)

# Query developer productivity
results = session.query(
    Commit.author_name,
    func.count(Commit.id).label('commits'),
    func.sum(Commit.chars_added).label('chars_added'),
    func.sum(Commit.chars_deleted).label('chars_deleted')
).group_by(
    Commit.author_name
).order_by(
    func.sum(Commit.chars_added + Commit.chars_deleted).desc()
).limit(10).all()

print("Top 10 Contributors by Character Changes:")
for author, commits, added, deleted in results:
    total_churn = (added or 0) + (deleted or 0)
    print(f"{author:30} Commits: {commits:4}  Chars: +{added or 0:8} -{deleted or 0:8}  Total: {total_churn:9}")

session.close()
```

### Language-Specific Analysis

```python
from cli.models import get_engine, get_session, Commit
from cli.config import Config

config = Config()
engine = get_engine(config.get_db_config())
session = get_session(engine)

# Define language mappings
language_extensions = {
    'Python': ['py', 'pyw'],
    'JavaScript': ['js', 'jsx', 'mjs'],
    'TypeScript': ['ts', 'tsx'],
    'Java': ['java'],
    'C/C++': ['c', 'cpp', 'h', 'hpp'],
    'HTML/CSS': ['html', 'css', 'scss'],
    'Documentation': ['md', 'txt', 'rst'],
    'Config': ['json', 'yaml', 'yml', 'xml', 'ini', 'toml']
}

# Count commits per language
language_stats = {}
commits = session.query(Commit.file_types).filter(
    Commit.file_types != None
).all()

for (file_types_str,) in commits:
    if not file_types_str:
        continue

    types = set(file_types_str.split(','))

    for language, extensions in language_extensions.items():
        if any(ext in types for ext in extensions):
            language_stats[language] = language_stats.get(language, 0) + 1

# Display results
print("Commits by Programming Language:")
for language, count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"  {language:20} {count:5} commits")

session.close()
```

## Complete Workflow Example

```bash
# 1. Create repositories CSV
cat > repos.csv << EOF
project_key,slug_name,clone_url
MYPROJECT,backend-api,https://github.com/myorg/backend-api.git
MYPROJECT,frontend-app,https://github.com/myorg/frontend-app.git
EOF

# 2. Extract repository data
python -m cli extract repos.csv

# 3. Import staff details (optional)
python -m cli import-staff staff_data.xlsx

# 4. Start backend server
python cli/start_backend.py &

# 5. Start frontend (in another terminal)
cd frontend
npm run dev

# 6. Open browser to http://localhost:5173
# Navigate to different dashboard pages to view analytics

# 7. Query data via API
curl http://localhost:8000/api/commits?limit=5 | jq '.[] | {author: .author_name, types: .file_types, chars: .chars_added}'
```

## Troubleshooting

### No data appearing after extraction

```bash
# Check if commits were saved
sqlite3 git_history.db "SELECT COUNT(*) FROM commits;"

# Check if new columns exist
sqlite3 git_history.db "PRAGMA table_info(commits);"
```

### Character counts are zero

- This happens for:
  - Initial commits (no parent to diff against)
  - Merge commits with complex conflicts
  - Binary file changes
  - Commits that failed diff parsing

### File types are empty

- Check if the commit actually modified files
- Verify the repository was cloned successfully
- Check for diff parsing errors in the CLI output

### Migration already run

If you see "column already exists" messages, the migration has already been applied. This is safe to ignore.

## Performance Tips

1. **Large Repositories**: Extract during off-peak hours
2. **Network Issues**: Use `--no-cleanup` to keep cloned repos for retry
3. **Database**: Use PostgreSQL/MySQL for better performance with large datasets
4. **Selective Extraction**: Create smaller CSV files for specific repositories

## Additional Resources

- Full documentation: [README.md](../README.md)
- Database schema: [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md)
- API documentation: http://localhost:8000/api/docs (when server running)
- Enhancement details: [COMMIT_DETAILS_ENHANCEMENT.md](../COMMIT_DETAILS_ENHANCEMENT.md)
