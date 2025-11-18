# Data Population Workflow - Complete Guide

## Date: November 18, 2025
## Version: 3.4

---

## Overview

This guide explains the correct order of operations to populate all database tables, including the staff_metrics table required for the optimized Staff Details page.

---

## Current Database Status

```
staff_details: 0 records (EMPTY - needs data!)
author_staff_mapping: 0 records (EMPTY - needs data!)
staff_metrics: 0 records (EMPTY - will be populated after above tables)
commits: 12 records (has data)
pull_requests: 1 record (has data)
```

---

## Why staff_metrics is Empty

The `staff_metrics` table depends on:
1. **staff_details** table - HR master data (staff information)
2. **author_staff_mapping** table - Maps Git authors to staff members

**Current Issue**: Both prerequisite tables are empty, so staff_metrics calculator has no data to work with.

---

## Complete Workflow

### Step 1: Import Staff Details (REQUIRED FIRST)

Import staff information from HR systems (Excel/CSV file).

**Command**:
```bash
python -m cli import-staff path/to/staff_data.xlsx
```

**What it does**:
- Reads staff information from Excel/CSV file
- Populates `staff_details` table with:
  - bank_id_1 (primary key)
  - staff_name, email_address
  - staff_type, staff_status, rank
  - department_id, company_name, hr_role
  - work_location, platform_name, tech_unit
  - And other organizational fields

**Expected File Format**:
```
Column Names (minimum required):
- bank_id_1 (or staff ID)
- staff_name
- email_address
- staff_status (Active/Inactive)
```

**Verify**:
```bash
python -c "from cli.config import Config; from cli.models import get_engine, get_session, StaffDetails; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); print(f'Staff Details: {session.query(StaffDetails).count()} records')"
```

---

### Step 2: Extract Git History (WITH Author Mapping)

Extract commits and PRs from Git repositories.

**Command**:
```bash
python -m cli extract path/to/repositories.csv
```

**What it does**:
1. Clones repositories listed in CSV file
2. Extracts commits and pull requests
3. Creates `author_staff_mapping` (maps git author emails to staff)
4. Stores commits in `commits` table
5. Stores PRs in `pull_requests` table
6. **Automatically calculates staff_metrics** after extraction

**Expected CSV Format**:
```
Project Key,Slug Name,Clone URL
PROJECT1,repo-name-1,https://bitbucket.org/workspace/repo1.git
PROJECT2,repo-name-2,https://bitbucket.org/workspace/repo2.git
```

**Verify**:
```bash
python -c "from cli.config import Config; from cli.models import get_engine, get_session, AuthorStaffMapping, Commit, PullRequest, StaffMetrics; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); print(f'Author Mappings: {session.query(AuthorStaffMapping).count()}'); print(f'Commits: {session.query(Commit).count()}'); print(f'Pull Requests: {session.query(PullRequest).count()}'); print(f'Staff Metrics: {session.query(StaffMetrics).count()}')"
```

---

### Step 3: Calculate All Metrics (OPTIONAL - Auto-runs after extract)

If you need to recalculate metrics manually or after making changes.

**Command**:
```bash
python -m cli calculate-metrics --all
```

**What it does**:
- Calculates `staff_metrics` (staff productivity)
- Calculates `commit_metrics` (daily commit aggregations)
- Calculates `pr_metrics` (daily PR aggregations)
- Calculates `repository_metrics` (repo statistics)
- Calculates `author_metrics` (author productivity)
- Calculates `team_metrics` (team aggregations)
- Calculates `daily_metrics` (daily org metrics)

**Individual Metric Calculation**:
```bash
# Calculate only staff metrics
python -m cli calculate-metrics --staff

# Calculate only repository metrics
python -m cli calculate-metrics --repositories

# Calculate multiple specific metrics
python -m cli calculate-metrics --staff --commits --prs
```

**Force Recalculation** (ignores timestamps):
```bash
python -m cli calculate-metrics --all --force
```

---

## Quick Start (Full Workflow)

```bash
# 1. Import staff data FIRST
python -m cli import-staff staff_data.xlsx

# 2. Extract git history (auto-calculates metrics)
python -m cli extract repositories.csv

# 3. (Optional) Manually recalculate if needed
python -m cli calculate-metrics --all

# 4. Verify all tables populated
python -c "from cli.config import Config; from cli.models import get_engine, get_session, StaffDetails, AuthorStaffMapping, StaffMetrics, Commit, PullRequest; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); print('=== TABLE COUNTS ==='); print(f'staff_details: {session.query(StaffDetails).count()}'); print(f'author_staff_mapping: {session.query(AuthorStaffMapping).count()}'); print(f'staff_metrics: {session.query(StaffMetrics).count()}'); print(f'commits: {session.query(Commit).count()}'); print(f'pull_requests: {session.query(PullRequest).count()}')"
```

