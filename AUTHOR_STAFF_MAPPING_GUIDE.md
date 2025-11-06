# Author-Staff Mapping Guide

## Overview

The Author-Staff Mapping feature allows you to link commit authors from your Git repositories to staff members from your HR database. This enables comprehensive analytics that combine code contributions with staff information.

## Purpose

- **Link Git Identity to HR Identity**: Map author names/emails to official staff records
- **Enable Cross-Analysis**: Combine commit data with staff details (department, role, etc.)
- **Track Team Contributions**: Accurately attribute work to the right people
- **Generate Reports**: Create comprehensive reports linking code activity to staff records

## Database Schema

### New Table: `author_staff_mapping`

```sql
id              INTEGER PRIMARY KEY
author_name     VARCHAR(255) UNIQUE NOT NULL
author_email    VARCHAR(255)
bank_id_1       VARCHAR(50)
staff_id        VARCHAR(50)
staff_name      VARCHAR(255)
mapped_date     DATETIME
notes           TEXT
```

**Key Fields**:
- `author_name`: Unique author name from commits (primary mapping key)
- `bank_id_1`: Bank ID from staff_details table
- `staff_id`: Staff ID from staff_details table
- `mapped_date`: Timestamp when mapping was created/updated
- `notes`: Optional notes about the mapping

## Features

### Tab 1: Create Mapping 🔗

Interactive interface for creating individual author-staff mappings.

#### Components:

**Left Column - Select Author**:
- Dropdown list of all commit authors
- Shows commit count for each author
- Displays author email
- Auto-filters out already-mapped authors
- Shows mapping progress (Total/Unmapped count)

**Right Column - Select Staff Member**:
- Search functionality by name or email
- Dropdown list of staff from staff_details
- Shows Bank ID, Staff ID, Email, and Tech Unit
- Real-time filtering based on search

**Bottom Section - Save Mapping**:
- Optional notes field
- Save button to create mapping
- Success animation on save
- Auto-refresh to show next unmapped author

#### Workflow:

```
1. Select an author from dropdown (left)
2. Search for matching staff member (right)
3. Select staff member from filtered list
4. Add optional notes
5. Click "Save Mapping"
6. System creates mapping and shows next unmapped author
```

### Tab 2: View Mappings 📊

View, manage, and export existing mappings.

#### Features:

**Summary Metrics**:
- Total Mappings count
- Mapping Coverage percentage
- Last Mapping date

**Mappings Table**:
- All existing mappings in tabular format
- Columns: Author Name, Email, Bank ID, Staff ID, Staff Name, Mapped Date, Notes
- Sortable and filterable

**Delete Functionality**:
- Select mapping to delete
- One-click delete with confirmation
- Auto-refresh after deletion

**Export**:
- Download all mappings as CSV
- Timestamped filename
- All columns included

### Tab 3: Bulk Operations ⚡

Automate mapping creation for multiple authors.

#### Auto-Match by Email

Automatically creates mappings when author email matches staff email.

**Process**:
1. System compares unmapped author emails with staff emails
2. Shows list of potential matches
3. User reviews matches
4. Click "Apply All Email Matches"
5. System creates all mappings with progress bar
6. Shows success/error summary

**Benefits**:
- Fast bulk mapping
- High accuracy (exact email match)
- Progress tracking
- Error handling

#### Upload Mappings from CSV

Import mappings from external CSV file.

**CSV Format**:
```csv
Author Name,Author Email,Bank ID,Staff ID,Staff Name,Notes
John Doe,john.doe@company.com,B12345,S67890,John Doe,Manual mapping
Jane Smith,jane@company.com,B23456,S78901,Jane Smith,
```

**Required Columns**:
- Author Name (required)
- Bank ID (required)
- Staff ID (required)
- Staff Name (required)

**Optional Columns**:
- Author Email
- Notes

**Process**:
1. Prepare CSV file with required columns
2. Upload CSV via file uploader
3. Preview data
4. Click "Import Mappings"
5. System processes with progress bar
6. Shows import summary

