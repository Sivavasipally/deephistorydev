# Authors Analytics View - User Guide

## Overview

The **Authors Analytics** view provides comprehensive statistics for all contributors across your analyzed repositories. This view aggregates data from commits, pull requests, and code reviews to give you a complete picture of each author's contributions.

## Accessing the View

1. Launch the dashboard: `streamlit run dashboard.py`
2. In the sidebar, select **"Authors Analytics"**

## Features

### 1. Summary Metrics

At the top of the page, you'll see four key metrics:

- **Total Authors**: Number of unique contributors
- **Total Commits**: Sum of all commits by all authors
- **Total Lines Changed**: Combined lines added and deleted
- **Total PRs**: Sum of PRs created and approved

### 2. Top Contributors Charts

#### Top 10 Contributors by Commits
- Bar chart showing authors with the most commits
- Color-coded by commit count
- Helps identify most active contributors

#### Top 10 Contributors by Lines Changed
- Grouped bar chart showing lines added vs deleted
- Green bars = Lines Added
- Red bars = Lines Deleted
- Identifies who makes the biggest code changes

### 3. Detailed Author Statistics Table

Comprehensive table showing all authors with the following columns:

| Column | Description |
|--------|-------------|
| **Author Name** | Contributor's name |
| **Email** | Contributor's email address |
| **Total Commits** | Number of commits made |
| **Lines Added** | Total lines of code added |
| **Lines Deleted** | Total lines of code deleted |
| **Total Lines Changed** | Sum of lines added and deleted |
| **Files Changed** | Number of files modified |
| **Repositories** | Number of repositories contributed to |
| **PRs Created** | Number of pull requests created |
| **PRs Approved** | Number of pull requests reviewed/approved |

#### Sorting Options

You can sort the table by any column:
- Select sorting column from dropdown
- Choose ascending or descending order
- Table updates automatically

### 4. Key Insights

Three important metrics at the bottom:

1. **Most Active Author**: Author with the most commits
2. **Most Lines Changed**: Author with the highest line count
3. **Top PR Reviewer**: Author who approved the most PRs

### 5. Data Export

Click **"Download Author Statistics as CSV"** to export the complete table with all statistics for further analysis in Excel, Google Sheets, etc.

## Use Cases

### Team Performance Analysis
Track individual and team productivity:
- Identify top contributors
- Recognize active reviewers
- Understand code ownership

### Resource Planning
Make informed decisions:
- See who contributes to which repositories
- Identify knowledge concentration
- Plan for bus factor mitigation

### Code Review Distribution
Ensure healthy review practices:
- Check if reviews are distributed evenly
- Identify potential review bottlenecks
- Balance workload across team

### Contribution Patterns
Understand development patterns:
- Compare commit frequency vs code volume
- Identify specialists (many commits, fewer lines) vs batch contributors
- Track cross-repository contributors

## Interpreting the Data

### High Commits, Low Lines Changed
- Frequent small improvements
- Bug fixes and maintenance
- Good incremental development practice

### Low Commits, High Lines Changed
- Large feature implementations
- Batch commits (less ideal)
- Possible refactoring work

### High PRs Approved
- Active code reviewer
- Important for code quality
- Knowledge sharing contributor

### Multi-Repository Contributors
- Cross-team collaboration
- Broad codebase knowledge
- Integration work

## Example Scenarios

### Scenario 1: New Team Member Onboarding
**Question**: Is the new developer ramping up?

**Analysis**:
1. Navigate to Authors Analytics
2. Sort by "Total Commits"
3. Find the new team member
4. Check:
   - Are commits increasing over time?
   - Which repositories are they contributing to?
   - Are they creating PRs?

### Scenario 2: Code Review Distribution
**Question**: Are code reviews distributed fairly?

**Analysis**:
1. Sort by "PRs Approved"
2. Check if top reviewers are overloaded
3. Identify team members who could review more
4. Balance review assignments

### Scenario 3: Technical Debt Assessment
**Question**: Who should be involved in refactoring discussions?

**Analysis**:
1. Sort by "Total Lines Changed"
2. Identify authors with deep code involvement
3. Cross-reference with "Repositories" column
4. Invite high-impact contributors to planning

### Scenario 4: Recognition and Rewards
**Question**: Who should be recognized this quarter?

**Analysis**:
1. Review all metrics:
   - Top commits (productivity)
   - Top lines changed (impact)
   - Top PR approvals (collaboration)
2. Export data for stakeholder review
3. Use for performance reviews or team recognition

## Tips and Best Practices

### 1. Regular Monitoring
- Review weekly or monthly
- Track trends over time
- Compare periods

### 2. Context Matters
- High commits ≠ always better
- Quality > quantity
- Consider repository size and complexity

### 3. Combine with Other Views
- Use with "Detailed Commits View" for specifics
- Cross-reference with "Detailed PRs View"
- Check individual commit quality

### 4. Account for Different Roles
- Senior developers: More reviews, strategic commits
- Junior developers: More frequent commits, learning
- Tech leads: Cross-repository work

### 5. Time Period Considerations
- Recent hires will have lower numbers
- Part-time contributors have different patterns
- Consider vacation and leave periods

## Data Accuracy Notes

### Commit Data
- ✅ Accurate: Based on Git history
- ✅ Complete: All branches analyzed (master/main)
- ⚠️ Email-based: Same person with different emails counted separately

### PR Data
- ⚠️ Limited: Only from merge commits
- ⚠️ Basic: For full PR data, integrate with Git platform API
- ✅ Historical: Shows merged PRs

### Approval Data
- ⚠️ Limited: Extracted from commit messages
- ⚠️ Incomplete: Not all PRs have approval data
- 💡 Tip: Integrate GitHub/GitLab API for complete data

## Troubleshooting

### "No author data available"
**Cause**: No commits in database
**Solution**: Run CLI tool first: `python cli.py your_repos.csv`

### Same person appears multiple times
**Cause**: Different email addresses used
**Solution**: Manual consolidation needed or Git email configuration

### PR counts seem low
**Cause**: PR data extracted from merge commits only
**Solution**: This is expected. For complete PR data, use Git platform APIs

### Charts not showing
**Cause**: Insufficient data or browser issue
**Solution**:
- Ensure multiple repositories processed
- Try different browser
- Check console for errors

## Export and Reporting

### CSV Export Format
The exported CSV includes all columns and can be used for:
- Excel pivot tables
- Quarterly reports
- Performance reviews
- Time series analysis (export periodically)

### Recommended Export Schedule
- **Weekly**: For active projects
- **Monthly**: For regular reporting
- **Quarterly**: For reviews and planning

### Sample Report Structure
```
Author Analytics Report - Q1 2024

Top Contributors:
1. Author A: 150 commits, 5,000 lines changed
2. Author B: 120 commits, 3,500 lines changed
3. Author C: 100 commits, 4,200 lines changed

Top Reviewers:
1. Author D: 45 PRs approved
2. Author E: 38 PRs approved
3. Author A: 35 PRs approved

Key Insights:
- Team productivity increased 15% over last quarter
- Code review distribution improved
- 3 new contributors onboarded successfully
```

## Related Documentation

- [README.md](README.md) - Complete application documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [PERFORMANCE_TIPS.md](PERFORMANCE_TIPS.md) - Performance optimization

## Feedback and Enhancement

This view provides comprehensive author analytics based on Git history. For additional metrics or custom reports, the data can be queried directly from the database using the SQLAlchemy models.

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for information on extending the dashboard with custom queries.
