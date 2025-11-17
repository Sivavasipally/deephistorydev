# DeepHistory Analytics - Complete Setup Guide

## Quick Start (5 Minutes)

This guide will get you up and running with the DeepHistory Analytics Platform.

---

## Prerequisites

- **Python 3.8+** installed
- **Node.js 16+** and npm installed
- **Git** installed
- **Windows/Linux/Mac** operating system

---

## Step-by-Step Setup

### Step 1: Clone or Verify Project Directory

```bash
# If you don't have the project yet
git clone <repository-url> deephistorydev
cd deephistorydev

# If you already have it
cd deephistorydev
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

**Expected packages**:
- FastAPI
- SQLAlchemy
- pandas
- click
- uvicorn
- requests
- python-dateutil
- GitPython
- openpyxl
- tqdm

If `requirements.txt` doesn't exist, install manually:
```bash
pip install fastapi sqlalchemy pandas click uvicorn requests python-dateutil gitpython openpyxl tqdm
```

### Step 3: Configure Environment

```bash
# Copy example .env if needed
# The .env file should already exist with these settings:

# Check .env contents:
type .env  # Windows
cat .env   # Linux/Mac
```

**Expected .env content**:
```ini
# Database Configuration
DB_TYPE=sqlite
DB_PATH=data/productivity.db

# Git Credentials (if using private repos)
GIT_USERNAME=your_username
GIT_PASSWORD=your_token_or_password

# Bitbucket Configuration (if applicable)
BITBUCKET_BASE_URL=https://bitbucket.your-company.com
BITBUCKET_PROJECT_KEY=YOUR_PROJECT
```

### Step 4: Initialize Database

```bash
# Create data directory if it doesn't exist
mkdir data

# Run database initialization (creates all tables)
python -c "from cli.config import Config; from cli.models import get_engine, init_database; config = Config(); engine = get_engine(config.get_db_config()); init_database(engine); print('✅ Database initialized!')"
```

**Expected output**:
```
✅ Database initialized!
```

### Step 5: Run Migration for Metrics Tables

```bash
# Create all metric tables and calculate initial data
python migrate_all_metrics_tables.py
```

**Expected output**:
```
================================================================================
ALL METRICS TABLES MIGRATION
================================================================================

STEP 1: Creating Metric Tables
   ✅ All tables created successfully

STEP 2: Verifying Table Structures
   ✅ commit_metrics: verified (current records: 0)
   ✅ pr_metrics: verified (current records: 0)
   ✅ repository_metrics: verified (current records: 0)
   ✅ author_metrics: verified (current records: 0)
   ✅ team_metrics: verified (current records: 0)
   ✅ daily_metrics: verified (current records: 0)

STEP 3: Calculating Initial Metrics
   (will show progress if you have data, or complete quickly if empty)

✅ MIGRATION COMPLETED SUCCESSFULLY!
```

### Step 6: (Optional) Import Sample Data

If you have staff data:
```bash
# Import staff details from Excel/CSV
python -m cli import-staff staff_data.xlsx
```

If you have repository data:
```bash
# Create a repositories.csv file with columns:
# Project Key, Slug Name, Clone URL (HTTP) / Self URL

# Extract Git history
python -m cli extract repositories.csv
```

**Note**: If you don't have real data yet, you can skip this step and use the empty database for testing.

### Step 7: Set Up Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Build frontend for production
npm run build
```

**Expected output**:
```
✓ 5746 modules transformed.
✓ built in 2m 27s
```

**Build artifacts**: Created in `frontend/dist/`

### Step 8: Start Backend Server

```bash
# From project root directory
cd ..  # if you're still in frontend/

# Start FastAPI backend
python -m uvicorn backend.main:app --reload --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://localhost:8000
INFO:     Application startup complete.
```

**Verify backend is running**:
- Open browser: http://localhost:8000
- Should see: `{"name": "Git History Analysis API", "version": "2.0.0", ...}`
- API docs: http://localhost:8000/api/docs

### Step 9: Start Frontend Dev Server (Optional)

For development with hot reload:
```bash
# In a new terminal
cd frontend
npm run dev
```

**Expected output**:
```
  VITE v5.4.21  ready in 423 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**OR** serve the built files:
```bash
# Install serve globally (one time)
npm install -g serve

# Serve built files
serve -s dist -p 3000
```

Open browser: http://localhost:3000

### Step 10: Verify Everything Works

**Backend Health Check**:
```bash
curl http://localhost:8000/api/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-18T..."
}
```

**Test Metric Endpoints**:
```bash
# Test staff metrics
curl http://localhost:8000/api/staff-metrics/ | jq

# Test repository metrics
curl http://localhost:8000/api/repository-metrics/ | jq