## Use Cases

### 1. Initial Setup

After importing staff details and extracting commits:

```
1. Go to "Author-Staff Mapping" page
2. Click "Bulk Operations" tab
3. Use "Auto-Match by Email" to map most authors
4. Switch to "Create Mapping" tab
5. Manually map remaining authors
```

### 2. New Staff Members

When new employees join:

```
1. Import updated staff details
2. Extract commits from repositories
3. Use "Create Mapping" to map new authors
```

### 3. Name Changes

When staff members change names:

```
1. Go to "View Mappings" tab
2. Delete old mapping
3. Go to "Create Mapping" tab
4. Create new mapping with updated name
```

### 4. Migration from Other Systems

When importing mappings from another system:

```
1. Export mappings from old system
2. Format as CSV with required columns
3. Use "Bulk Operations" → "Upload Mappings from CSV"
```

## Best Practices

### Mapping Strategy

1. **Start with Auto-Match**: Use email matching first to handle bulk of mappings
2. **Manual Review**: Review auto-matched entries in "View Mappings" tab
3. **Add Notes**: Document unusual mappings or special cases
4. **Regular Updates**: Update mappings when staff details change

### Data Quality

1. **Verify Email Accuracy**: Ensure staff_details has correct emails
2. **Check for Duplicates**: Review mappings for duplicate author names
3. **Handle Variations**: Map name variations (e.g., "John Doe" and "J. Doe")
4. **Document Exceptions**: Use notes field for special cases

### Maintenance

1. **Regular Audits**: Periodically review mappings for accuracy
2. **Export Backups**: Download CSV backups regularly
3. **Update After HR Changes**: Update mappings when staff details change
4. **Monitor Coverage**: Track mapping coverage percentage

## Analytics Integration

Once mappings are created, you can:

### SQL Queries

**Commits by Department**:
```sql
SELECT sd.tech_unit, COUNT(c.id) as commits
FROM commits c
JOIN author_staff_mapping asm ON c.author_name = asm.author_name
JOIN staff_details sd ON asm.bank_id_1 = sd.bank_id_1
GROUP BY sd.tech_unit
ORDER BY commits DESC;
```

**Lines Changed by Staff Level**:
```sql
SELECT sd.staff_level,
       SUM(c.lines_added + c.lines_deleted) as total_lines
FROM commits c
JOIN author_staff_mapping asm ON c.author_name = asm.author_name
JOIN staff_details sd ON asm.bank_id_1 = sd.bank_id_1
GROUP BY sd.staff_level
ORDER BY total_lines DESC;
```

**Active Contributors by Platform**:
```sql
SELECT sd.platform_name,
       COUNT(DISTINCT asm.author_name) as contributors,
       SUM(commit_counts.total) as commits
FROM author_staff_mapping asm
JOIN staff_details sd ON asm.bank_id_1 = sd.bank_id_1
JOIN (
    SELECT author_name, COUNT(*) as total
    FROM commits
    GROUP BY author_name
) commit_counts ON asm.author_name = commit_counts.author_name
GROUP BY sd.platform_name
ORDER BY contributors DESC;
```

### Dashboard Analytics

With mappings in place, you can create:
- Team productivity reports
- Department-level code metrics
- Staff performance analytics
- Platform contribution analysis

## Troubleshooting

### No Authors Found

**Problem**: "No commit authors found" message
**Solution**:
- Extract commits first using CLI: `python cli.py extract repositories.csv`
- Verify commits exist in database using SQL Executor

### No Staff Found

**Problem**: "No staff details found" message
**Solution**:
- Import staff details using CLI: `python cli.py import-staff staff_data.xlsx`
- Verify staff_details table has data using Table Viewer

### Email Match Failures

**Problem**: Auto-match by email finds no matches
**Causes**:
1. Email formats don't match (e.g., case sensitivity)
2. Emails in commits differ from HR records
3. Staff details missing emails

