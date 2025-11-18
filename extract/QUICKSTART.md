# Quick Start Guide - Git History Extractor

Get started in 5 minutes! 🚀

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**What gets installed:**
- `sqlalchemy` - Database ORM
- `pymysql` - MySQL connector
- `cryptography` - Security library
- `requests` - HTTP library
- `click` - CLI framework
- `python-dotenv` - Environment variables
- `gitpython` - Git operations

## Step 2: Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Minimum Required Configuration:**

```env
# Database
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=git_history

# Bitbucket
BITBUCKET_URL=https://bitbucket.yourcompany.com
BITBUCKET_USERNAME=john.doe
BITBUCKET_APP_PASSWORD=ATBBxxxxxxxxx
```

## Step 3: Create Repository List

Create `repos.csv` with your repositories:

```csv
project_key,repo_slug
MYPROJECT,backend-api
MYPROJECT,frontend-app
DATAENG,data-pipeline
```

**Tips:**
- One repository per line
- Use actual Bitbucket project keys and repo slugs
- Check Bitbucket URL: `https://bitbucket.com/projects/MYPROJECT/repos/backend-api`
  - Project Key: `MYPROJECT`
  - Repo Slug: `backend-api`

## Step 4: Run Extraction

```bash
python -m cli extract repos.csv
```

**That's it!** The tool will:
1. ✅ Create database tables automatically
2. ✅ Clone each repository temporarily
3. ✅ Extract all commits from Git history
4. ✅ Fetch pull requests from Bitbucket API
5. ✅ Save everything to database
6. ✅ Clean up temporary files

## Common Options

### Extract Specific Branches

```bash
python -m cli extract repos.csv --branches main,develop
```

### Extract Date Range

```bash
python -m cli extract repos.csv --since 2024-01-01 --until 2024-12-31
```

### Auto-Map Authors to Staff

**Prerequisites:** Import staff data first
```bash
python -m cli import-staff staff.xlsx
```

**Then extract with auto-mapping:**
```bash
python -m cli extract repos.csv --auto-map --company-domains company.com
```

## Output Example

```
================================================================================
EXTRACTING GIT HISTORY FROM BITBUCKET
================================================================================
Mode: Extract repositories
CSV File: repos.csv
Database: MySQL (git_history)

Reading repositories from CSV...
Found 3 repositories

[1/3] Processing: MYPROJECT/backend-api
  ✓ Repository cloned
  ✓ Extracted 1,234 commits
  ✓ Fetched 45 pull requests
  ✓ Saved to database

[2/3] Processing: MYPROJECT/frontend-app
  ✓ Repository cloned
  ✓ Extracted 876 commits
  ✓ Fetched 32 pull requests
  ✓ Saved to database

[3/3] Processing: DATAENG/data-pipeline
  ✓ Repository cloned
  ✓ Extracted 543 commits
  ✓ Fetched 18 pull requests
  ✓ Saved to database

================================================================================
EXTRACTION COMPLETE
================================================================================
Total Repositories: 3
Total Commits: 2,653
Total Pull Requests: 95
Time Elapsed: 8m 34s
================================================================================
```

## Verification

Check your database:

```sql
-- Check repositories
SELECT * FROM repositories;

-- Check commits count
SELECT COUNT(*) FROM commits;

-- Check pull requests
SELECT COUNT(*) FROM pull_requests;

-- Check recent commits
SELECT author_name, COUNT(*) as commits
FROM commits
GROUP BY author_name
ORDER BY commits DESC
LIMIT 10;
```

## Troubleshooting

### "Authentication failed"
- Verify BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD in `.env`
- Check app password has "Repositories: Read" permission

### "Database connection failed"
- Ensure database server is running
- Verify DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
- Create the database if it doesn't exist: `CREATE DATABASE git_history;`

### "Repository not found"
- Check project_key and repo_slug in repos.csv
- Verify you have read access to the repository
- Confirm repository exists in Bitbucket

### "Git clone failed"
- Check network connectivity to Bitbucket server
- Verify Git is installed: `git --version`
- Ensure sufficient disk space for temporary clones

## Next Steps

After extraction:

1. **Check Unmapped Authors** (if using auto-mapping):
   ```bash
   python -m cli auto-map --show-unmapped
   ```

2. **Calculate Staff Metrics**:
   ```bash
   python -m cli calculate-metrics --staff
   ```

3. **View Data**:
   - Use SQL queries to analyze the data
   - Connect BI tools to the database
   - Build dashboards

## Need More Help?

- Read the full [README.md](README.md) for detailed documentation
- Check command help: `python -m cli extract --help`
- Review `.env.example` for all configuration options

---

**You're all set! 🎉**
