# Git History Deep Analyzer

A comprehensive Python application for analyzing Git repository history, extracting commit and pull request data, and visualizing insights through an interactive dashboard.

## Features

### 1. Command-Line Tool (cli.py)
- Read repository information from CSV files
- Clone repositories with full commit history
- Extract detailed commit information (author, date, lines changed, files modified)
- Extract pull request data from merge commits
- Store data in SQLite or MariaDB database
- Progress bars and status updates
- Automatic cleanup of cloned repositories

### 2. Streamlit Dashboard (dashboard.py)
- **Overview**: Summary statistics of all analyzed repositories
- **Authors Analytics**: Comprehensive author statistics (commits, lines changed, PRs, approvals) with visualizations
- **Top 10 Commits**: Commits with the most lines changed, with visualizations
- **Top PR Approvers**: Most active PR reviewers
- **Detailed Commits View**: Searchable, filterable, and sortable commit history
- **Detailed PRs View**: Searchable, filterable, and sortable pull request history
- Export data to CSV

## Installation

### Prerequisites
- Python 3.8 or higher
- Git installed on your system
- MariaDB (optional, if not using SQLite)

### Setup

1. Clone this repository or extract the files

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment configuration:
```bash
cp .env.example .env
```

4. Edit `.env` file with your configuration:
```ini
# Database Configuration
DB_TYPE=sqlite  # or mariadb

# SQLite Configuration (if using SQLite)
SQLITE_DB_PATH=git_history.db

# MariaDB Configuration (if using MariaDB)
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=git_history

# Git Credentials
GIT_USERNAME=your_git_username
GIT_PASSWORD=your_git_password_or_token

# Clone Directory
CLONE_DIR=./repositories
```

## Usage

### 1. Prepare CSV File

Create a CSV file with the following columns:
```
Project Key,Slug Name,Clone URL (HTTP)
PROJECT1,repo-name-1,https://github.com/user/repo1.git
PROJECT2,repo-name-2,https://github.com/user/repo2.git
```

Example: `repositories.csv`

### 2. Run the CLI Tool

Extract Git history from repositories:

```bash
python cli.py repositories.csv
```

Options:
- `--no-cleanup`: Keep cloned repositories after processing (useful for debugging)

Example:
```bash
python cli.py repositories.csv --no-cleanup
```

The tool will:
1. Read the CSV file
2. Clone each repository
3. Extract commit history
4. Extract pull request information
5. Store data in the database
6. Show progress bars and status updates
7. Clean up cloned repositories (unless --no-cleanup is specified)

### 3. Launch the Dashboard

Start the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

The dashboard will open in your default web browser at `http://localhost:8501`

### Dashboard Features

#### Overview Page
- Total commits across all repositories
- Number of unique authors
- Total repositories analyzed
- Total lines of code changed

#### Authors Analytics Page
- **Comprehensive author statistics** including:
  - Total commits per author
  - Lines added, deleted, and total changed
  - Files modified count
  - Number of repositories contributed to
  - Pull requests created
  - Pull requests approved/reviewed
- **Visualizations**:
  - Top 10 contributors by commits (bar chart)
  - Top 10 contributors by lines changed (grouped bar chart)
- **Key insights**: Most active author, most lines changed, top PR reviewer
- **Sortable table** by any metric
- **CSV export** for further analysis
- See [AUTHORS_ANALYTICS_GUIDE.md](AUTHORS_ANALYTICS_GUIDE.md) for detailed usage

#### Top 10 Commits Page
- Bar chart showing commits with most lines changed
- Detailed table with commit information
- Filterable by repository

#### Top PR Approvers Page
- Horizontal bar chart of most active reviewers
- Number of PRs approved per person
- Number of repositories they've reviewed

#### Detailed Commits View
- Filter by:
  - Author
  - Repository
  - Branch
  - Date range
- Sort by:
  - Date
  - Total lines changed
  - Lines added
  - Lines deleted
  - Files changed
- Export filtered results to CSV

#### Detailed PRs View
- Filter by:
  - Author
  - Repository
  - State (open/closed/merged)
  - Date range
- Sort by:
  - Created date
  - Total lines changed
  - Number of approvals
  - Number of commits
- Export filtered results to CSV

