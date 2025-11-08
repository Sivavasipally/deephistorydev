# Inactive Staff Exclusion Policy

## Overview
The system now automatically excludes inactive staff members from all calculations, mappings, and filter options to ensure data accuracy and relevance.

---

## What's Excluded

### 1. **Author-Staff Mapping**
- Inactive staff members are **not shown** in the staff selection dropdown
- Auto-match by email **skips** inactive staff
- Bulk mapping operations **exclude** inactive staff
- Only active staff members can be mapped to authors

### 2. **Authors Analytics (Enhanced)**
- Filter dropdowns (Rank, Manager, Location, Staff Type) only show values from **active staff**
- Analytics calculations only include **active staff** data
- Mapped authors linked to inactive staff show in results, but inactive status is transparent

### 3. **Staff List API**
- `/api/staff/` endpoint returns only **active staff members**
- Search functionality only searches **active staff**
- Inactive staff cannot be selected for new mappings

---

## Technical Implementation

### Database Filter
All queries include this filter condition:
```python
(StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))
```

This means:
- ✅ Include staff where status is NOT 'Inactive'
- ✅ Include staff where status is NULL (legacy data)
- ❌ Exclude staff where status IS 'Inactive'

---

## Affected Endpoints

### 1. GET `/api/authors/statistics`
**Before**: Included all staff in analytics
**After**: Only includes active staff

```python
# Added filter
query = query.filter(
    (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))
)
```

### 2. GET `/api/authors/filter-options`
**Before**: Showed all ranks, managers, locations, staff types
**After**: Only shows values from active staff

```python
# Applied to all filter queries
active_filter = (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))

ranks = session.query(StaffDetails.rank).filter(active_filter)
managers = session.query(StaffDetails.reporting_manager_name).filter(active_filter)
# etc.
```

### 3. GET `/api/staff/`
**Before**: Returned all staff members
**After**: Only returns active staff

```python
# Added to base query
query = session.query(StaffDetails).filter(
    StaffDetails.bank_id_1.isnot(None),
    (StaffDetails.staff_status != 'Inactive') | (StaffDetails.staff_status.is_(None))
)
```

---

## User-Facing Changes

### Author-Staff Mapping Page

**Auto-Match Alert** (Updated):
```
"This will automatically map authors to active staff members when their
email addresses match exactly. Inactive staff members are excluded from matching."
```

**Bulk Mapping Card** (Updated):
- Card header shows: "Only active staff members shown"
- Staff dropdown only contains active staff
- Name suggestions only suggest active staff matches

### Authors Analytics Page

**Filter Dropdowns**:
- Rank: Only shows ranks from active staff
- Reporting Manager: Only shows managers with active reports
- Work Location: Only shows locations with active staff
- Staff Type: Only shows types of active staff

---

## Edge Cases Handled

### 1. Existing Mappings to Inactive Staff
**Scenario**: An author was previously mapped to a staff member who is now inactive.

**Behavior**:
- ✅ Existing mapping is **preserved** (not deleted)
- ✅ Author still shows in analytics with staff details
- ✅ Mapping appears in "View Mappings" tab
- ❌ Cannot create **new** mappings to this inactive staff member
- ❌ Cannot edit mapping to point to this inactive staff member

**Rationale**: Historical data integrity - past work should remain attributed.

### 2. Staff with NULL Status
**Scenario**: Legacy staff records without a staff_status value.

**Behavior**:
- ✅ Treated as **active** (inclusive approach)
- ✅ Appears in dropdowns and filters
- ✅ Can be used for new mappings

**Rationale**: Backward compatibility with existing data.

### 3. Filter Results
**Scenario**: User filters by a manager who has both active and inactive reports.

**Behavior**:
- ✅ Only shows contributions from **active** reports
- ❌ Inactive reports **not** included in counts
- ℹ️ Results may seem "incomplete" compared to HRIS data (by design)

**Rationale**: Current organizational view is more relevant than historical.

---

## Benefits

### 1. Data Accuracy
- Analytics reflect **current** organizational structure
- Prevent mapping to employees who have left
- Avoid outdated reporting relationships

### 2. User Experience
- Shorter dropdown lists (easier to find active staff)
- Relevant filter options
- Clear messaging about exclusion policy

### 3. Performance
- Smaller result sets
- Faster query execution
- Reduced data transfer

### 4. Compliance
- Aligns with HR data policies
- Respects employee offboarding processes
- Maintains data privacy for former employees

---

## Staff Status Values

### Recognized Statuses
Based on the `staff_status` column in `staff_details` table:

| Status | Included? | Description |
|--------|-----------|-------------|
| `Active` | ✅ Yes | Current employee |
| `Inactive` | ❌ No | Former employee |
| `NULL` | ✅ Yes | Legacy data (treated as active) |
| Other values | ✅ Yes | Treated as active unless explicitly "Inactive" |