**Solutions**:
- Manually create mappings using "Create Mapping" tab
- Update staff_details with correct emails
- Use CSV import for bulk mapping

### Mapping Update Errors

**Problem**: Cannot update existing mapping
**Solution**:
- Delete old mapping first
- Create new mapping
- Or use CSV import to overwrite

### Duplicate Authors

**Problem**: Same person has multiple author names
**Approach**:
1. Map primary author name
2. Add notes explaining other variations
3. Consider using SQL to consolidate data

## Performance

### Large Datasets

**Authors**: Supports thousands of distinct authors
**Staff**: Handles large staff_details tables efficiently
**Bulk Operations**: Progress bar for long-running operations

### Optimization Tips

1. **Use Auto-Match First**: Faster than manual mapping
2. **Search Before Scrolling**: Use search in staff selection
3. **Batch CSV Imports**: Better for 100+ mappings
4. **Export Regularly**: Keep CSV backups for quick restore

## Security & Privacy

### Data Protection

- Mappings stored in local database
- No external transmission
- Follows same security as main database

### Access Control

- Dashboard provides read/write access
- Recommend protecting dashboard with authentication
- Consider read-only database users for reporting

## Migration & Export

### Export All Mappings

```
1. Go to "View Mappings" tab
2. Click "Download Mappings as CSV"
3. Save file with timestamp
```

### Import to Another Instance

```
1. Export mappings from source
2. Transfer CSV file
3. Use "Upload Mappings from CSV" in target
```

### Backup Strategy

**Recommended Schedule**:
- Weekly CSV exports
- Before major mapping updates
- After bulk import operations

## Advanced Usage

### SQL Integration

Access mappings in custom queries via SQL Executor:

```sql
-- Join commits with staff details
SELECT c.*, sd.tech_unit, sd.platform_name
FROM commits c
JOIN author_staff_mapping asm ON c.author_name = asm.author_name
JOIN staff_details sd ON asm.bank_id_1 = sd.bank_id_1
WHERE c.commit_date >= '2024-01-01';
```

### Programmatic Access

Access via Python:

```python
from models import get_engine, get_session, AuthorStaffMapping

engine = get_engine(db_config)
session = get_session(engine)

# Get all mappings
mappings = session.query(AuthorStaffMapping).all()

# Get specific mapping
mapping = session.query(AuthorStaffMapping)\
    .filter_by(author_name='John Doe')\
    .first()
```

## FAQ

**Q: Can one author be mapped to multiple staff members?**
A: No, author_name is unique. One author = one staff member.

**Q: What happens if I update a staff member's details?**
A: Mapping uses bank_id_1, so it will reflect updated staff details automatically.

**Q: Can I map authors without email?**
A: Yes, author_email is optional in the mapping.

**Q: How do I handle contractors vs employees?**
A: Use the notes field to document staff type, or filter by staff_type in staff_details.

**Q: What if an author leaves the company?**
A: Keep the mapping for historical accuracy. Mark in notes if needed.

**Q: Can I bulk delete mappings?**
A: Currently no, but you can use SQL Executor:
```sql
DELETE FROM author_staff_mapping WHERE notes LIKE '%test%';
```

## Summary

The Author-Staff Mapping feature provides:
- ✅ Interactive mapping interface
- ✅ Bulk auto-matching by email
- ✅ CSV import/export
- ✅ Mapping management and tracking
- ✅ Integration with analytics
- ✅ Progress tracking and error handling

**Getting Started**:
```bash
# 1. Import staff details
python cli.py import-staff staff_data.xlsx

# 2. Extract commits
python cli.py extract repositories.csv

# 3. Launch dashboard
streamlit run dashboard.py

# 4. Navigate to "Author-Staff Mapping"
# 5. Use "Bulk Operations" → "Auto-Match by Email"
# 6. Manually map remaining authors
```

This enables powerful cross-analysis between code contributions and staff information!