---

## Data Flow Diagram

```
┌──────────────────────┐
│   Staff Data File    │
│   (Excel/CSV)        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Step 1: import-staff        │
│  Populates: staff_details    │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Repositories CSV File       │
└──────┬───────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Step 2: extract                       │
│  Populates:                            │
│  - commits                             │
│  - pull_requests                       │
│  - author_staff_mapping (auto-maps)    │
│  Auto-runs: calculate_staff_metrics    │
└──────┬─────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Step 3: calculate-metrics --all    │
│  Populates all metric tables:       │
│  - staff_metrics ✓                  │
│  - commit_metrics                   │
│  - pr_metrics                       │
│  - repository_metrics               │
│  - author_metrics                   │
│  - team_metrics                     │
│  - daily_metrics                    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  All Tables Populated!       │
│  Staff Details Page Ready    │
└──────────────────────────────┘
```

---

## Table Dependencies

### Level 1 (No Dependencies - Import First)
- **staff_details** ← Imported from Excel/CSV
- **commits** ← Extracted from Git
- **pull_requests** ← Extracted from Git

### Level 2 (Depends on Level 1)
- **author_staff_mapping** ← Created during extract (maps git authors → staff)

### Level 3 (Depends on Level 1 + 2 - Calculated Metrics)
- **staff_metrics** ← Depends on: staff_details + author_staff_mapping + commits + pull_requests
- **commit_metrics** ← Depends on: commits
- **pr_metrics** ← Depends on: pull_requests
- **repository_metrics** ← Depends on: commits + pull_requests
- **author_metrics** ← Depends on: commits + pull_requests
- **team_metrics** ← Depends on: commits + pull_requests + staff_details
- **daily_metrics** ← Depends on: commits + pull_requests

---

## Troubleshooting

### Problem: staff_metrics table is empty

**Diagnosis**:
```bash
python -c "from cli.config import Config; from cli.models import get_engine, get_session, StaffDetails, AuthorStaffMapping; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); print(f'staff_details: {session.query(StaffDetails).count()}'); print(f'author_staff_mapping: {session.query(AuthorStaffMapping).count()}')"
```

**Solutions**:

1. **If staff_details is 0**:
   ```bash
   # Import staff data first
   python -m cli import-staff staff_data.xlsx
   ```

2. **If author_staff_mapping is 0**:
   ```bash
   # Extract git data (this creates mappings)
   python -m cli extract repositories.csv
   ```

3. **If both tables have data but staff_metrics is still empty**:
   ```bash
   # Manually calculate staff metrics
   python -m cli calculate-metrics --staff
   ```

---

### Problem: "No module named 'openpyxl'" when importing staff

**Solution**:
```bash
pip install openpyxl pandas
```

---

### Problem: Staff metrics calculation shows "0/0 processed"

**Cause**: No author mappings exist

**Solution**:
```bash
# Run extract to create author mappings
python -m cli extract repositories.csv
```

---

### Problem: UTF-8 encoding errors during import

**Solution**: Ensure your Excel/CSV file is saved with UTF-8 encoding, or specify encoding:
```bash
python -m cli import-staff staff_data.csv --encoding utf-8
```

---

## Performance Expectations

### Initial Data Load

| Operation | Records | Time | Notes |
|-----------|---------|------|-------|
| Import staff (1,000) | 1,000 | ~5-10 sec | Depends on file size |
| Import staff (10,000) | 10,000 | ~30-60 sec | |
| Extract 1 repo | Varies | ~30-120 sec | Depends on repo size |
| Extract 10 repos | Varies | ~5-20 min | Parallel processing |
| Calculate staff metrics (1,000) | 1,000 | ~10-30 sec | |
| Calculate staff metrics (10,000) | 10,000 | ~2-5 min | |
| Calculate all metrics | All | ~5-15 min | For 10,000 staff, 100 repos |

### Incremental Updates

| Operation | Time | Notes |
|-----------|------|-------|
| Re-extract single repo | ~30-60 sec | Updates existing data |
| Recalculate staff metrics | ~1-3 min | For 10,000 staff |
| Recalculate all metrics | ~3-10 min | Only recalcs changed data |

---

## Automated Workflow Example

Create a script `populate_data.sh` (Linux/Mac) or `populate_data.bat` (Windows):

