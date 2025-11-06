# Git History Deep Analyzer

A comprehensive Python application for analyzing Git repository history, extracting commit and pull request data, staff information, and visualizing insights through an interactive dashboard with advanced analytics and mapping capabilities.

## Features

### 1. Command-Line Tool (cli.py)

#### Git History Extraction (`extract` command)
- Read repository information from CSV files
- Clone repositories with full commit history
- Extract detailed commit information (author, date, lines changed, files modified)
- **Bitbucket REST API v1.0 Integration**: Extract PRs and approvals directly from Bitbucket Server/Data Center
- **GitPython-Based Fallback**: Extract PRs and approvals from Git commit history when API unavailable
- **Multi-Platform Support**: Works with Bitbucket, GitHub, GitLab, and others
- Intelligent pattern matching for PR detection across platforms
- Approval extraction from API or Git commit trailers and messages
- Store data in SQLite or MariaDB database
- Progress bars and status updates
- Automatic cleanup of cloned repositories

#### Staff Details Import (`import-staff` command)
- Import staff information from Excel (.xlsx, .xls) or CSV files
- 71-field comprehensive staff schema
- Automatic column mapping
- Smart date parsing for all date fields
- Update existing records or insert new ones
- Batch processing with progress tracking
- Data validation and error handling

### 2. Streamlit Dashboard (dashboard.py)

#### Overview Page
- Summary statistics of all analyzed repositories
- Quick metrics: commits, authors, repositories, lines changed

#### Authors Analytics Page ⭐ NEW: Date Range Filter
- **Date Range Selection**: Filter all statistics by commit date range
  - Interactive date pickers for start and end dates
  - Automatically detects data range from your commits
  - Shows filtered period info (number of days)
  - Reset button to restore full range
- **Comprehensive author statistics** (filtered by date):
  - Total commits per author
  - Lines added, deleted, and total changed
  - Files modified count
  - Number of repositories contributed to
  - Pull requests created and approved/reviewed
- **Visualizations**:
  - Top 10 contributors by commits (bar chart)
  - Top 10 contributors by lines changed (grouped bar chart)
- **Key insights**: Most active author, most lines changed, top PR reviewer
- **Sortable table** by any metric
- **CSV export** for filtered results
- See [DASHBOARD_FEATURES.md](DASHBOARD_FEATURES.md) for detailed usage

#### Top 10 Commits Page
- Bar chart showing commits with most lines changed
- Detailed table with commit information
- Filterable by repository

#### Top PR Approvers Page
- Horizontal bar chart of most active reviewers
- Number of PRs approved per person
- Number of repositories reviewed

#### Detailed Commits View
- Filter by author, repository, branch, date range
- Sort by date, lines changed, files changed
- Export filtered results to CSV

#### Detailed PRs View
- Filter by author, repository, state, date range
- Sort by date, lines, approvals, commits
- Export filtered results to CSV

#### Author-Staff Mapping Page ⭐ NEW
- **Interactive Mapping Interface**:
  - Multi-select list of distinct commit authors (with commit counts)
  - Multi-select list of staff members by Bank ID
  - Third list showing created mappings
  - Search and filter functionality
- **Three Tabs**:
  1. **Create Mapping**: Interactive author-to-staff assignment
  2. **View Mappings**: See all mappings with metrics and export
  3. **Bulk Operations**: Auto-match by email, CSV import/export
- **Features**:
  - Auto-match authors to staff by email
  - Manual mapping with notes
  - Progress tracking for bulk operations
  - CSV import/export for data portability
  - Mapping coverage percentage
  - Unique mapping table with timestamp tracking
- See [AUTHOR_STAFF_MAPPING_GUIDE.md](AUTHOR_STAFF_MAPPING_GUIDE.md) for detailed guide

#### Table Viewer Page ⭐ NEW
- Browse all database tables with row counts
- Interactive table selection with configurable row limits
- Table statistics (rows, columns, memory usage)
- Column information (data types, null counts)
- Export any table as CSV
- Supports all 6 tables: repositories, commits, pull_requests, pr_approvals, staff_details, author_staff_mapping

