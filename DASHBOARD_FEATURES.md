# Dashboard Features Guide

## Overview

The Git History Analysis Dashboard provides comprehensive visualizations and analytics for Git repository data, including commits, pull requests, approvals, and staff information.

## Pages and Features

### 1. Overview
- **Quick Statistics**: Total commits, authors, repositories, and lines changed
- **At-a-glance summary** of the entire dataset

### 2. Authors Analytics 👨‍💻
**NEW: Date Range Filter** 📅

Comprehensive statistics for all contributors with powerful filtering capabilities.

#### Features:
- ✅ **Date Range Selection**: Filter all statistics by commit date range
  - Start Date and End Date pickers
  - Shows min/max dates from your data
  - Displays date range info (number of days)
  - Reset button to restore full range

- ✅ **Dynamic Summary Metrics** (filtered by date range):
  - Total Authors (who contributed in the period)
  - Total Commits (within date range)
  - Total Lines Changed (within date range)
  - Total PRs (created and approved in the period)

- ✅ **Visual Analytics** (filtered by date range):
  - Top 10 Contributors by Commits (bar chart)
  - Top 10 Contributors by Lines Changed (grouped bar chart)

- ✅ **Detailed Statistics Table**:
  - Sortable by any metric
  - Shows: Commits, Lines Added/Deleted, Files Changed, Repositories, PRs Created/Approved
  - Download as CSV

- ✅ **Insights Section**:
  - Most Active Author (in date range)
  - Most Lines Changed (in date range)
  - Top PR Approver (in date range)

#### Usage Example:

```
1. Navigate to "Authors Analytics"
2. Select Start Date: 2024-01-01
3. Select End Date: 2024-12-31
4. View filtered statistics for 2024
5. Sort by "Total Commits" descending
6. Download filtered results as CSV
```

#### Use Cases:

**Quarterly Reviews**:
- Set date range to Q1, Q2, Q3, or Q4
- Compare contributor activity across quarters
- Identify trends in commit patterns

**Monthly Reports**:
- Filter to specific month
- Generate monthly contributor reports
- Track team productivity over time

**Project Milestones**:
- Filter to project start/end dates
- Analyze team contributions during critical periods
- Measure impact before/after major changes

**Performance Reviews**:
- Filter to review period (e.g., last 6 months)
- Export individual contributor statistics
- Track growth and contributions over time

### 3. Top 10 Commits
- Largest commits by lines changed
- Visual bar chart
- Detailed commit information table

### 4. Top PR Approvers
- Most active code reviewers
- Horizontal bar chart
- Approval counts and details

### 5. Detailed Commits View
- **Filters**: Author, Repository, Branch, Date Range
- **Sorting**: By date, lines, files changed
- **Export**: Download filtered commits as CSV
- Full commit details with messages

### 6. Detailed PRs View
- **Filters**: Author, Repository, State, Date Range
- **Sorting**: By date, lines, approvals, commits
- **Export**: Download filtered PRs as CSV
- PR metadata including approvals count

### 7. Table Viewer 📋
- Browse all database tables
- Tables overview with row counts
- Configurable row limits
- Column statistics and information
- Export any table as CSV

**Available Tables**:
- repositories
- commits
- pull_requests
- pr_approvals
- staff_details

### 8. SQL Executor ⚡
- Execute custom SQL queries
- 6 sample query templates
- Database schema reference
- Safety warnings for destructive queries
- Export query results as CSV

**Sample Queries**:
- Top Authors by Commits
- PRs with Most Approvals
- Commits by Month
- Staff by Department
- Join Commits with Repositories

## Technical Details

### Date Range Filtering

The Authors Analytics date range filter applies to:

1. **Commits**: Filtered by `commit_date`
2. **Pull Requests**: Filtered by `created_date`
3. **PR Approvals**: Filtered by `approval_date`

All three data sources are independently filtered and then aggregated to provide accurate statistics for the selected period.

### Filter Implementation

