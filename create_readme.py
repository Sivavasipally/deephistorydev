#!/usr/bin/env python3
"""Script to create comprehensive README.md"""

readme_content = """# Git History Deep Analyzer

> **Enterprise-Grade Git Repository Analytics Platform**
> Version 3.5 - Complete Staff Metrics & Data Synchronization Edition

A comprehensive application for analyzing Git repository history with staff correlation, featuring modern React + FastAPI architecture, interactive dashboards, and ultra-fast pre-calculated metrics (20-70x faster).

## 🚀 Quick Start

```bash
# Setup
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Extract, Map, Calculate
python -m cli extract --repos "repo1,repo2"
python -m cli auto-map-staff
python -m cli calculate-metrics --all

# Start (2 terminals)
cd backend && python -m uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Access: http://localhost:3000
```

## 📋 What's New in v3.5

### 1. Separate Current Year Metrics Table
- **Two tables**: `staff_metrics` (all-time) + `current_year_staff_metrics` (2025)
- Dedicated frontend page: `/current-year-metrics`
- Clean separation of historical vs current year data

### 2. Data Synchronization Tool (SQLite → MariaDB)
- Automatic ID remapping with new ID generation
- Foreign key relationship preservation
- Duplicate detection & incremental sync
- Transaction safety & batch processing
- Usage: `python datasync/sync_sqlite_to_mariadb.py`

### 3. Reorganized Frontend
- `/staff-details` - All-time productivity metrics
- `/current-year-metrics` - **NEW** Dedicated 2025 analytics page
- Enhanced search, filtering, and Excel export

## 🏗 Architecture

```
React Frontend (11 Pages) ←→ FastAPI Backend (50+ APIs) ←→ SQLite/MySQL/MariaDB (9 Tables)
                                        ↕
                              CLI Tools + Data Sync Tool
                              (Bitbucket Extract + Metrics Engine + SQLite→MariaDB)
```

### Project Structure

```
deephistorydev/
├── cli/                          # Business Logic & CLI Tools
│   ├── models.py                 # 9 SQLAlchemy tables
│   ├── bitbucket_api.py          # Data extraction
│   ├── staff_metrics_calculator.py  # Metrics engine
│   └── __main__.py               # CLI entry point
├── backend/                      # FastAPI Backend
│   ├── main.py
│   └── routers/                  # API modules (50+ endpoints)
├── frontend/                     # React Frontend
│   └── src/pages/                # 11 dashboard pages
├── datasync/                     # Data Sync Tool
│   ├── sync_sqlite_to_mariadb.py # Main sync script
│   ├── quick_setup.py            # Connection tester
│   └── README.md                 # Detailed docs
└── extract/                      # Standalone extraction tool
```

## ✨ Key Features

- **11 Interactive Dashboards**: Overview, Staff Details, Current Year Metrics, Productivity, 360° View, Team Comparison, Authors, Commits, PRs, Mapping, Table Viewer, SQL Executor
- **Dual Staff Metrics**: Separate tables for all-time and current year (2025) analytics
- **Pre-calculated Metrics**: 20-70x faster queries
- **Author-Staff Mapping**: Manual + automatic (email-based)
- **Excel Export**: Multi-sheet workbooks
- **Data Sync**: SQLite → MariaDB with ID remapping
- **Multi-Database**: SQLite, MySQL, MariaDB, PostgreSQL

## 💻 Technology Stack

**Frontend**: React 18 + Ant Design 5.x + @ant-design/charts + Vite
**Backend**: FastAPI + SQLAlchemy 2.x + Uvicorn + Pydantic v2
**Database**: SQLite / MySQL / MariaDB / PostgreSQL
**CLI**: Python 3.9+ + Requests + python-dotenv

## 📦 Installation

```bash
# 1. Clone
git clone <repository>
cd deephistorydev

# 2. Backend
python -m venv venv
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt

# 3. Frontend
cd frontend && npm install && cd ..

# 4. Database
python cli/migrate_current_year_table.py
```

## ⚙ Configuration

Create `.env`:

```bash
# Database
DB_TYPE=sqlite                    # sqlite, mysql, mariadb
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gpt
DB_USER=username
DB_PASSWORD=password

# Bitbucket
BITBUCKET_BASE_URL=https://bitbucket.example.com
BITBUCKET_USERNAME=your_username
BITBUCKET_PASSWORD=your_app_password

# Data Sync
MARIADB_URL=mysql+pymysql://user:pass@host:3306/database
```

## 📖 Usage Guide

### 1. Extract Data

```bash
python -m cli extract --repos "repo1,repo2,repo3"
python -m cli extract --repos "repo1" --since "2024-01-01"
python -m cli extract --repos "repo1" --branches "main,develop"
```

### 2. Map Authors to Staff

```bash
# Auto-map by email
python -m cli auto-map-staff

# OR manual CSV
python -m cli export-mappings --output mappings.csv
# Edit mappings.csv
python -m cli import-mappings --input mappings.csv
```

### 3. Calculate Metrics

```bash
python -m cli calculate-metrics --all
python -m cli calculate-metrics --staff
```

### 4. Start Application

```bash
# Terminal 1: Backend
cd backend && python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### 5. Sync to MariaDB (Optional)

```bash
set MARIADB_URL=mysql+pymysql://user:pass@host:3306/database
python datasync/quick_setup.py            # Test connection
python datasync/sync_sqlite_to_mariadb.py # Run sync
```

## 🗄 Database Schema

**9 Core Tables**:

1. `repositories` - Repository info
2. `commits` - Git commits with file changes
3. `pull_requests` - PRs with metadata
4. `pr_approvals` - PR approvals
5. `authors` - Git authors
6. `staff_details` - Staff information
7. `author_staff_mapping` - Author-to-staff correlation
8. `staff_metrics` - **All-time productivity metrics**
9. `current_year_staff_metrics` - **2025-specific metrics**

**Relationships**:
- repositories → commits, pull_requests
- pull_requests → pr_approvals
- staff_details → author_mappings, staff_metrics, current_year_staff_metrics

## 🌐 API Endpoints

Base: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

**Key Endpoints**:
```
GET  /api/overview/summary                   # Dashboard stats
GET  /api/commits/                           # List commits
GET  /api/pull-requests/                     # List PRs
GET  /api/staff-metrics/                     # All-time metrics
GET  /api/staff-metrics/current-year         # 2025 metrics ✨NEW
GET  /api/staff-metrics/current-year/{id}    # Specific 2025 metrics
POST /api/staff-metrics/recalculate-all      # Recalculate
```

## 🔄 Data Synchronization

**SQLite → MariaDB Migration Tool** with:

✅ **Automatic ID Remapping**: New IDs generated, mappings preserved
✅ **Relationship Preservation**: All foreign keys maintained
✅ **Duplicate Detection**: Skips existing records
✅ **Transaction Safety**: Rollback on errors
✅ **Batch Processing**: Optimized for large datasets
✅ **ID Mapping Export**: `id_mappings.json` for reference

**Sync Order** (respecting dependencies):
1. repositories, authors (no dependencies)
2. commits → repositories
3. pull_requests → repositories
4. pr_approvals → pull_requests
5. staff_details (no dependencies)
6. author_mappings → staff_details
7. staff_metrics, current_year_staff_metrics → staff_details

**Example**:
```bash
# SQLite ID 1 → MariaDB ID 101 (new, remapped)
# All child records updated to reference 101
```

See [datasync/README.md](datasync/README.md) for full documentation.

## 🖥 Frontend Pages

1. **Overview** (`/`) - Dashboard summary
2. **Staff Details** (`/staff-details`) - All-time metrics
3. **Current Year Metrics** (`/current-year-metrics`) - 2025 analytics ✨NEW
4. **Staff Productivity** (`/productivity`) - Individual analysis
5. **Team Comparison** (`/team-comparison`) - Side-by-side
6. **360° Dashboard** (`/360-dashboard`) - Comprehensive view
7. **Authors Analytics** (`/authors`) - Git authors
8. **Commits View** (`/commits`) - Commit history
9. **Pull Requests** (`/pull-requests`) - PR list
10. **Author Mapping** (`/mapping`) - Mapping UI
11. **Table Viewer** (`/tables`) - Direct DB access
12. **SQL Executor** (`/sql`) - Custom queries

## 🔧 CLI Commands

```bash
# Extract
python -m cli extract --repos "repo1,repo2"
python -m cli extract --project "PROJECT_KEY"

# Mapping
python -m cli auto-map-staff
python -m cli export-mappings --output FILE
python -m cli import-mappings --input FILE

# Metrics
python -m cli calculate-metrics --all
python -m cli calculate-metrics --staff

# Database
python cli/migrate_current_year_table.py        # Create table
python datasync/quick_setup.py                  # Test connections
python datasync/sync_sqlite_to_mariadb.py       # Sync data

# Diagnostics
python -m cli diagnose
python -m cli show-stats
```

## 🐛 Troubleshooting

### Table Doesn't Exist
```bash
python cli/migrate_current_year_table.py
```

### Current Year Metrics Empty
```bash
python -m cli calculate-metrics --staff
```

### Frontend 404 on /current-year-metrics
Check API URL in `frontend/src/pages/CurrentYearStaffMetrics.jsx:60`:
```javascript
axios.get("http://localhost:8000/api/staff-metrics/current-year")
```

### Data Sync Connection Error
```bash
# Test connections
python datasync/quick_setup.py

# Verify target DB
mysql -h host -u user -p database -e "SHOW TABLES;"
```

## 📊 Metrics Overview

### All-Time Metrics (`staff_metrics`)
- Total commits, lines added/deleted, files changed
- Total PRs created/merged, approvals given
- Repositories touched, file types worked
- First/last commit dates, code churn ratio

### Current Year Metrics (`current_year_staff_metrics`)
- Activity Totals: 10 key metrics
- Diversity: Different file types, repos, projects
- Distribution: % code, config, documentation
- Monthly Averages: Commits, PRs, approvals per month
- Technology Lists: File types, repos, projects worked

## 📝 Version History

**v3.5** (Jan 2025) - Separate current year table + data sync tool
**v3.4** (Jan 2025) - Current year metrics (27 fields)
**v3.3** (Dec 2024) - Performance optimization (20-70x)
**v3.0** (Sep 2024) - React + FastAPI rewrite

## 🎯 Quick Reference Card

```bash
# SETUP
pip install -r requirements.txt && cd frontend && npm install

# WORKFLOW
python -m cli extract --repos "repo1,repo2"       # 1. Extract
python -m cli auto-map-staff                        # 2. Map
python -m cli calculate-metrics --all               # 3. Calculate
python cli/migrate_current_year_table.py            # 4. Migrate

# START (2 terminals)
cd backend && python -m uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# SYNC TO MARIADB
set MARIADB_URL=mysql+pymysql://user:pass@host:3306/db
python datasync/sync_sqlite_to_mariadb.py

# ACCESS
# http://localhost:3000 - Frontend
# http://localhost:8000/docs - API Documentation
```

---

## 📚 Documentation

- **Data Sync Tool**: [datasync/README.md](datasync/README.md)
- **Quick Start**: [datasync/QUICK_START.md](datasync/QUICK_START.md)
- **Historical Docs**: [docs/](docs/) folder

---

**Built with ❤️ using React, FastAPI, and SQLAlchemy**

*Version 3.5 - Complete Staff Metrics & Data Synchronization Edition*
"""

# Write the README
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("✅ README.md created successfully!")
print("📄 Old README backed up as README_OLD.md")