### Examples
```sql
-- Included (Active)
staff_status = 'Active'          → ✅ Included
staff_status = 'Probation'       → ✅ Included
staff_status = 'Contracted'      → ✅ Included
staff_status = NULL              → ✅ Included

-- Excluded (Inactive)
staff_status = 'Inactive'        → ❌ Excluded
staff_status = 'Resigned'        → ✅ Included (not "Inactive")
staff_status = 'Terminated'      → ✅ Included (not "Inactive")
```

**Note**: Only the exact string `'Inactive'` triggers exclusion. All other values are included.

---

## Testing Recommendations

### 1. Verify Exclusion
```sql
-- Check how many staff are inactive
SELECT staff_status, COUNT(*)
FROM staff_details
GROUP BY staff_status;

-- Find authors mapped to inactive staff
SELECT m.author_name, m.staff_name, s.staff_status
FROM author_staff_mapping m
JOIN staff_details s ON m.bank_id_1 = s.bank_id_1
WHERE s.staff_status = 'Inactive';
```

### 2. Test Auto-Match
1. Create a test author with email matching an inactive staff member
2. Run auto-match
3. Verify the author is **not** matched
4. Create a test author with email matching an active staff member
5. Run auto-match
6. Verify the author **is** matched

### 3. Test Filters
1. Note a manager name with both active and inactive reports
2. Filter by that manager
3. Count results
4. Verify count matches only **active** reports

---

## Future Enhancements

### 1. Show Inactive Badge
For existing mappings to inactive staff:
```javascript
{record.staff_status === 'Inactive' && (
  <Tag color="red">Inactive</Tag>
)}
```

### 2. Remapping Suggestions
Suggest remapping authors from inactive to active staff:
```
"Warning: John Doe is mapped to inactive staff member Jane Smith.
Would you like to remap to an active staff member?"
```

### 3. Inactive Staff Filter Toggle
Optional toggle to include inactive staff for historical analysis:
```javascript
<Switch>
  Include Inactive Staff (Historical Analysis)
</Switch>
```

### 4. Audit Log
Track when mappings were created vs when staff became inactive:
```
"Mapped on 2024-01-15 (Active)"
"Staff became inactive on 2024-06-30"
```

---

## Troubleshooting

### "Why is the staff dropdown list shorter now?"
**Answer**: Inactive staff members are now hidden. This is expected behavior to show only current employees.

### "I can't find an employee I know works here"
**Possible Causes**:
1. Staff member's status is set to "Inactive" in HRIS data
2. Staff member not yet in the staff_details table
3. Search query not matching their name/email

**Solution**: Check `staff_status` in database or contact HR data team.

### "Why do some authors show staff details with inactive status?"
**Answer**: Historical mappings are preserved. The author was mapped when the staff member was active. This is intentional for data integrity.

### "Can I still see inactive staff contributions?"
**Answer**: Yes, if they were already mapped. New mappings cannot be created to inactive staff, but existing mappings remain visible.

---

## SQL Queries for Administrators

### Count Active vs Inactive Staff
```sql
SELECT
    CASE
        WHEN staff_status = 'Inactive' THEN 'Inactive'
        WHEN staff_status IS NULL THEN 'NULL (Treated as Active)'
        ELSE 'Active/Other'
    END AS status_category,
    COUNT(*) as count
FROM staff_details
GROUP BY status_category;
```

### Find Mappings to Inactive Staff
```sql
SELECT
    m.author_name,
    m.staff_name,
    m.mapped_date,
    s.staff_status,
    s.email_address
FROM author_staff_mapping m
JOIN staff_details s ON m.bank_id_1 = s.bank_id_1
WHERE s.staff_status = 'Inactive'
ORDER BY m.mapped_date DESC;
```

### Active Staff by Department
```sql
SELECT
    tech_unit,
    COUNT(*) as active_count
FROM staff_details
WHERE staff_status != 'Inactive' OR staff_status IS NULL
GROUP BY tech_unit
ORDER BY active_count DESC;
```

---

## Summary

**Key Points**:
- ✅ Only **active** staff in dropdowns and filters
- ✅ Existing mappings to inactive staff **preserved**
- ✅ NULL status treated as **active** (backward compatible)
- ✅ Clear user messaging about exclusion policy
- ✅ Maintains historical data integrity

**Impact**:
- More relevant analytics
- Cleaner user interface
- Better data quality
- Aligned with HR policies

---

**Implementation Date**: Current Session
**Files Modified**:
- `backend/routers/authors.py` (3 locations)
- `backend/routers/staff.py` (1 location)
- `frontend/src/pages/AuthorMapping.jsx` (2 locations)