#### SQL Executor Page ⭐ NEW
- Execute custom SQL queries against the database
- 6+ pre-built sample query templates
- Complete database schema reference
- Safety warnings for destructive queries
- Query results with statistics
- Export results as CSV
- Advanced analytics capabilities

## Recent Updates

### Version 2.0 - Major Feature Release

**New Features**:
1. ✅ **Bitbucket REST API v1.0 Integration** - Direct API extraction for accurate PR and approval data
2. ✅ **Staff Details Management** - Import and manage HR staff information
3. ✅ **Author-Staff Mapping** - Link Git authors to official staff records
4. ✅ **Date Range Filtering** - Filter author analytics by date range
5. ✅ **Table Viewer** - Browse and export all database tables
6. ✅ **SQL Executor** - Run custom queries with templates
7. ✅ **Command Groups** - Multiple CLI commands (extract, import-staff)

**Improvements**:
- Enhanced PR detection (40-85% increase in detection rate)
- Squash-merge support
- Flexible pattern matching
- Better branch handling
- Automatic email-based mapping
- Bulk operations with progress tracking
- CSV import/export for all data

See [BITBUCKET_API_GUIDE.md](BITBUCKET_API_GUIDE.md) for API integration details.

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

# Bitbucket API Configuration (for REST API v1.0)
# For Bitbucket Server/Data Center, use your server URL
# Example: https://bitbucket.sgp.dbs.com:8443
BITBUCKET_URL=https://bitbucket.sgp.dbs.com:8443
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_APP_PASSWORD=your_bitbucket_app_password

# Clone Directory
CLONE_DIR=./repositories
```

**Notes**:
- Bitbucket API provides accurate PR and approval data (recommended for Bitbucket repos)
- GitPython fallback works for all Git platforms
- **Special characters in passwords** are automatically handled via URL encoding
- See [BITBUCKET_API_GUIDE.md](BITBUCKET_API_GUIDE.md) for API setup
- See [CREDENTIAL_HANDLING.md](CREDENTIAL_HANDLING.md) for password handling

## Usage

### 1. Prepare CSV File

Create a CSV file with the following columns:
```csv
Project Key,Slug Name,Clone URL (HTTP)
PROJECT1,repo-name-1,https://github.com/user/repo1.git
PROJECT2,repo-name-2,https://bitbucket.company.com/scm/proj/repo2.git
```

Example: `repositories.csv`

### 2. Run the CLI Tool

#### Extract Git History

```bash
python cli.py extract repositories.csv
```

Options:
- `--no-cleanup`: Keep cloned repositories after processing (useful for debugging)

Example:
```bash
python cli.py extract repositories.csv --no-cleanup
```

The tool will:
1. Read the CSV file
2. Clone each repository
3. Extract commit history
4. Extract pull requests (via API or GitPython)
5. Extract PR approvals
6. Store data in the database
7. Show progress bars and status updates
8. Clean up cloned repositories (unless --no-cleanup)

#### Import Staff Details

```bash
python cli.py import-staff staff_data.xlsx
# or
python cli.py import-staff staff_data.csv
```

The tool will:
1. Detect file type (Excel or CSV)
2. Map columns to database schema (71 fields)
3. Parse dates automatically
4. Update existing or insert new records
5. Show progress bar
6. Display summary (imported, updated, skipped)

**Supported Fields** (71 total):
- Bank ID, Staff ID, Staff Name, Email
- Employment details (type, status, start/end dates)
- Organizational info (tech unit, platform, department)
- Location and role information
- Many more (see CLI output for full list)

### 3. Launch the Dashboard

Start the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

The dashboard will open at `http://localhost:8501`

### 4. Map Authors to Staff (Optional)

After importing staff details and extracting commits:

1. Navigate to **Author-Staff Mapping** page
2. Use **Bulk Operations** → **Auto-Match by Email** for automatic mapping
3. Manually map remaining authors in **Create Mapping** tab
4. View and export mappings in **View Mappings** tab

This enables cross-analysis between Git contributions and HR staff data.

## Database Schema

### Core Tables

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

### Extended Tables

5. **staff_details** ⭐ NEW
   - id, bank_id_1, staff_id, staff_name, email_address
   - 71 fields including employment details, org info, dates, etc.