## Database Schema

### Tables

1. **repositories**
   - id, project_key, slug_name, clone_url, created_at

2. **commits**
   - id, repository_id, commit_hash, author_name, author_email
   - committer_name, committer_email, commit_date, message
   - lines_added, lines_deleted, files_changed, branch

3. **pull_requests**
   - id, repository_id, pr_number, title, description
   - author_name, author_email, created_date, merged_date
   - state, source_branch, target_branch
   - lines_added, lines_deleted, commits_count

4. **pr_approvals**
   - id, pull_request_id, approver_name, approver_email, approval_date

## Configuration Options

### Database Selection

**SQLite** (Default):
- Best for: Small to medium projects, single-user scenarios
- Setup: No additional installation required
- Configuration: Set `DB_TYPE=sqlite` and `SQLITE_DB_PATH`

**MariaDB**:
- Best for: Large projects, multi-user scenarios, production use
- Setup: Install MariaDB server
- Configuration: Set `DB_TYPE=mariadb` and MariaDB connection details

### Git Authentication

For private repositories, provide authentication:
- **Username**: Your Git username
- **Password**: Personal access token (recommended) or password

**GitHub Personal Access Token:**
1. Go to GitHub Settings � Developer settings � Personal access tokens
2. Generate new token with `repo` scope
3. Use token as password in `.env` file

## Performance and Repository Size

⚠️ **Important**: Very large repositories (> 10 GB, e.g., Linux kernel) may take hours to clone and process, or may fail entirely.

For best results:
- Start with small repositories (< 100 MB)
- Use the provided `sample_repositories.csv` for testing
- See [PERFORMANCE_TIPS.md](PERFORMANCE_TIPS.md) for detailed guidance

## Troubleshooting

### Clone Errors
- Ensure Git credentials are correct in `.env`
- Check if repositories use 'master' or 'main' branch (tool handles both)
- Verify network connectivity and repository URLs
- **Large repositories**: May timeout or fail. Use smaller repos or split into batches

### Database Connection Issues
- **SQLite**: Check file permissions for database file
- **MariaDB**: Verify server is running and credentials are correct

### No PR Data
- PR data is extracted from merge commits
- If repository doesn't use merge commits, PR data will be limited
- For full PR data, consider integrating with Git platform APIs (GitHub, GitLab, Bitbucket)

### Dashboard Not Loading Data
- Ensure CLI tool has been run first to populate database
- Check database connection in `.env` file
- Verify database file/server is accessible

## Limitations and Notes

1. **Pull Request Data**: The CLI tool extracts PR information from merge commits. For comprehensive PR data including reviews, approvals, and detailed metadata, you would need to integrate with the Git platform's API (GitHub API, GitLab API, Bitbucket API).

2. **Approval Data**: PR approvals are extracted from commit messages (e.g., "Reviewed-by:" tags). For accurate approval data, API integration is recommended.

3. **Branch Analysis**: By default, the tool analyzes the master/main branch. For comprehensive branch analysis, modifications to the code would be needed.

4. **Large Repositories**: Very large repositories may take significant time to clone and process. Consider using `--no-cleanup` option for debugging.

## Example Workflow

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your settings

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create CSV file with repositories
cat > repositories.csv << EOF
Project Key,Slug Name,Clone URL (HTTP)
MyProject,my-repo,https://github.com/user/my-repo.git
EOF

# 4. Extract Git history
python cli.py repositories.csv

# 5. Launch dashboard
streamlit run dashboard.py
```

## Advanced Usage

### Custom Database Queries

You can write custom queries using the SQLAlchemy models:

```python
from config import Config
from models import get_engine, get_session, Commit, Repository

config = Config()
engine = get_engine(config.get_db_config())
session = get_session(engine)

# Example: Get commits from specific author
commits = session.query(Commit).filter(
    Commit.author_email == 'developer@example.com'
).all()
```

### Extending the Dashboard

The dashboard is built with Streamlit and Plotly, making it easy to add custom visualizations:

```python
# Add to dashboard.py
def get_commit_trends(self):
    # Your custom query
    pass

# Add new page in main()
elif page == "Commit Trends":
    st.header("Commit Trends Over Time")
    # Your visualization code
```

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for educational and analytical purposes.
