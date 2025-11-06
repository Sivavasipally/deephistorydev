# AI-Powered SQL Query Generator Guide

## Overview

The SQL Executor now includes an AI-powered query generator that converts natural language descriptions into SQL queries using the Dify AI API. Simply describe what data you want in plain English, and the AI will generate the appropriate SQL query for your database schema.

## Features

### 🤖 Natural Language to SQL
- **Input**: Describe your data requirements in plain English
- **Output**: Professionally crafted SQL query
- **Integration**: Seamlessly integrates with SQL Executor

### 📊 Schema-Aware Generation
- AI understands all 6 database tables
- Knows table relationships and foreign keys
- Generates proper JOINs when needed
- Handles date filtering and aggregations

### ✅ User-Friendly Workflow
1. Describe what data you want
2. Click "Generate SQL"
3. Review the generated query
4. Click "Use This Query" to load it
5. Execute the query

## How to Use

### Step 1: Navigate to SQL Executor

```
Dashboard → SQL Executor → AI-Powered Query Generator section
```

### Step 2: Describe Your Data Need

In the text area, describe what data you want in plain English.

**Example Prompts**:

```
"Get all staff who have committed code in the last 6 months"

"Show me the top 10 developers by number of commits"

"Find all pull requests that were approved by more than 3 people"

"List commits grouped by month with total lines added"

"Get staff members from the platform team with their commit counts"

"Show repositories with the most pull requests"
```

### Step 3: Generate SQL

Click the **🚀 Generate SQL** button. The system will:
1. Send your description to the AI API
2. Include complete database schema
3. Receive generated SQL query
4. Display the query with syntax highlighting

### Step 4: Review Generated Query

The AI-generated SQL appears below in a code block:
- ✅ Review for correctness
- ✅ Check table names and columns
- ✅ Verify JOINs and conditions
- ✅ Understand what data will be returned

### Step 5: Use or Modify

**Option A: Use Directly**
- Click **✅ Use This Query**
- Query loads into SQL Query text area
- Click **▶ Execute Query** to run it

**Option B: Modify First**
- Copy the generated SQL
- Paste into SQL Query text area
- Make manual adjustments
- Execute the modified query

**Option C: Start Over**
- Click **🗑️ Clear** to remove generated query
- Enter a new description
- Generate again

## Example Workflows

### Example 1: Simple Query

**Prompt**: "Get all repositories"

**Generated SQL**:
```sql
SELECT * FROM repositories;
```

**Steps**:
1. Enter prompt
2. Click "Generate SQL"
3. Review query
4. Click "Use This Query"
5. Execute

### Example 2: Complex Join Query

**Prompt**: "Show staff members with their total commits and lines of code changed"

**Generated SQL**:
```sql
SELECT
    sd.staff_name,
    sd.email_address,
    COUNT(c.id) as total_commits,
    SUM(c.lines_added + c.lines_deleted) as total_lines_changed
FROM staff_details sd
JOIN author_staff_mapping asm ON sd.bank_id_1 = asm.bank_id_1
JOIN commits c ON asm.author_name = c.author_name
GROUP BY sd.staff_id, sd.staff_name, sd.email_address
ORDER BY total_commits DESC;
```

**Steps**:
1. Enter prompt describing the complex join
2. Generate SQL
3. Review the generated JOINs
4. Use query
5. Execute and analyze results

### Example 3: Date Filtering

**Prompt**: "Get commits from the last month"

**Generated SQL**:
```sql
SELECT
    commit_hash,
    author_name,
    commit_date,
    message,
    lines_added,
    lines_deleted
FROM commits
WHERE commit_date >= date('now', '-1 month')
ORDER BY commit_date DESC;
```

**Steps**:
1. Enter prompt with time reference
2. Generate SQL
3. Verify date logic
4. Execute

### Example 4: Aggregation Query

**Prompt**: "Show pull requests grouped by author with approval counts"

**Generated SQL**:
```sql
SELECT
    pr.author_name,
    COUNT(DISTINCT pr.id) as total_prs,
    AVG(approval_count) as avg_approvals
FROM pull_requests pr
LEFT JOIN (
    SELECT pull_request_id, COUNT(*) as approval_count
    FROM pr_approvals
    GROUP BY pull_request_id
) pa ON pr.id = pa.pull_request_id
GROUP BY pr.author_name
ORDER BY total_prs DESC;
```

**Steps**:
1. Enter aggregation request
2. Generate complex query with subquery
3. Review logic
4. Execute

## Database Schema Reference

The AI has knowledge of all 6 tables:

### repositories
- id, project_key, slug_name, clone_url, created_at

### commits
- id, repository_id, commit_hash, author_name, author_email
- committer_name, committer_email, commit_date, message
- lines_added, lines_deleted, files_changed, branch

### pull_requests
- id, repository_id, pr_number, title, description
- author_name, author_email, created_date, merged_date
- state, source_branch, target_branch
- lines_added, lines_deleted, commits_count

### pr_approvals
- id, pull_request_id, approver_name, approver_email, approval_date

### staff_details
- id, bank_id_1, staff_id, staff_name, email_address
- staff_start_date, staff_end_date, tech_unit, platform_name
- staff_type, staff_status, rank, department_id
- ... (71 fields total)

### author_staff_mapping
- id, author_name, author_email
- bank_id_1, staff_id, staff_name
- mapped_date, notes

## Advanced Usage

### Multi-Table Queries

**Prompt**: "Get all commits with repository information and author staff details"

The AI will automatically generate appropriate JOINs:
```sql
SELECT
    r.project_key,
    r.slug_name,
    c.commit_hash,
    c.author_name,
    sd.staff_name,
    sd.tech_unit,
    c.lines_added,
    c.lines_deleted
FROM commits c
JOIN repositories r ON c.repository_id = r.id
LEFT JOIN author_staff_mapping asm ON c.author_name = asm.author_name
LEFT JOIN staff_details sd ON asm.bank_id_1 = sd.bank_id_1;
```