6. **author_staff_mapping** ⭐ NEW
   - id, author_name, author_email
   - bank_id_1, staff_id, staff_name
   - mapped_date, notes

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Overview** | Summary statistics and quick metrics |
| **Authors Analytics** | Comprehensive author stats with **date range filter** |
| **Top 10 Commits** | Largest commits by lines changed |
| **Top PR Approvers** | Most active code reviewers |
| **Detailed Commits View** | Filterable, sortable commit history |
| **Detailed PRs View** | Filterable, sortable PR history |
| **Author-Staff Mapping** ⭐ | Map Git authors to staff members |
| **Table Viewer** ⭐ | Browse and export all database tables |
| **SQL Executor** ⭐ | Run custom SQL queries with templates |

## Advanced Features

### Cross-Analysis Queries

With author-staff mapping, you can run powerful queries:

```sql
-- Commits by Department
SELECT sd.tech_unit, COUNT(c.id) as commits
FROM commits c
JOIN author_staff_mapping asm ON c.author_name = asm.author_name
JOIN staff_details sd ON asm.bank_id_1 = sd.bank_id_1
GROUP BY sd.tech_unit;

-- Top Contributors by Platform
SELECT sd.platform_name, asm.author_name, COUNT(c.id) as commits
FROM commits c
JOIN author_staff_mapping asm ON c.author_name = asm.author_name
JOIN staff_details sd ON asm.bank_id_1 = sd.bank_id_1
GROUP BY sd.platform_name, asm.author_name
ORDER BY commits DESC;
```

### Date Range Analytics

Filter author statistics by any date range:
- Quarterly performance reviews
- Monthly team reports
- Project milestone analysis
- Before/after comparisons

### Bulk Operations

- Auto-match 100+ authors by email in seconds
- Import/export mappings via CSV
- Progress tracking for all operations
- Error handling and recovery

## Configuration Options

### Database Selection

**SQLite** (Default):
- Best for: Small to medium projects, single-user scenarios
- Setup: No additional installation required
- Configuration: Set `DB_TYPE=sqlite` and `SQLITE_DB_PATH`

**MariaDB**:
- Best for: Large projects, multi-user scenarios, production use
- Setup: Install MariaDB server
- Configuration: Set `DB_TYPE=mariadb` and connection details

### Git Authentication

For private repositories:
- **Username**: Your Git username
- **Password**: Personal access token (recommended) or password

**GitHub Personal Access Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Use token as password in `.env`

**Bitbucket App Password:**
1. Go to Bitbucket → Personal settings → App passwords
2. Create password with `REPO_READ` and `PROJECT_READ` permissions
3. Use in `.env` as `BITBUCKET_APP_PASSWORD`

## Documentation

- [BITBUCKET_API_GUIDE.md](BITBUCKET_API_GUIDE.md) - Bitbucket API integration guide
- [AUTHOR_STAFF_MAPPING_GUIDE.md](AUTHOR_STAFF_MAPPING_GUIDE.md) - Author-staff mapping guide
- [DASHBOARD_FEATURES.md](DASHBOARD_FEATURES.md) - Dashboard features and date filtering
- [TABLE_VIEWER_SQL_GUIDE.md](TABLE_VIEWER_SQL_GUIDE.md) - Table viewer and SQL executor
- [AUTHORS_ANALYTICS_GUIDE.md](AUTHORS_ANALYTICS_GUIDE.md) - Authors analytics usage
- [GITPYTHON_ANALYSIS_GUIDE.md](GITPYTHON_ANALYSIS_GUIDE.md) - GitPython analysis details
- [CREDENTIAL_HANDLING.md](CREDENTIAL_HANDLING.md) - Password handling
- [PERFORMANCE_TIPS.md](PERFORMANCE_TIPS.md) - Performance optimization

## Troubleshooting

### Clone Errors
- Ensure Git credentials are correct in `.env`
- Check repository URLs and network connectivity
- **Large repositories**: May timeout. Use smaller repos or batches

### Database Issues
- **SQLite**: Check file permissions
- **MariaDB**: Verify server running and credentials correct