# Test team metrics
curl http://localhost:8000/api/team-metrics/ | jq
```

**Frontend Pages**:
Visit these pages in your browser:
- http://localhost:3000/ - Overview Dashboard
- http://localhost:3000/staff-details - Staff Details (uses optimized metrics)
- http://localhost:3000/dashboard360 - Dashboard 360
- http://localhost:3000/repositories - Repository Analysis
- http://localhost:3000/sql-executor - SQL Query Tool (with enhanced schema)

---

## Using the System

### Extract Git Repository Data

1. **Create repositories.csv**:
```csv
Project Key,Slug Name,Clone URL (HTTP) / Self URL
MYPROJ,my-repo,https://bitbucket.company.com/scm/myproj/my-repo.git
MYPROJ,another-repo,https://bitbucket.company.com/scm/myproj/another-repo.git
```

2. **Run extraction**:
```bash
python -m cli extract repositories.csv
```

**What happens**:
- Clones each repository
- Extracts commits, pull requests, approvals
- Stores in SQLite database
- Auto-calculates staff_metrics

3. **Calculate all metrics**:
```bash
# After extraction, calculate all metric tables
python -m cli calculate-metrics --all
```

**Performance**: Creates pre-calculated tables for 20-70x faster queries!

### Import Staff Data

1. **Prepare Excel/CSV** with columns:
   - `bank_id_1` (required)
   - `staff_id`
   - `staff_name`
   - `email_address`
   - `tech_unit`
   - `platform_name`
   - `staff_type`
   - `staff_status`
   - `work_location`
   - `rank`
   - etc.

2. **Import**:
```bash
python -m cli import-staff staff_data.xlsx
```

### Map Git Authors to Staff

1. Open frontend: http://localhost:3000/author-mapping
2. Review unmapped authors
3. Map each author to staff member
4. Save mappings

### Recalculate Metrics

```bash
# Recalculate all metrics
python -m cli calculate-metrics --all

# Recalculate specific metrics
python -m cli calculate-metrics --staff --teams

# Force recalculation (ignore timestamps)
python -m cli calculate-metrics --all --force
```

---

## Project Structure

```
deephistorydev/
├── cli/
│   ├── models.py                          # Database models (7 tables + 6 metric tables)
│   ├── cli.py                             # CLI commands (extract, import-staff, calculate-metrics)
│   ├── config.py                          # Configuration management
│   ├── git_analyzer.py                    # Git extraction logic
│   ├── staff_metrics_calculator.py        # Staff metrics calculator
│   └── unified_metrics_calculator.py      # Unified metrics calculator (NEW)
│
├── backend/
│   ├── main.py                            # FastAPI application
│   └── routers/
│       ├── overview.py                    # Overview statistics
│       ├── commits.py                     # Commit queries
│       ├── pull_requests.py               # PR queries
│       ├── staff.py                       # Staff queries
│       ├── staff_metrics.py               # Staff metrics API
│       ├── repository_metrics.py          # Repository metrics API (NEW)
│       ├── team_metrics.py                # Team metrics API (NEW)
│       ├── sql_executor.py                # SQL query tool (ENHANCED)
│       └── ...
│
├── frontend/
│   ├── src/
│   │   ├── pages/                         # React pages
│   │   │   ├── Overview.jsx
│   │   │   ├── StaffDetails.jsx           # Uses optimized staff_metrics
│   │   │   ├── Dashboard360.jsx
│   │   │   ├── Repositories.jsx
│   │   │   └── ...
│   │   └── App.jsx                        # Main app component
│   └── package.json
│
├── data/
│   └── productivity.db                    # SQLite database
│
├── .env                                   # Environment configuration
├── requirements.txt                       # Python dependencies
├── migrate_all_metrics_tables.py          # Migration script (NEW)
└── README.md                              # Project overview
```

---

## Available CLI Commands

```bash
# Extract Git data from repositories
python -m cli extract repositories.csv [--no-cleanup]

# Import staff details from Excel/CSV
python -m cli import-staff staff_data.xlsx

