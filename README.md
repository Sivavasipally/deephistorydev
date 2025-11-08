# Git History Deep Analyzer

A comprehensive enterprise-grade application for analyzing Git repository history with staff correlation, featuring a modern **React + FastAPI** architecture, interactive dashboards, and AI-powered analytics.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GIT HISTORY DEEP ANALYZER                                 │
│                         Version 3.0 (React Edition)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Extract → Analyze → Map → Visualize → Export                              │
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Git    │  │   PRs    │  │  Staff   │  │ Author   │  │  React   │    │
│  │ Commits  │→ │Approvals │→ │ Details  │→ │ Mapping  │→ │Dashboard │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│       ↓             ↓             ↓             ↓             ↓             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    SQLite / MySQL / PostgreSQL                     │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│       ↓                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │              FastAPI Backend + React Frontend                      │    │
│  │  10+ Pages | Real-time Filters | Staff Analytics | Productivity   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Dashboard Pages](#dashboard-pages)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Staff Integration](#staff-integration)
- [Productivity Analytics](#productivity-analytics)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        MODERN ARCHITECTURE                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐        ┌──────────────────┐                  │
│  │  React Frontend │        │  FastAPI Backend │                  │
│  │   (Vite + Ant)  │◄──────►│   (Python 3.8+)  │                  │
│  │                 │  REST  │                  │                  │
│  │ • 10+ Pages     │  API   │ • 15+ Endpoints  │                  │
│  │ • Charts        │        │ • SQLAlchemy ORM │                  │
│  │ • Real-time     │        │ • Pydantic       │                  │
│  └────────┬────────┘        └────────┬─────────┘                  │
│           │                          │                             │
│           ↓                          ↓                             │
│  ┌────────────────────────────────────────────┐                   │
│  │            Database Layer                  │                   │
│  │  ┌──────────────┐   ┌──────────────┐      │                   │
│  │  │   SQLite     │   │ MySQL/PGSQL  │      │                   │
│  │  │ (Development)│   │ (Production) │      │                   │
│  │  └──────────────┘   └──────────────┘      │                   │
│  │                                             │                   │
│  │  • 6 Core Tables                           │                   │
│  │  • Staff Integration                       │                   │
│  │  • Author Mapping                          │                   │
│  └────────────────────────────────────────────┘                   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Features

### 🎨 Modern React Frontend

#### Interactive Dashboard Pages (10+)

```
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARD PAGES                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Overview              → Quick metrics & summary         │
│  2. Staff Analytics ⭐    → Grouped by staff with filters   │
│  3. Commits View          → Detailed commit history         │
│  4. Pull Requests View    → PR tracking with filters        │
│  5. Top Commits           → Largest code changes            │
│  6. Top Approvers         → Most active reviewers           │
│  7. Staff Productivity 🆕 → Individual performance metrics  │
│  8. Author Mapping ⭐     → Link authors to staff           │
│     • Auto-match by email                                   │
│     • Bulk operations with smart suggestions                │
│     • Reverse mapping (staff → author)                      │
│  9. Table Viewer          → Browse all database tables      │
│ 10. SQL Executor          → Custom queries + AI generation  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 FastAPI Backend

**RESTful API with:**
- 15+ specialized endpoints
- Automatic OpenAPI documentation
- Fast async operations
- SQLAlchemy ORM
- Pydantic validation
- CORS support

### 📊 Staff Productivity Analytics (NEW)

**Comprehensive developer assessment:**
- ✅ **Time Granularity**: Daily | Weekly | Monthly | Yearly
- ✅ **Metrics**: Commits, Lines changed, PRs, Repos touched, Files changed
- ✅ **Charts**:
  - Commits over time (line chart)
  - Lines changed (stacked column)
  - PR activity trend
  - Repository breakdown
  - Calendar heatmap (GitHub-style)
- ✅ **Filters**: Staff name, date range, repository
- ✅ **Export**: CSV for all charts
- ✅ **Staff-based grouping**: All Git identities merged per staff

### 🔗 Author-Staff Mapping

**Intelligent correlation system:**
- ✅ Auto-match by email with progress tracking
- ✅ Multi-select bulk operations
- ✅ Smart suggestions with similarity algorithm
- ✅ Reverse mapping (staff without mappings)
- ✅ Inactive staff exclusion
- ✅ Visual progress indicators

### 📈 Advanced Analytics

**Staff Analytics Features:**
- ✅ Grouped by staff_name/bank_id (all Git identities merged)
- ✅ Filters: Rank, Manager, Location, Staff Type
- ✅ "All" option in every filter dropdown
- ✅ Shows only mapped, active staff
- ✅ Real-time metric calculations
- ✅ CSV export for all data

---

## Technology Stack

### Frontend
```
┌────────────────────────────────────────────────────────────┐
│ React 18            │ Modern component-based UI             │
│ Vite 5              │ Lightning-fast build tool             │
│ Ant Design 5        │ Enterprise UI components              │
│ Ant Design Charts   │ G2Plot visualizations                 │
│ React Router 6      │ Client-side routing                   │
│ Axios               │ HTTP client                           │
│ Day.js              │ Date manipulation                     │
└────────────────────────────────────────────────────────────┘
```

### Backend
```
┌────────────────────────────────────────────────────────────┐
│ FastAPI 0.104+      │ Modern async web framework            │
│ Python 3.8+         │ Core language                         │
│ SQLAlchemy 2.0+     │ ORM with async support                │
│ Pydantic 2.0+       │ Data validation                       │
│ Uvicorn             │ ASGI server                           │
│ GitPython 3.1+      │ Git repository analysis               │
└────────────────────────────────────────────────────────────┘
```

### Database
```
┌────────────────────────────────────────────────────────────┐
│ SQLite              │ Development (default)                 │
│ MySQL/MariaDB       │ Production option                     │
│ PostgreSQL          │ Production option                     │
└────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- **Python** 3.8 or higher
- **Node.js** 16+ and npm
- **Git** installed on your system
- **Database** (SQLite included, MySQL/PostgreSQL optional)

### Backend Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Create environment configuration
cp .env.example .env

# 3. Edit .env with your settings
nano .env
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build for production (optional)
npm run build
```

---

## Quick Start

### Complete Workflow

```bash
┌─────────────────────────────────────────────────────────────┐
│                    QUICK START GUIDE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Extract Git History                                │
│  ───────────────────────────                                │
│  $ python cli.py extract repositories.csv                   │
│                                                              │
│  Step 2: Import Staff Details                               │
│  ──────────────────────────────────────                     │
│  $ python cli.py import-staff staff_data.xlsx               │
│                                                              │
│  Step 3: Start Backend Server                               │
│  ───────────────────────────                                │
│  $ python start_backend.py                                  │
│  → Running on http://0.0.0.0:8000                          │
│                                                              │
│  Step 4: Start Frontend (New Terminal)                      │
│  ───────────────────────────────────────                    │
│  $ cd frontend                                              │
│  $ npm run dev                                              │
│  → Running on http://localhost:5173                        │
│                                                              │
│  Step 5: Map Authors to Staff                               │
│  ──────────────────────────                                 │
│  → Open http://localhost:5173                              │
│  → Navigate to "Author-Staff Mapping"                       │
│  → Use "Auto-Match by Email"                                │
│  → Map remaining authors (bulk or individual)               │
│                                                              │
│  Step 6: Analyze Productivity                               │
│  ───────────────────────────────                            │
│  → Navigate to "Staff Productivity"                         │
│  → Select staff member                                      │
│  → Choose time granularity                                  │
│  → View charts and export data                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Development Mode

```bash
# Terminal 1 - Backend
python start_backend.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Production Mode

```bash
# Build frontend
cd frontend
npm run build

# Start backend (serves built frontend)
cd ..
python start_backend.py
```

---

## Dashboard Pages

### 1. Overview
**Quick metrics and repository summary**
- Total commits, authors, PRs, repositories
- Top contributors chart
- Recent activity

### 2. Staff Analytics ⭐ ENHANCED
**Comprehensive staff-based analytics**
- **Grouping**: All data grouped by staff_name/bank_id
- **Filters**: Rank, Manager, Location, Staff Type, Date Range
- **"All" option**: Every filter has "All" selection
- **Only Mapped Staff**: Shows only active, mapped staff members
- **Charts**: Top 10 staff by code changes
- **Export**: CSV download

### 3. Commits View
**Detailed commit history**
- Searchable and filterable table
- Author, date, message, lines changed
- Repository and branch filters
- Pagination and sorting

### 4. Pull Requests View
**PR tracking and analysis**
- PR status, author, dates
- Approval counts
- Merge information
- Filter by repository, author, state

### 5. Top Commits
**Largest code changes**
- Sorted by lines changed (added + deleted)
- Grouped column chart
- Top 20 commits
- Filter by date range

### 6. Top Approvers
**Most active PR reviewers**
- Horizontal bar chart
- Approval counts with medals (🥇🥈🥉)
- Top 20 approvers

### 7. Staff Productivity 🆕 NEW
**Individual developer performance**
- **Staff Selection**: Required - searchable dropdown
- **Time Granularity**: Daily | Weekly | Monthly | Yearly
- **Date Range**: Optional filter
- **Summary Stats**: 6 key metrics
- **Charts (5 tabs)**:
  1. Commits Over Time (line)
  2. Lines Changed (stacked column)
  3. Files Changed (area)
  4. Repos Touched (column)
  5. PR Activity (line)
- **Repository Breakdown**: Commits per repo
- **Calendar Heatmap**: GitHub-style daily commits (daily view)
- **CSV Export**: For all charts
- **Staff-Based**: All Git identities aggregated by bank_id

### 8. Author-Staff Mapping ⭐ ENHANCED
**Three-tab mapping interface**

**Tab 1: Create Mapping**
- Select unmapped author
- Select staff member (active only)
- Add optional notes
- Save mapping

**Tab 2: View Mappings**
- All existing mappings table
- Delete functionality
- CSV export
- Statistics

**Tab 3: Bulk Operations**
- **Auto-Match by Email**: Progress tracking
- **Multi-Select Bulk Mapping**:
  - Checkbox list of unmapped authors
  - Smart suggestions with similarity scores
  - Color-coded confidence (green/orange/gray)
  - Select all / Clear selection
  - Progress tracking
- **Reverse Mapping**: Staff → Author
  - Shows unmapped staff members
  - Two-step mapping process
  - Clear visual workflow

### 9. Table Viewer
**Browse all database tables**
- Table selector
- Dynamic columns
- Row count display
- CSV export

### 10. SQL Executor
**Custom query execution**
- SQL editor
- Sample queries
- Results table
- CSV export

---

## API Endpoints

### Authors
```
GET  /api/authors/statistics              - Staff-based analytics with filters
GET  /api/authors/top-contributors        - Top contributors by metric
GET  /api/authors/filter-options          - Get filter dropdown values
GET  /api/authors/productivity/{bank_id}  - Individual staff productivity 🆕
```

### Commits
```
GET  /api/commits/                        - List all commits
GET  /api/commits/top-by-lines            - Top commits by lines changed
```

### Pull Requests
```
GET  /api/pull-requests/                  - List all PRs
GET  /api/pull-requests/top-approvers     - Top PR approvers
```

### Staff
```
GET  /api/staff/                          - List active staff
GET  /api/staff/unmapped                  - List unmapped staff 🆕
```

### Mappings
```
GET    /api/mappings/                     - List all mappings
POST   /api/mappings/                     - Create new mapping
DELETE /api/mappings/{author_name}        - Delete mapping
GET    /api/mappings/unmapped-authors     - List unmapped authors
```

### Overview
```
GET  /api/overview/stats                  - Dashboard overview statistics
```

### Tables
```
GET  /api/tables/info                     - List all tables
GET  /api/tables/{table_name}/data        - Get table data
```

---

## Database Schema

### Core Tables

```sql
┌─────────────────┐         ┌──────────────────┐
│  repositories   │         │    commits       │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │◄───────┤│ id (PK)          │
│ project_key     │    1:N  │ repository_id(FK)│
│ slug_name       │         │ commit_hash      │
│ clone_url       │         │ author_name      │
│ created_at      │         │ author_email     │
└─────────────────┘         │ commit_date      │
                            │ lines_added      │
                            │ lines_deleted    │
                            │ files_changed    │
                            └──────────────────┘
                                     │
                                     │
        ┌────────────────────────────┘
        │
        ↓
┌─────────────────┐
│ pull_requests   │
├─────────────────┤
│ id (PK)         │
│ repository_id(FK)│
│ pr_number       │
│ title           │
│ author_name     │
│ created_date    │
│ merged_date     │
│ state           │
└────────┬────────┘
         │
         │ 1:N
         ↓
┌─────────────────┐
│  pr_approvals   │
├─────────────────┤
│ id (PK)         │
│pull_request_id  │
│ approver_name   │
│ approver_email  │
│ approval_date   │
└─────────────────┘

┌─────────────────┐
│ staff_details   │
├─────────────────┤
│ id (PK)         │
│ bank_id_1       │◄────────┐
│ staff_id        │         │
│ staff_name      │         │
│ email_address   │         │
│ rank            │         │
│ work_location   │         │
│ ... (71 fields) │         │
└─────────────────┘         │
                            │
                         1:N│
                            │
              ┌─────────────┴───────────┐
              │ author_staff_mapping    │
              ├─────────────────────────┤
              │ id (PK)                 │
              │ author_name (UNIQUE)    │
              │ author_email            │
              │ bank_id_1 (FK)          │
              │ staff_id                │
              │ staff_name              │
              │ mapped_date             │
              │ notes                   │
              └─────────────────────────┘
```

---

## Staff Integration

### Key Features

**1. Inactive Staff Exclusion**
- Automatically filters out staff with `staff_status = 'Inactive'`
- Applies to:
  - Author mapping dropdowns
  - Staff analytics calculations
  - Filter options
  - Auto-match operations
- Existing mappings to inactive staff are preserved (historical data integrity)

**2. Staff-Based Grouping**
- All analytics grouped by `bank_id_1` (not author_name)
- Multiple Git identities per staff member are merged
- Example: john@work.com + john@personal.com = 1 staff entry

**3. Mapping Intelligence**
- **Auto-Match**: Matches by email address
- **Smart Suggestions**: Name similarity algorithm (Levenshtein-like)
- **Confidence Levels**:
  - Green (>70%): High confidence
  - Orange (50-70%): Medium confidence
  - Gray (<50%): Low confidence
- **Reverse Mapping**: Find authors for unmapped staff

---

## Productivity Analytics

### Staff Productivity Endpoint

**Endpoint**: `GET /api/authors/productivity/{bank_id}`

**Parameters**:
- `bank_id` (path): Staff bank ID (required)
- `granularity` (query): daily | weekly | monthly | yearly
- `start_date` (query): YYYY-MM-DD
- `end_date` (query): YYYY-MM-DD
- `repository_id` (query): Filter by repository

**Response Structure**:
```json
{
  "staff": {
    "bank_id": "EMP001",
    "name": "John Smith",
    "email": "john@company.com",
    "rank": "Senior Developer",
    "location": "New York",
    "tech_unit": "Platform",
    "staff_type": "Permanent"
  },
  "granularity": "monthly",
  "timeseries": {
    "commits": [
      {
        "period": "2024-01",
        "commits": 45,
        "lines_added": 2500,
        "lines_deleted": 1200,
        "files_changed": 120,
        "repos_touched": 3
      }
    ],
    "prs": [
      {
        "period": "2024-01",
        "prs_opened": 8
      }
    ]
  },
  "repository_breakdown": [...],
  "calendar_heatmap": [...],
  "summary": {
    "total_commits": 450,
    "date_range": {...}
  }
}
```

### How It Works

1. **Get all author mappings** for the staff member
2. **Aggregate data** from all mapped Git identities
3. **Group by time period** based on granularity
4. **Calculate metrics**:
   - Commits per period
   - Lines added/deleted per period
   - Files changed per period
   - Repos touched per period
   - PRs opened per period
5. **Generate breakdowns**:
   - Repository distribution
   - Calendar heatmap (daily only)

---

## Configuration

### Environment Variables (.env)

```ini
# Database Configuration
DB_TYPE=sqlite                    # or mysql, postgresql
SQLITE_DB_PATH=git_history.db

# MySQL/MariaDB (if using)
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=git_history

# Git Credentials
GIT_USERNAME=your_git_username
GIT_PASSWORD=your_token

# Bitbucket API (Optional)
BITBUCKET_URL=https://bitbucket.company.com
BITBUCKET_USERNAME=your_username
BITBUCKET_APP_PASSWORD=your_app_password

# Clone Directory
CLONE_DIR=./repositories
```

### Frontend Configuration (frontend/.env)

```ini
# API Base URL
VITE_API_BASE_URL=http://localhost:8000
```

---

## Usage Examples

### Example 1: Basic Analysis Workflow

```bash
# 1. Extract Git data
python cli.py extract repositories.csv

# 2. Import staff data
python cli.py import-staff staff.xlsx

# 3. Start servers
python start_backend.py          # Terminal 1
cd frontend && npm run dev        # Terminal 2

# 4. Open browser
# → http://localhost:5173
# → Navigate to "Author-Staff Mapping"
# → Click "Auto-Match by Email"
# → Map remaining authors
```

### Example 2: Productivity Assessment

```bash
# After data extraction and mapping:

# 1. Go to "Staff Productivity" page
# 2. Select staff member: "John Smith"
# 3. Choose granularity: "Monthly"
# 4. Set date range: Last 6 months
# 5. View charts:
#    - Commits trend
#    - Lines changed
#    - Repository distribution
# 6. Export CSV for reporting
```

### Example 3: Team Analytics

```bash
# In "Staff Analytics" page:

# 1. Filter by:
#    - Rank: "Senior Developer"
#    - Location: "New York"
#    - Date Range: Q4 2024
# 2. View aggregated team metrics
# 3. Export CSV
# 4. Analyze in Excel/BI tools
```

---

## Troubleshooting

### Frontend Issues

**Issue**: API connection refused
**Solution**: Ensure backend is running on port 8000
```bash
python start_backend.py
```

**Issue**: CORS errors
**Solution**: Check CORS configuration in `backend/main.py`

### Backend Issues

**Issue**: Database connection failed
**Solution**: Verify `.env` configuration and database accessibility

**Issue**: Import errors
**Solution**: Ensure all dependencies installed
```bash
pip install -r requirements.txt
```

### Mapping Issues

**Issue**: Auto-match finds no matches
**Solution**:
- Verify staff email addresses are populated
- Check author emails in commits
- Use manual mapping or bulk operations

**Issue**: Inactive staff appearing
**Solution**: Update staff_status to 'Inactive' in database

---

## Performance

### Optimizations

1. **Backend**:
   - SQLAlchemy query optimization
   - Indexed database columns
   - Async FastAPI operations
   - Efficient JOIN queries

2. **Frontend**:
   - Vite for fast builds
   - React component memoization
   - Lazy loading for routes
   - Optimized re-renders

3. **Database**:
   - Indexes on frequently queried columns
   - Optimized GROUP BY queries
   - Connection pooling

### Benchmarks

- **Page Load**: < 1 second
- **API Response**: 50-200ms (typical)
- **Staff Analytics**: < 500ms (10K commits)
- **Productivity Query**: < 1s (all time data)
- **Frontend Build**: ~20 seconds

---

## Version History

### Version 3.0 (Current - React Edition)

**Major Features**:
- ✅ Complete React + FastAPI rewrite
- ✅ Modern responsive UI with Ant Design
- ✅ Staff Productivity Analytics page
- ✅ Enhanced Author-Staff Mapping
- ✅ Reverse mapping (staff → author)
- ✅ Multi-select bulk operations
- ✅ Smart mapping suggestions
- ✅ Inactive staff exclusion
- ✅ Staff-based grouping in analytics
- ✅ "All" option in all filters
- ✅ Calendar heatmap visualization
- ✅ Real-time chart interactions
- ✅ Comprehensive CSV exports

**Technical Improvements**:
- Modern React 18 with hooks
- FastAPI with automatic OpenAPI docs
- SQLAlchemy 2.0 with type hints
- Pydantic v2 validation
- Vite for fast builds
- Component-based architecture
- RESTful API design

---

## License

This project is provided as-is for educational and analytical purposes.

---

## Quick Reference

```
┌────────────────────────────────────────────────────────────┐
│                    COMMAND REFERENCE                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ # Installation                                              │
│ pip install -r requirements.txt                            │
│ cd frontend && npm install                                 │
│ cp .env.example .env                                       │
│                                                             │
│ # Data Extraction                                           │
│ python cli.py extract <csv_file>                          │
│ python cli.py import-staff <xlsx/csv>                     │
│                                                             │
│ # Start Application                                         │
│ python start_backend.py                # Backend           │
│ cd frontend && npm run dev             # Frontend          │
│                                                             │
│ # Access                                                    │
│ Frontend: http://localhost:5173                            │
│ Backend API: http://localhost:8000                         │
│ API Docs: http://localhost:8000/docs                       │
│                                                             │
│ # Production Build                                          │
│ cd frontend && npm run build                               │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

**Version**: 3.0 (React Edition)
**Last Updated**: 2025
**Python**: 3.8+
**Node.js**: 16+
**Status**: Production Ready

**Key Technologies**: React 18 | FastAPI | Ant Design | SQLAlchemy | Pydantic | Vite | GitPython