```python
# Date range applies to:
- Commit statistics (commit_date)
- PR creation statistics (created_date)
- PR approval statistics (approval_date)

# Results show only:
- Authors who contributed within date range
- Commits made within date range
- PRs created within date range
- Approvals given within date range
```

### Performance

- Date filtering is done at the database level (efficient)
- Uses indexed date columns for fast queries
- Aggregations computed on filtered results
- Typical query time: < 1 second for 10K+ commits

## Best Practices

### Using Date Range Filters

1. **Start Broad, Then Narrow**:
   - Begin with full date range to see overall trends
   - Narrow down to specific periods for detailed analysis

2. **Compare Periods**:
   - Filter to Q1, export data
   - Filter to Q2, export data
   - Compare externally in Excel/spreadsheet

3. **Regular Intervals**:
   - Use monthly or quarterly intervals for consistent reporting
   - Track changes over time

4. **Reset When Needed**:
   - Use the Reset button to return to full dataset
   - Helpful when exploring different date ranges

### Data Export

All filtered views support CSV export:
- Exports include only filtered/sorted data
- Timestamped filenames prevent overwrites
- Open in Excel, Google Sheets, or data analysis tools

### Combining Features

**Workflow Example**:
```
1. Authors Analytics → Filter to last quarter → Identify top contributor
2. Detailed Commits View → Filter by top contributor → See all their commits
3. SQL Executor → Custom query for deeper analysis → Export results
```

## Advanced Usage

### Date Range + Sorting

Combine date filtering with sorting for powerful insights:

```
Filter: Last 6 months
Sort by: Lines Deleted (Descending)
Result: Find who's been cleaning up the most code recently
```

### Multi-Step Analysis

1. **Identify Period**: Use date range to focus on specific timeframe
2. **Find Contributors**: See who was active in that period
3. **Drill Down**: Use Detailed Commits/PRs views for specifics
4. **Custom Analysis**: Use SQL Executor for complex queries

### Exporting for Reports

**Monthly Report Process**:
```
1. Set date range to last month
2. Export Authors Analytics as CSV
3. Export Detailed Commits View as CSV
4. Export Detailed PRs View as CSV
5. Combine in reporting tool/spreadsheet
```

## Troubleshooting

### Date Range Issues

**Problem**: "No author data available for the selected date range"
**Solution**:
- Verify commits exist in that date range
- Use Table Viewer to check commits table
- Expand date range to include more data

**Problem**: Reset button doesn't work
**Solution**:
- Streamlit may cache state - refresh page (F5)
- Or manually adjust dates to full range

**Problem**: Statistics seem incomplete
**Solution**:
- Ensure date range includes all desired data
- Check that PRs/approvals have valid dates
- Use SQL Executor to verify data quality

### Performance

**Large Date Ranges**:
- Full dataset queries may take 1-2 seconds
- Use smaller date ranges for faster results
- Database indexes optimize date filtering

**Memory Usage**:
- Exports create CSV files in memory
- Very large exports (100K+ rows) may be slow
- Use SQL Executor with LIMIT for sampling

## Future Enhancements

Potential additions:
- Date range presets (Last 7 days, Last month, Last quarter, Last year)
- Compare two date ranges side-by-side
- Date range visualization (timeline chart)
- Save/load custom date range filters
- Export multiple date ranges in batch

## Quick Reference

### Navigation
```
Sidebar → Select Page → Apply Filters → View/Export Results
```

### Key Shortcuts
- **F5**: Refresh dashboard
- **Reset Dates**: Return to full date range
- **Download CSV**: Export current filtered view

### Common Tasks

**Find Top Contributors This Quarter**:
```
Authors Analytics → Set Q1-Q4 dates → Sort by Total Commits
```

**Review Team Activity Last Month**:
```
Authors Analytics → Set last month dates → View summary metrics
```

**Export Filtered Data**:
```
Apply date filter → Click "Download ... as CSV"
```

---

**Quick Start**:
```bash
streamlit run dashboard.py
```

Navigate to any page from the sidebar and start exploring your Git history data!
