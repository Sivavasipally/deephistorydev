# Quick Start Guide

## Setup (5 minutes)

### 1. Initial Setup
```bash
# Run setup script
python setup.py

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` file:
```ini
DB_TYPE=sqlite
SQLITE_DB_PATH=git_history.db
GIT_USERNAME=your_username
GIT_PASSWORD=your_token
CLONE_DIR=./repositories
```

## Usage

### Extract Git History

**Option 1: Use sample CSV**
```bash
python cli.py sample_repositories.csv
```

**Option 2: Create your own CSV**

Create `my_repos.csv`:
```csv
Project Key,Slug Name,Clone URL (HTTP)
MyProject,my-app,https://github.com/user/my-app.git
MyProject,my-api,https://github.com/user/my-api.git
```

Run extraction:
```bash
python cli.py my_repos.csv
```

### View Dashboard

```bash
streamlit run dashboard.py
```

Open browser to: http://localhost:8501

## Dashboard Navigation

1. **Overview** - Summary statistics
2. **Top 10 Commits** - Biggest commits by lines changed
3. **Top PR Approvers** - Most active reviewers
4. **Detailed Commits View** - Full commit history with filters
5. **Detailed PRs View** - Full PR history with filters

## Common Commands

```bash
# Extract with cleanup
python cli.py repos.csv

# Extract and keep cloned repos (for debugging)
python cli.py repos.csv --no-cleanup

# Run dashboard
streamlit run dashboard.py

# Run dashboard on specific port
streamlit run dashboard.py --server.port 8080
```

## CSV Format

Your CSV must have these columns (in any order):
- `Project Key` - Project identifier
- `Slug Name` - Repository name
- `Clone URL (HTTP)` or `Self URL` - Git clone URL

Example:
```csv
Project Key,Slug Name,Clone URL (HTTP)
PROJ,repo-name,https://github.com/user/repo.git
```

## Troubleshooting

### "Git clone failed"
- Check Git credentials in `.env`
- Verify repository URL is correct
- Ensure you have access to the repository

### "No module named 'git'"
```bash
pip install gitpython
```

### "Database connection error"
- Check `DB_TYPE` in `.env`
- For SQLite: Ensure you have write permissions
- For MariaDB: Verify server is running

### "No data in dashboard"
- Run CLI tool first: `python cli.py your_repos.csv`
- Check database file exists
- Verify `.env` database configuration

## Tips

1. **For private repos**: Use personal access token as password
2. **Large repos**: Process in batches to manage disk space
3. **Database choice**: Use SQLite for quick start, MariaDB for production
4. **Performance**: First run takes time (cloning), subsequent runs are faster for same repos

## Getting Help

See [README.md](README.md) for detailed documentation.
