# Quick Start: Staff Integration Features

## Overview
The Authors Analytics page now shows enriched data from the HR staff details table when authors are mapped to staff members.

---

## Step 1: Map Authors to Staff

Before you can see staff details in analytics, you need to map Git authors to staff records.

### Option A: Auto-Match by Email (Fastest)

1. Navigate to **Author-Staff Mapping** in the sidebar
2. Click the **"Bulk Operations"** tab
3. Click **"Run Auto-Match"**
4. Confirm the dialog
5. Wait for automatic matching to complete

This will automatically link authors whose Git email matches their staff email.

### Option B: Manual Mapping

1. Go to **Author-Staff Mapping** → **"Create Mapping"** tab
2. Left side: Select the Git author
3. Right side: Select the corresponding staff member
4. Add optional notes
5. Click **"Create Mapping"**

---

## Step 2: View Enhanced Analytics

1. Navigate to **Authors Analytics** in the sidebar
2. You'll now see the enhanced version with:
   - Staff details columns (Bank ID, Rank, Manager, Location, Type)
   - Green "Mapped" tag for linked authors
   - Mapping rate statistic

---

## Step 3: Use Filters

### Filter by Rank
1. Click the **"Rank"** dropdown in the filters panel
2. Select a rank (e.g., "VP", "Director", "Manager")
3. View contributions only from that rank level

### Filter by Reporting Manager
1. Click the **"Reporting Manager"** dropdown
2. Search or select a manager's name
3. See all contributions from their direct reports

### Filter by Location
1. Click the **"Work Location"** dropdown
2. Select a location (e.g., "Singapore", "India")
3. View contributions by office location

### Filter by Staff Type
1. Click the **"Staff Type"** dropdown
2. Select type (e.g., "Permanent", "Contract")
3. Compare contribution patterns

### Combine Filters
You can use multiple filters together:
- Example: Singapore VPs under a specific manager
- Example: Permanent staff in India with commits this quarter

---

## Understanding the Display

### Mapped Authors
- Show a green ✅ "Mapped" tag
- Display official staff name (if different from Git username)
- Include all staff details (Bank ID, Rank, etc.)

### Unmapped Authors
- No green tag
- Show Git author name and email only
- Staff detail columns show "-"

### Mapping Rate Metric
- Green (>50%): Good mapping coverage
- Orange (≤50%): Need more mappings
- Shows: "X of Y authors mapped"

---

## Common Use Cases

### 1. Team Performance Review
**Goal**: See my team's Git contributions

**Steps**:
1. Set "Reporting Manager" filter to your name
2. Optionally set date range (e.g., last quarter)
3. View table and chart
4. Export to CSV for reporting

### 2. Location-Based Analysis
**Goal**: Compare contributions across offices

**Steps**:
1. Set "Work Location" to "Singapore"
2. Note statistics
3. Change to "India"
4. Compare the numbers

### 3. Contractor vs Permanent
**Goal**: Analyze contribution patterns by employment type

**Steps**:
1. Filter by "Permanent" staff type
2. Note commit counts and lines changed
3. Switch filter to "Contract"
4. Compare the patterns

### 4. VP Contributions
**Goal**: See all VP-level contributions

**Steps**:
1. Set "Rank" filter to "VP"
2. Sort table by commits (descending)
3. Export for executive summary

---

## Exporting Data

The CSV export includes all columns:
- Author Name
- Email
- Staff Name (if mapped)
- Bank ID
- Rank
- Reporting Manager
- Work Location
- Staff Type
- All commit statistics
- Mapping status (Yes/No)

Perfect for:
- Management reports
- Performance reviews
- Resource planning
- Team analytics

---

## Tips & Best Practices

### 1. Regular Mapping Updates
- Run auto-match monthly for new team members
- Manually map authors with non-standard emails
- Keep mappings current as staff changes

### 2. Filter Combinations
- Use multiple filters for specific insights
- Clear filters to see full picture
- Date range + filters = period-specific team view

### 3. Data Quality
- Check mapping rate regularly
- Aim for >80% mapping coverage
- Unmapped authors likely external contributors or old accounts

### 4. Performance Reviews
- Export filtered data for 1-on-1s
- Use date range for review periods (quarterly, annually)
- Compare team members within same rank/location

---

## Troubleshooting

### "No staff details showing"
- **Cause**: Authors not mapped to staff
- **Fix**: Use Author-Staff Mapping page to create mappings

### "Mapping rate is 0%"
- **Cause**: No mappings created yet
- **Fix**: Run auto-match or manually create mappings

### "Filter shows no results"
- **Cause**: Selected filters exclude all authors
- **Fix**: Click "Clear Filters" and try again

### "Staff name different from Git username"
- **This is normal**: System shows official staff name from HR data
- Git username shown as secondary text if different

---

## API Endpoints (For Developers)

### Get Statistics with Filters
```http
GET /api/authors/statistics?rank=VP&work_location=Singapore
```

### Get Filter Options
```http
GET /api/authors/filter-options
```

Returns available values for all filter dropdowns.

---

## Next Steps

1. ✅ Map authors using auto-match
2. ✅ Explore the enhanced analytics page
3. ✅ Try different filter combinations
4. ✅ Export filtered data
5. ✅ Share insights with team

---

**Questions?** Check the full documentation in `STAFF_INTEGRATION_SUMMARY.md`
