# Project Structure

## Overview
This project consists of two main applications for Git repository analysis:
1. **CLI Tool** - Command-line tool for extracting Git history
2. **Dashboard** - Streamlit web dashboard for visualization

## File Structure

```
deephistorydev/
│
├── cli.py                      # Command-line interface application
├── dashboard.py                # Streamlit dashboard application
├── models.py                   # Database models (SQLAlchemy)
├── config.py                   # Configuration management
├── git_analyzer.py             # Git operations and data extraction
├── setup.py                    # Setup/initialization script
│
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
├── .gitignore                  # Git ignore patterns
│
├── README.md                   # Full documentation
├── QUICKSTART.md               # Quick start guide
├── PROJECT_STRUCTURE.md        # This file
│
├── sample_repositories.csv     # Sample CSV file for testing
│
└── repositories/               # Directory for cloned repos (auto-created)
```

## Core Components

### 1. CLI Tool (cli.py)
**Purpose**: Extract Git history from repositories listed in CSV file

**Key Classes**:
- `GitHistoryCLI` - Main CLI controller

**Features**:
- CSV parsing with flexible column name detection
- Progress bars for each processing step
- Repository cloning with authentication
- Commit and PR data extraction
- Database storage
- Automatic cleanup

**Usage**:
```bash
python cli.py repositories.csv
```

### 2. Dashboard (dashboard.py)
**Purpose**: Visualize and analyze extracted Git history data

**Key Classes**:
- `GitHistoryDashboard` - Dashboard controller and data queries

**Pages**:
1. **Overview** - Summary statistics
2. **Top 10 Commits** - Biggest commits by lines changed
3. **Top PR Approvers** - Most active reviewers
4. **Detailed Commits View** - Searchable commit history
5. **Detailed PRs View** - Searchable PR history

**Usage**:
```bash
streamlit run dashboard.py
```

### 3. Database Models (models.py)
**Purpose**: Define database schema and ORM mappings

**Models**:
- `Repository` - Repository information
- `Commit` - Commit details
- `PullRequest` - Pull request information
- `PRApproval` - PR approval/review data

**Functions**:
- `get_engine()` - Create database engine
- `init_database()` - Initialize schema
- `get_session()` - Get database session

### 4. Configuration (config.py)
**Purpose**: Manage application configuration from environment variables

**Class**:
- `Config` - Configuration manager

**Methods**:
- `get_db_config()` - Get database configuration
- `get_clone_dir()` - Get clone directory path
- `get_git_credentials()` - Get Git credentials

### 5. Git Analyzer (git_analyzer.py)
**Purpose**: Git operations and data extraction logic

**Class**:
- `GitAnalyzer` - Git repository analyzer

**Methods**:
- `clone_repository()` - Clone a Git repository
- `extract_commits()` - Extract commit history
- `extract_pull_requests()` - Extract PR data from merge commits
- `extract_pr_approvals()` - Extract approval data
- `get_commit_stats()` - Calculate commit statistics
- `cleanup_repository()` - Remove cloned repository

### 6. Setup Script (setup.py)
**Purpose**: Initialize the application environment

**Functions**:
- `setup()` - Create necessary directories and files

**Usage**:
```bash
python setup.py
```

## Data Flow

```
┌──────────────┐
│  CSV File    │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  CLI Tool (cli.py)   │
│  ┌───────────────┐   │
│  │ Git Analyzer  │   │
│  └───────────────┘   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Database            │
│  ┌─────────────┐     │
│  │ repositories│     │
│  │ commits     │     │
│  │ pull_requests│    │
│  │ pr_approvals│     │
│  └─────────────┘     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Dashboard           │
│  (dashboard.py)      │
│  ┌───────────────┐   │
│  │ Visualizations│   │
│  │ Filters       │   │
│  │ Analytics     │   │
│  └───────────────┘   │
└──────────────────────┘
```

## Database Schema

```sql
repositories
├── id (PK)
├── project_key
├── slug_name
├── clone_url
└── created_at

commits
├── id (PK)
├── repository_id (FK)
├── commit_hash (UNIQUE)
├── author_name
├── author_email
├── committer_name
├── committer_email
├── commit_date
├── message
├── lines_added
├── lines_deleted
├── files_changed
└── branch

pull_requests
├── id (PK)
├── repository_id (FK)
├── pr_number
├── title
├── description
├── author_name
├── author_email
├── created_date
├── merged_date
├── state
├── source_branch
├── target_branch
├── lines_added
├── lines_deleted
└── commits_count

pr_approvals
├── id (PK)
├── pull_request_id (FK)
├── approver_name
├── approver_email
└── approval_date
```

## Dependencies

### Core Libraries
- **GitPython** - Git operations
- **SQLAlchemy** - Database ORM
- **Pandas** - Data manipulation
- **Streamlit** - Web dashboard
- **Plotly** - Interactive visualizations
- **Click** - CLI framework
- **tqdm** - Progress bars
- **python-dotenv** - Environment variables

### Database Drivers
- **PyMySQL** - MariaDB/MySQL connector (optional)
- SQLite (built-in with Python)

## Configuration

### Environment Variables (.env)
```ini
# Database
DB_TYPE=sqlite              # or mariadb
SQLITE_DB_PATH=git_history.db

# MariaDB (if DB_TYPE=mariadb)
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=password
MARIADB_DATABASE=git_history

# Git Authentication
GIT_USERNAME=username
GIT_PASSWORD=token

# Directories
CLONE_DIR=./repositories
```

## Extension Points

### Adding New Analyses
1. Add query method to `GitHistoryDashboard` class in `dashboard.py`
2. Create new page in `main()` function
3. Add visualization using Plotly or Streamlit components

### Adding New Data Sources
1. Extend `GitAnalyzer` class in `git_analyzer.py`
2. Add new models to `models.py` if needed
3. Update CLI processing in `cli.py`

### Custom Database Queries
```python
from config import Config
from models import get_engine, get_session, Commit

config = Config()
engine = get_engine(config.get_db_config())
session = get_session(engine)

# Your custom query
results = session.query(Commit).filter(...).all()
```

## Performance Considerations

1. **Large Repositories**:
   - Cloning takes time proportional to repository size
   - Consider batch processing
   - Use `--no-cleanup` for debugging only

2. **Database Choice**:
   - SQLite: Fast for < 1M commits
   - MariaDB: Better for > 1M commits or concurrent access

3. **Memory Usage**:
   - Commits are processed in batches
   - Large commit histories may require significant RAM

## Security Notes

1. **Credentials**: Never commit `.env` file
2. **Personal Access Tokens**: Use tokens instead of passwords
3. **Token Permissions**: Grant minimal required scopes
4. **Database**: Use strong passwords for MariaDB
5. **Network**: Use HTTPS for Git operations

## Troubleshooting

See [README.md](README.md#troubleshooting) for detailed troubleshooting guide.

## Future Enhancements

Potential improvements:
- Git platform API integration (GitHub, GitLab, Bitbucket)
- Multi-branch analysis
- Code complexity metrics
- Team collaboration analytics
- Real-time updates
- Export to various formats (PDF, Excel)
- Automated report generation
- Email notifications