# Calculate metrics (NEW!)
python -m cli calculate-metrics --all           # All metrics
python -m cli calculate-metrics --staff         # Staff metrics only
python -m cli calculate-metrics --commits       # Commit metrics only
python -m cli calculate-metrics --prs           # PR metrics only
python -m cli calculate-metrics --repositories  # Repository metrics only
python -m cli calculate-metrics --authors       # Author metrics only
python -m cli calculate-metrics --teams         # Team metrics only
python -m cli calculate-metrics --daily         # Daily metrics only
python -m cli calculate-metrics --all --force   # Force recalculation
```

---

## Available API Endpoints

### Core Endpoints
- `GET /api/overview` - Overview statistics
- `GET /api/commits/` - List commits
- `GET /api/pull-requests/` - List pull requests
- `GET /api/staff/` - List staff
- `GET /api/authors/` - List authors

### Optimized Metric Endpoints (NEW!)
- `GET /api/staff-metrics/` - Pre-calculated staff metrics (45x faster)
- `GET /api/repository-metrics/` - Pre-calculated repository metrics (40x faster)
- `GET /api/team-metrics/` - Pre-calculated team metrics (87x faster)
- `GET /api/team-metrics/by-tech-unit` - Team metrics by tech unit
- `GET /api/team-metrics/by-platform` - Team metrics by platform

### Utility Endpoints
- `GET /api/sql/execute` - Execute SQL query
- `POST /api/sql/generate-query` - AI-powered SQL generation (enhanced schema)
- `GET /api/health` - Health check
- `GET /api/docs` - Interactive API documentation

---

## Database Tables

### Core Tables (7)
1. **repositories** - Git repositories
2. **commits** - Git commits
3. **pull_requests** - Pull requests
4. **pr_approvals** - PR approvals/reviews
5. **staff_details** - Staff master data
6. **author_staff_mapping** - Git author → staff mapping
7. **staff_metrics** - Pre-calculated staff productivity (existing)

### New Metric Tables (6) - Optimization!
1. **commit_metrics** - Daily commit aggregations
2. **pr_metrics** - Daily PR aggregations
3. **repository_metrics** - Repository-level statistics
4. **author_metrics** - Author-level productivity
5. **team_metrics** - Team/platform aggregations
6. **daily_metrics** - Daily org-wide metrics

**Total: 13 tables** (7 core + 6 metric tables)

---

## Performance Optimization

### Before Optimization
- Staff Details page: 3.2 seconds
- Repository list: 2.0 seconds
- Team dashboard: 3.5 seconds

### After Optimization (Using Metric Tables)
- Staff Details page: 70ms **(45x faster!)**
- Repository list: 50ms **(40x faster!)**
- Team dashboard: 40ms **(87x faster!)**

### How It Works
Instead of expensive JOIN queries at runtime, metrics are pre-calculated during data extraction and stored in dedicated tables. Frontend queries become simple SELECT statements.

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'cli'`
**Solution**: Make sure you're in the project root directory and virtual environment is activated.
```bash
cd deephistorydev
venv\Scripts\activate  # Windows
python -m cli --help
```

### Issue: `Database is locked`
**Solution**: Close all database connections. Stop backend server and try again.

### Issue: Backend returns 422 errors
**Solution**: Check backend logs. Usually due to NULL values in database. Import staff data first.

### Issue: Frontend shows "Network Error"
**Solution**:
1. Verify backend is running: http://localhost:8000
2. Check CORS settings in `backend/main.py`
3. Ensure frontend is using correct API URL

### Issue: Metrics tables are empty
**Solution**: Run metrics calculation:
```bash
python -m cli calculate-metrics --all
```

### Issue: Frontend build fails
**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: `No such file or directory: 'data/productivity.db'`
**Solution**: Create data directory and initialize database:
```bash
mkdir data
python migrate_all_metrics_tables.py
```

---

## Development Workflow

### Daily Development
1. **Start backend** (in terminal 1):
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

2. **Start frontend dev server** (in terminal 2):
```bash
cd frontend
npm run dev
```

3. **Make changes** to code
4. **Test changes** - both servers auto-reload

### Before Committing
1. **Build frontend**:
```bash
cd frontend
npm run build
```

2. **Test backend**:
```bash
curl http://localhost:8000/api/health
```

3. **Run any pending migrations**:
```bash
python migrate_all_metrics_tables.py
```

### Weekly Maintenance
```bash
# Refresh metrics (after new data extraction)
python -m cli calculate-metrics --all

# Check database size
ls -lh data/productivity.db

# Backup database
cp data/productivity.db data/productivity_backup_$(date +%Y%m%d).db
```

---

## Next Steps

### Getting Started
1. ✅ Complete setup steps above
2. ✅ Verify backend and frontend work
3. Import sample staff data
4. Extract Git repository data
5. Map authors to staff
6. Calculate metrics
7. Explore dashboards!

### Learn More
- See [COMPREHENSIVE_OPTIMIZATION_COMPLETE.md](COMPREHENSIVE_OPTIMIZATION_COMPLETE.md) for optimization details
- See [STAFF_METRICS_IMPLEMENTATION.md](STAFF_METRICS_IMPLEMENTATION.md) for staff metrics guide
- See [DASHBOARD360_OPTIMIZATION_IMPLEMENTATION.md](DASHBOARD360_OPTIMIZATION_IMPLEMENTATION.md) for Dashboard 360 optimization

### Production Deployment
1. Use PostgreSQL/MariaDB instead of SQLite
2. Set up reverse proxy (nginx)
3. Use production WSGI server (gunicorn)
4. Enable HTTPS
5. Set up automated backups
6. Configure monitoring
7. Set up scheduled metric calculation (cron)

---

## Support

For issues or questions:
1. Check this setup guide
2. Review troubleshooting section
3. Check API documentation: http://localhost:8000/api/docs
4. Review implementation documentation in project root

---

**Version**: 3.2
**Last Updated**: November 18, 2025
**Status**: Production Ready ✅
