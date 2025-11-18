# Git History Extractor for Bitbucket

This is a standalone tool to extract Git commit history and pull request data from Bitbucket repositories and store it in a database.

## Prerequisites

- Python 3.8 or higher
- Git installed on your system
- Bitbucket Server/Data Center access with credentials
- MySQL/PostgreSQL/SQL Server database

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file** with your configuration:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file** with your actual credentials:
   ```env
   # Database Configuration
   DB_TYPE=mysql              # mysql, postgresql, or mssql
   DB_HOST=localhost
   DB_PORT=3306              # 3306 for MySQL, 5432 for PostgreSQL, 1433 for MSSQL
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=git_history

   # Bitbucket Configuration
   BITBUCKET_URL=https://bitbucket.yourcompany.com
   BITBUCKET_USERNAME=your_username
   BITBUCKET_APP_PASSWORD=your_app_password
   ```

## Bitbucket App Password Setup

1. Go to Bitbucket → Profile → Personal Settings → App passwords
2. Create new app password with these permissions:
   - **Repositories**: Read
   - **Pull requests**: Read
3. Copy the generated password to your `.env` file

## Database Setup

The tool will automatically create the required tables on first run:
- `repositories` - Repository metadata
- `commits` - Commit history
- `pull_requests` - Pull request information
- `pr_approvals` - PR approval records

## Preparing Repository List

Create a `repos.csv` file with the repositories you want to extract:

**Format:**
```csv
project_key,repo_slug
PROJECT1,backend-api
PROJECT1,frontend-app
PROJECT2,mobile-app
```

**Example:** See `repos.csv.example`

## Usage

### Basic Extraction

Extract all repositories listed in repos.csv:

```bash
python -m cli extract repos.csv
```

### With Options

**Filter by branches:**
```bash
python -m cli extract repos.csv --branches main,develop,release
```

**Date range filtering:**
```bash
python -m cli extract repos.csv --since 2024-01-01 --until 2024-12-31
```

**Combined options:**
```bash
python -m cli extract repos.csv \
  --branches main,develop \
  --since 2024-01-01 \
  --until 2024-12-31
```

## Command Reference

### Extract Command

```bash
python -m cli extract <csv_file> [OPTIONS]
```

**Options:**
- `--no-cleanup` - Keep cloned repositories
- `--branches TEXT` - Comma-separated list of branches to extract (default: all)
- `--since TEXT` - Start date (YYYY-MM-DD)
- `--until TEXT` - End date (YYYY-MM-DD)

## What Gets Extracted

### From Git History:
- Commit hash
- Author name and email
- Committer name
- Commit date and message
- Lines added/deleted
- Files changed
- Character changes
- File types
- Branch information

### From Bitbucket API:
- Pull request number, title, description
- PR author, state, dates
- Source and target branches
- Commits in PR
- Approvals and reviewers
- Lines added/deleted in PR

## Workflow Example

```bash
# Extract repository data
python -m cli extract repos.csv
```

## Troubleshooting

### Git Clone Fails
- Check network connectivity to Bitbucket server
- Verify credentials in `.env` file
- Ensure repository exists and you have read access

### Database Connection Fails
- Verify database is running
- Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD in `.env`
- Ensure database exists (create it if needed)

### API Rate Limits
- Bitbucket may rate-limit API calls
- The tool includes retry logic with exponential backoff
- For large extractions, run in batches


## Files Structure

```
extract/
├── cli/
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # Main CLI with extract command
│   ├── config.py             # Configuration management
│   ├── models.py             # Database models
│   ├── git_analyzer.py       # Git extraction logic
│   └── bitbucket_api.py      # Bitbucket API integration
├── .env.example              # Example configuration
├── repos.csv.example         # Example repository list
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Performance

- **Small repos** (< 1000 commits): 1-2 minutes
- **Medium repos** (1000-10000 commits): 5-15 minutes
- **Large repos** (> 10000 commits): 15-60 minutes

Performance depends on:
- Repository size
- Network speed
- Number of pull requests
- Database write speed

## Support

For issues or questions:
1. Check this README first
2. Verify all prerequisites are met
3. Check `.env` configuration
4. Review error messages in console output

## Version

- Version: 3.5
- Date: 2025-11-18
- Features: Git extraction, PR extraction, Auto-mapping

---

**Happy Extracting! 🚀**