**populate_data.sh**:
```bash
#!/bin/bash
set -e

echo "==================================="
echo "Data Population Workflow"
echo "==================================="

# Step 1: Import staff
echo "Step 1: Importing staff data..."
python -m cli import-staff data/staff_data.xlsx

# Step 2: Extract repositories
echo "Step 2: Extracting git history..."
python -m cli extract data/repositories.csv

# Step 3: Calculate all metrics (optional - already done in extract)
echo "Step 3: Calculating all metrics..."
python -m cli calculate-metrics --all --force

echo "==================================="
echo "Data population complete!"
echo "==================================="

# Verify counts
python -c "from cli.config import Config; from cli.models import get_engine, get_session, StaffMetrics; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); print(f'\nStaff Metrics: {session.query(StaffMetrics).count()} records')"
```

**populate_data.bat** (Windows):
```batch
@echo off
echo ===================================
echo Data Population Workflow
echo ===================================

REM Step 1: Import staff
echo Step 1: Importing staff data...
python -m cli import-staff data\staff_data.xlsx
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM Step 2: Extract repositories
echo Step 2: Extracting git history...
python -m cli extract data\repositories.csv
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM Step 3: Calculate all metrics
echo Step 3: Calculating all metrics...
python -m cli calculate-metrics --all --force
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo ===================================
echo Data population complete!
echo ===================================

REM Verify counts
python -c "from cli.config import Config; from cli.models import get_engine, get_session, StaffMetrics; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); print(f'\nStaff Metrics: {session.query(StaffMetrics).count()} records')"
```

---

## Regular Maintenance

### Daily Updates (Recommended)

```bash
# Re-extract changed repositories (incremental)
python -m cli extract repositories.csv

# This automatically recalculates staff_metrics
```

### Weekly Full Refresh (Recommended)

```bash
# Force recalculation of all metrics
python -m cli calculate-metrics --all --force
```

### Monthly Staff Data Sync

```bash
# Re-import updated staff data
python -m cli import-staff staff_data_latest.xlsx

# Recalculate staff metrics with new data
python -m cli calculate-metrics --staff --force
```

---

## Integration with Staff Details Page

Once data is populated:

1. **Restart Backend**:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```

2. **Open Staff Details Page**:
   ```
   http://localhost:3000/staff-details
   ```

3. **Expected Behavior**:
   - Page loads in < 1 second
   - Shows all staff with pre-calculated metrics
   - Commit counts, PR counts, approval counts visible
   - Expanding a row loads detailed data on-demand

---

## Verification Commands

### Check All Table Counts
```bash
python -c "from cli.config import Config; from cli.models import get_engine, get_session, StaffDetails, AuthorStaffMapping, StaffMetrics, Commit, PullRequest, CommitMetrics, PRMetrics, RepositoryMetrics; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); print('=== TABLE COUNTS ==='); print(f'staff_details: {session.query(StaffDetails).count()}'); print(f'author_staff_mapping: {session.query(AuthorStaffMapping).count()}'); print(f'staff_metrics: {session.query(StaffMetrics).count()}'); print(f'commits: {session.query(Commit).count()}'); print(f'pull_requests: {session.query(PullRequest).count()}'); print(f'commit_metrics: {session.query(CommitMetrics).count()}'); print(f'pr_metrics: {session.query(PRMetrics).count()}'); print(f'repository_metrics: {session.query(RepositoryMetrics).count()}')"
```

### Check Sample Staff Metrics
```bash
python -c "from cli.config import Config; from cli.models import get_engine, get_session, StaffMetrics; config = Config(); engine = get_engine(config.get_db_config()); session = get_session(engine); samples = session.query(StaffMetrics).limit(3).all(); print('=== SAMPLE STAFF METRICS ==='); [print(f'{s.staff_name}: {s.total_commits} commits, {s.total_prs_created} PRs') for s in samples]"
```

---

## Related Documentation

- [STAFF_DETAILS_OPTIMIZATION.md](STAFF_DETAILS_OPTIMIZATION.md) - Staff Details page optimization
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete setup instructions
- [README.md](README.md) - Project overview

---

## Summary

**Correct Order**:
1. ✅ Import staff data → populates `staff_details`
2. ✅ Extract git history → populates `commits`, `pull_requests`, `author_staff_mapping`
3. ✅ Calculate metrics (auto or manual) → populates `staff_metrics` and other metric tables

**Current Status**:
- ❌ Step 1 not done (staff_details is empty)
- ✅ Step 2 partially done (commits/PRs exist, but no author mappings)
- ❌ Step 3 can't complete without Step 1 & 2

**Action Required**:
Run `python -m cli import-staff <your_staff_file>` to populate staff data first!

---

**Version**: 3.4
**Last Updated**: November 18, 2025
**Status**: ✅ Complete Documentation