### Analytical Queries

**Prompt**: "Show monthly commit trends for the last year"

AI generates time-series query:
```sql
SELECT
    strftime('%Y-%m', commit_date) as month,
    COUNT(*) as commits,
    SUM(lines_added) as added,
    SUM(lines_deleted) as deleted
FROM commits
WHERE commit_date >= date('now', '-1 year')
GROUP BY month
ORDER BY month;
```

### Department Analysis

**Prompt**: "Compare commits across different tech units"

AI generates grouped analysis:
```sql
SELECT
    sd.tech_unit,
    COUNT(DISTINCT asm.author_name) as developers,
    COUNT(c.id) as total_commits,
    AVG(c.lines_added + c.lines_deleted) as avg_lines_per_commit
FROM staff_details sd
JOIN author_staff_mapping asm ON sd.bank_id_1 = asm.bank_id_1
JOIN commits c ON asm.author_name = c.author_name
GROUP BY sd.tech_unit
ORDER BY total_commits DESC;
```

## Best Practices

### 1. Be Specific

**Instead of**: "Get commits"
**Better**: "Get commits from the last month with author names and lines changed"

### 2. Specify Sorting

**Include**: "order by commit count descending"
**Result**: AI adds `ORDER BY commit_count DESC`

### 3. Limit Results

**Include**: "limit to top 10"
**Result**: AI adds `LIMIT 10`

### 4. Mention Relationships

**Include**: "with repository information"
**Result**: AI includes appropriate JOIN

### 5. Define Time Ranges

**Be specific**: "from January 2024 to March 2024"
**Or relative**: "in the last 3 months"

### 6. Request Aggregations

**Examples**:
- "count of commits by author"
- "sum of lines added per month"
- "average approvals per PR"

## Prompt Examples

### Simple Queries

```
"List all repositories"
"Show me staff details"
"Get recent commits"
"Display pull requests"
```

### Filtered Queries

```
"Get commits by author 'John Doe'"
"Show PRs in merged state"
"Find staff from platform team"
"List commits after 2024-01-01"
```

### Aggregation Queries

```
"Count commits per author"
"Sum lines changed by repository"
"Average approvals per pull request"
"Total commits by month"
```

### Join Queries

```
"Get commits with repository names"
"Show authors with their staff details"
"List PRs with approval counts"
"Display commits by staff tech unit"
```

### Analytical Queries

```
"Top 10 contributors by commits"
"Most active months for commits"
"Repositories with most pull requests"
"Staff members who haven't committed recently"
```

## Troubleshooting

### API Timeout

**Issue**: "Request timeout. Please try again."
**Solution**:
- Click "Generate SQL" again
- Simplify your prompt
- Check network connectivity

### API Error

**Issue**: "API Error: 401" or "API Error: 500"
**Solution**:
- Contact system administrator
- API credentials may need refresh
- Fall back to manual SQL or sample queries

### Incorrect Query

**Issue**: Generated SQL doesn't match intent
**Solution**:
- Rephrase your prompt more clearly
- Be more specific about tables and fields
- Manually modify the generated query
- Use sample queries as reference

### Empty Result

**Issue**: "answer" field empty in API response
**Solution**:
- Prompt may be unclear
- Try different wording
- Start with simpler query
- Check example prompts for guidance

## Security & Privacy

### Data Protection
- Prompts are sent to internal Dify API only
- No data leaves the corporate network
- Only schema is shared, not actual data
- Queries reviewed before execution

### Safe Execution
- AI generates SELECT queries by default
- Destructive operations (DELETE, UPDATE) flagged
- Review all generated queries before execution
- Use standard SQL Executor safety features

## Integration with Manual SQL

### Workflow

1. **Start with AI**: Generate initial query
2. **Review**: Check generated SQL
3. **Refine**: Manually adjust if needed
4. **Execute**: Run the query
5. **Save**: Use as sample for future

### Best of Both Worlds

- **AI**: Quick start, complex joins, syntax help
- **Manual**: Fine-tuning, edge cases, optimization
- **Combined**: Efficient workflow for all skill levels

## FAQ

**Q: Can AI generate UPDATE or DELETE queries?**
A: Yes, but they're flagged with warnings. Review carefully before execution.

**Q: What if the generated query is wrong?**
A: Manually edit it in the SQL Query text area before executing.

**Q: Can I save generated queries?**
A: Copy to clipboard and save externally, or execute and download results.

**Q: Does AI understand my specific data?**
A: AI knows the schema but not your data. It generates queries based on table structure.

**Q: How complex can my prompt be?**
A: Very complex! Try multi-table joins, subqueries, aggregations, etc.

**Q: Can I use it for learning SQL?**
A: Absolutely! Great way to learn SQL patterns for your schema.

**Q: What happens if API is down?**
A: Fall back to manual SQL input or sample queries.

**Q: Is there a query history?**
A: Not currently. Copy queries you want to reuse.

## Summary

The AI-Powered SQL Query Generator provides:
- ✅ Natural language to SQL conversion
- ✅ Schema-aware query generation
- ✅ Automatic JOIN handling
- ✅ Date filtering and aggregations
- ✅ Seamless integration with SQL Executor
- ✅ Review and edit workflow
- ✅ Safe execution with warnings

**Quick Start**:
```
1. Describe your data need in plain English
2. Click "Generate SQL"
3. Review the generated query
4. Click "Use This Query"
5. Execute and analyze results
```

This feature makes SQL accessible to all users while maintaining the power and flexibility of direct SQL execution!