### API Issues
- **Bitbucket API**: Verify URL, username, app password in `.env`
- **Authentication**: Use app password, not regular password
- **SSL**: Tool uses `verify=False` for self-signed certificates
- Falls back to GitPython if API fails

### No PR Data
- **Bitbucket**: Use API integration for accurate data
- **Other platforms**: PR data from merge commits (may be limited)
- Check CSV output and logs for detection stats

### Dashboard Not Loading
- Ensure CLI has been run first to populate database
- Check database connection in `.env`
- Verify database file/server accessible

### Import Errors
- **Staff import**: Check Excel/CSV column names match expected format
- **Date errors**: Tool auto-parses dates, but review formats
- Check logs for specific error messages

## Performance

### Repository Size
⚠️ **Important**: Very large repositories (> 10 GB) may take hours or fail.

Recommendations:
- Start with small repositories (< 100 MB)
- Use the provided `sample_repositories.csv` for testing
- See [PERFORMANCE_TIPS.md](PERFORMANCE_TIPS.md) for guidance

### API vs GitPython

| Feature | Bitbucket API | GitPython |
|---------|--------------|-----------|
| **PR Detection** | 100% accurate | 30-90% (pattern-based) |
| **Speed** | Slower (API calls) | Faster (local analysis) |
| **Setup** | Requires credentials | No setup needed |
| **Data Quality** | Complete metadata | Best-effort extraction |

**Recommendation**: Use API for Bitbucket repositories, GitPython for others.

## Example Workflows

### Basic Workflow
```bash
# 1. Setup
cp .env.example .env
# Edit .env with your settings

# 2. Install dependencies
pip install -r requirements.txt

# 3. Extract Git history
python cli.py extract repositories.csv

# 4. Launch dashboard
streamlit run dashboard.py
```

### With Staff Integration
```bash
# 1. Extract Git history
python cli.py extract repositories.csv

# 2. Import staff details
python cli.py import-staff staff_data.xlsx

# 3. Launch dashboard
streamlit run dashboard.py

# 4. Map authors to staff
# - Go to "Author-Staff Mapping" page
# - Use "Auto-Match by Email"
# - Manually map remaining

# 5. Run cross-analysis queries
# - Use "SQL Executor" page
# - Run department/platform analytics
```

### Complete Analysis Pipeline
```bash
# 1. Extract from Bitbucket with API
python cli.py extract bitbucket_repos.csv

# 2. Import staff information
python cli.py import-staff staff_october_2024.xlsx

# 3. Launch dashboard
streamlit run dashboard.py

# 4. Create author-staff mappings
# - Auto-match by email (bulk operation)
# - Manual mapping for edge cases
# - Export mappings as backup

# 5. Analyze with date filters
# - Filter by quarter for performance reviews
# - Export filtered author statistics
# - Run custom SQL queries

# 6. Generate reports
# - Commits by department
# - Platform contribution analysis
# - Team productivity metrics
```

## Advanced Customization

### Custom Queries

```python
from config import Config
from models import get_engine, get_session, Commit, Repository, AuthorStaffMapping, StaffDetails

config = Config()
engine = get_engine(config.get_db_config())
session = get_session(engine)

# Example: Commits by staff level
query = session.query(
    StaffDetails.staff_level,
    func.count(Commit.id).label('commits')
).join(
    AuthorStaffMapping, StaffDetails.bank_id_1 == AuthorStaffMapping.bank_id_1
).join(
    Commit, AuthorStaffMapping.author_name == Commit.author_name
).group_by(
    StaffDetails.staff_level
)

results = query.all()
```

### Extending Dashboard

```python
# Add to dashboard.py
def get_platform_metrics(self):
    """Custom query for platform metrics."""
    session = get_session(self.engine)
    # Your query here
    pass

# Add new page
elif page == "Platform Analytics":
    st.header("Platform Contribution Analysis")
    metrics = dashboard.get_platform_metrics()
    # Your visualizations
```

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for educational and analytical purposes.

## Support

For issues and questions:
- Check the documentation files in the repository
- Review troubleshooting section above
- Submit issues on the project repository

---

**Version**: 2.0
**Last Updated**: 2025
**Python**: 3.8+
**Key Technologies**: SQLAlchemy, Streamlit, Plotly, GitPython, Pandas
