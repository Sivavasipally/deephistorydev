# Database Schema Documentation

## Overview

The Git History Deep Analyzer uses a relational database to store and analyze developer productivity metrics by combining Git repository data with HR organizational information. The schema is designed to support comprehensive productivity analytics, code quality metrics, and organizational insights.

## Database Support

- **Development**: SQLite (file-based, zero configuration)
- **Production**: MariaDB/MySQL (scalable, concurrent access)

## Entity Relationship Diagram

```
┌─────────────────┐
│  Repository     │
│  (repositories) │
└────────┬────────┘
         │ 1
         │
         │ N
    ┌────┴────────────────────────┐
    │                             │
┌───▼──────────┐         ┌────────▼─────────┐
│  Commit      │         │  PullRequest     │
│  (commits)   │         │  (pull_requests) │
└──────────────┘         └────────┬─────────┘
                                  │ 1
                                  │
                                  │ N
                         ┌────────▼─────────┐
                         │  PRApproval      │
                         │  (pr_approvals)  │
                         └──────────────────┘

┌──────────────────────┐         ┌──────────────────────────┐
│  StaffDetails        │◄────────┤  AuthorStaffMapping      │
│  (staff_details)     │         │  (author_staff_mapping)  │
└──────────────────────┘         └──────────────────────────┘
         ▲                                    ▲
         │                                    │
         └────────────────┬───────────────────┘
                          │
                    Links Git Authors
                    to HR Employees
```

---

## Tables

### 1. repositories

**Purpose**: Stores information about Git repositories being analyzed for productivity metrics.

**Description**: Each repository represents a unique project tracked in the version control system. This is the parent table for all commit and pull request activity.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Unique identifier for the repository (Primary Key) |
| `project_key` | VARCHAR(255) | NO | Project key or identifier from the version control system (e.g., Bitbucket project key) |
| `slug_name` | VARCHAR(255) | NO | Repository slug name - the unique identifier within a project |
| `clone_url` | VARCHAR(500) | NO | Git clone URL used to fetch repository data |
| `created_at` | DATETIME | YES | Timestamp when this repository was first added to the system |

**Relationships**:
- One-to-Many with `commits` table
- One-to-Many with `pull_requests` table

---

### 2. commits

**Purpose**: Individual Git commits with metadata for productivity analysis and code contribution tracking.

**Description**: Each commit represents a single code contribution to a repository. This is the primary source of developer productivity metrics including lines of code, commit frequency, and file changes.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Unique identifier for the commit record (Primary Key) |
| `repository_id` | INTEGER | NO | Foreign key linking to the repository this commit belongs to |
| `commit_hash` | VARCHAR(40) | NO | Git commit SHA-1 hash - unique identifier for the commit in Git (Unique) |
| `author_name` | VARCHAR(255) | YES | Name of the developer who authored the code changes |
| `author_email` | VARCHAR(255) | YES | Email address of the commit author |
| `committer_name` | VARCHAR(255) | YES | Name of the person who committed the code (may differ from author) |
| `committer_email` | VARCHAR(255) | YES | Email address of the committer |
| `commit_date` | DATETIME | YES | Timestamp when the commit was created |
| `message` | TEXT | YES | Commit message describing the changes made |
| `lines_added` | INTEGER | YES | Number of lines of code added in this commit (Default: 0) |
| `lines_deleted` | INTEGER | YES | Number of lines of code deleted in this commit (Default: 0) |
| `files_changed` | INTEGER | YES | Number of files modified in this commit (Default: 0) |
| `branch` | VARCHAR(255) | YES | Git branch where this commit was made (Default: 'master') |

**Relationships**:
- Many-to-One with `repositories` table (via `repository_id`)

**Indexes**:
- Primary Key on `id`
- Unique index on `commit_hash`
- Foreign Key index on `repository_id`

---

### 3. pull_requests

**Purpose**: Pull requests for code review tracking, collaboration metrics, and merge success analysis.

**Description**: Represents proposed code changes submitted for review before merging. Critical for measuring code quality, collaboration, and review processes.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Unique identifier for the pull request record (Primary Key) |
| `repository_id` | INTEGER | NO | Foreign key linking to the repository this PR belongs to |
| `pr_number` | INTEGER | YES | Pull request number within the repository |
| `title` | VARCHAR(500) | YES | Title or summary of the pull request |
| `description` | TEXT | YES | Detailed description of changes proposed in the PR |
| `author_name` | VARCHAR(255) | YES | Name of the developer who created the pull request |
| `author_email` | VARCHAR(255) | YES | Email address of the PR author |
| `created_date` | DATETIME | YES | Timestamp when the PR was created |
| `merged_date` | DATETIME | YES | Timestamp when the PR was merged (null if not merged) |
| `state` | VARCHAR(50) | YES | Current state of the PR: open, closed, or merged |
| `source_branch` | VARCHAR(255) | YES | Git branch containing the proposed changes |
| `target_branch` | VARCHAR(255) | YES | Git branch where changes will be merged (typically main/master) |
| `lines_added` | INTEGER | YES | Total number of lines added across all commits in this PR (Default: 0) |
| `lines_deleted` | INTEGER | YES | Total number of lines deleted across all commits in this PR (Default: 0) |
| `commits_count` | INTEGER | YES | Number of commits included in this pull request (Default: 0) |

**Relationships**:
- Many-to-One with `repositories` table (via `repository_id`)
- One-to-Many with `pr_approvals` table

**State Values**:
- `open`: PR is currently open and awaiting review/merge
- `closed`: PR was closed without merging
- `merged`: PR was successfully merged into target branch

---

### 4. pr_approvals

**Purpose**: Tracks who approved pull requests and when - used for code review metrics and quality analysis.

**Description**: Each approval represents a reviewer's sign-off on proposed code changes. Used for measuring code review participation and quality assurance processes.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Unique identifier for the approval record (Primary Key) |
| `pull_request_id` | INTEGER | NO | Foreign key linking to the pull request that was approved |
| `approver_name` | VARCHAR(255) | YES | Name of the reviewer who approved the pull request |
| `approver_email` | VARCHAR(255) | YES | Email address of the approver |
| `approval_date` | DATETIME | YES | Timestamp when the approval was given |

**Relationships**:
- Many-to-One with `pull_requests` table (via `pull_request_id`)

---

### 5. staff_details

**Purpose**: HR master data for staff members including organizational structure, employment details, and demographic information.

**Description**: Comprehensive staff/employee information from HR systems. Contains organizational structure, employment details, and metadata for all staff members. Used to link Git activity to actual employees and analyze productivity by organizational attributes.

#### Primary Identification

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Unique auto-increment identifier for the record (Primary Key) |
| `bank_id_1` | VARCHAR(50) | YES | Primary bank/organization identifier - **KEY FOR LINKING TO GIT AUTHORS** |
| `staff_id` | VARCHAR(50) | YES | Employee ID or staff number from HR system |
| `email_address` | VARCHAR(255) | YES | Official work email address of the staff member |

#### Personal Information

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `staff_first_name` | VARCHAR(255) | YES | First name of the staff member |
| `staff_last_name` | VARCHAR(255) | YES | Last name/surname of the staff member |
| `staff_name` | VARCHAR(255) | YES | Full name (typically first name + last name) |
| `citizenship` | VARCHAR(100) | YES | Citizenship or nationality |
| `gender` | VARCHAR(20) | YES | Gender of the staff member |

#### Employment Status and Dates

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `staff_status` | VARCHAR(100) | YES | Current employment status (e.g., Active, Inactive, On Leave) |
| `sub_status` | VARCHAR(100) | YES | Detailed sub-status within the main employment status |
| `movement_status` | VARCHAR(100) | YES | Status related to organizational movements (e.g., Transfer, Promotion) |
| `staff_start_date` | DATE | YES | Date when employment started |
| `staff_end_date` | DATE | YES | Date when employment ended (null if currently active) |
| `last_work_day` | DATE | YES | Last working day for the staff member |
| `movement_date` | DATE | YES | Date of last organizational movement or status change |

#### Staff Type and Classification

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `original_staff_type` | VARCHAR(100) | YES | Original classification before any changes |
| `staff_type` | VARCHAR(100) | YES | Current type (e.g., Permanent, Contract, Temporary, Consultant) |
| `rank` | VARCHAR(100) | YES | Job rank or grade level within the organization |
| `staff_level` | VARCHAR(100) | YES | Hierarchical level |
| `hr_role` | VARCHAR(255) | YES | Role designation from HR perspective |
| `job_function` | VARCHAR(255) | YES | Primary job function or responsibility area |
| `default_role` | VARCHAR(255) | YES | Default role assignment |
| `skill_set_type` | VARCHAR(255) | YES | Type or category of skills possessed |

#### Organizational Structure

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `tech_unit` | VARCHAR(255) | YES | Technology unit or tech division |
| `division` | VARCHAR(255) | YES | Corporate division or business unit |
| `department_id` | VARCHAR(50) | YES | Department identifier code |
| `platform_index` | VARCHAR(50) | YES | Index or code for the platform/product |
| `platform_name` | VARCHAR(255) | YES | Name of the platform or product |
| `platform_unit` | VARCHAR(255) | YES | Unit within the platform organization |
| `platform_lead` | VARCHAR(255) | YES | Name of the platform lead or manager |
| `sub_platform` | VARCHAR(255) | YES | Sub-platform or component |
| `staff_grouping` | VARCHAR(100) | YES | Grouping classification (e.g., by skill, project, team) |

#### Reporting Structure

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `reporting_manager_1bank_id` | VARCHAR(50) | YES | Bank ID of the direct reporting manager |
| `reporting_manager_staff_id` | VARCHAR(50) | YES | Staff ID of the direct reporting manager |
| `reporting_manager_name` | VARCHAR(255) | YES | Full name of the direct reporting manager |
| `reporting_manager_pc_code` | VARCHAR(50) | YES | Profit center code of the reporting manager |

#### Work Location and Type

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `work_location` | VARCHAR(255) | YES | Primary work location or office (e.g., Singapore, New York, Remote) |
| `reporting_location` | VARCHAR(255) | YES | Official reporting location for HR purposes |
| `primary_seating` | VARCHAR(255) | YES | Primary seating location or desk assignment |
| `work_type1` | VARCHAR(100) | YES | Primary work type classification |
| `work_type2` | VARCHAR(100) | YES | Secondary work type classification |

#### Company and Legal Entity

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `company_name` | VARCHAR(255) | YES | Full legal name of the employing company |
| `company_short_name` | VARCHAR(100) | YES | Abbreviated company name |

#### Financial and Billing

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `staff_pc_code` | VARCHAR(50) | YES | Profit center code for the staff member |
| `billing_pc_code` | VARCHAR(50) | YES | Profit center code used for billing |
| `people_cost_type` | VARCHAR(100) | YES | Type of cost classification for people costs |
| `fte` | FLOAT | YES | Full-Time Equivalent (1.0 = full-time, 0.5 = half-time) |
| `hc_included` | VARCHAR(20) | YES | Flag indicating if headcount is included in official counts (Yes/No) |
| `reason_for_hc_included_no` | VARCHAR(255) | YES | Explanation if headcount is not included |

#### Contract Information

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `contract_start_date` | DATE | YES | Start date of current employment contract |
| `contract_end_date` | DATE | YES | End date of current employment contract |
| `original_tenure_start_date` | DATE | YES | Original start date of tenure |
| `po_number` | VARCHAR(100) | YES | Purchase Order number for contract staff |
| `mcr_number` | VARCHAR(100) | YES | MCR (Managed Contractor Resource) number |
| `assignment_id` | VARCHAR(100) | YES | Assignment identifier for contract/project-based staff |

#### Data Management

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `as_of_date` | DATE | YES | Snapshot date - the date this record represents (for historical tracking) |
| `reporting_period` | VARCHAR(50) | YES | Reporting period (e.g., 2024-Q1, January-2024) |
| `effective_date` | DATE | YES | Date when this record becomes effective |
| `effective_billing_date` | DATE | YES | Date when billing information becomes effective |
| `created_by` | VARCHAR(255) | YES | Username or system that created this record |
| `date_created` | DATETIME | YES | Timestamp when record was created in database |
| `modified_by` | VARCHAR(255) | YES | Username or system that last modified this record |
| `date_modified` | DATETIME | YES | Timestamp when record was last modified |

**Relationships**:
- One-to-Many with `author_staff_mapping` table (via `bank_id_1`)

---

### 6. author_staff_mapping

**Purpose**: Maps Git commit author names/emails to staff members - enables linking code contributions to employees.

**Description**: This is the critical bridge that connects version control activity to HR employee data. Enables attribution of code contributions to specific employees for productivity analytics.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Unique identifier for the mapping record (Primary Key) |
| `author_name` | VARCHAR(255) | NO | Git author name as it appears in commits (e.g., "John Doe") - **UNIQUE** |
| `author_email` | VARCHAR(255) | YES | Git author email address as it appears in commits |
| `bank_id_1` | VARCHAR(50) | YES | Bank ID from staff_details table - links to the employee |
| `staff_id` | VARCHAR(50) | YES | Employee ID from staff_details table |
| `staff_name` | VARCHAR(255) | YES | Official staff name from HR system (may differ from Git author name) |
| `mapped_date` | DATETIME | YES | Timestamp when this mapping was created |
| `notes` | TEXT | YES | Additional notes about the mapping (e.g., why multiple Git names map to one person) |

**Relationships**:
- Many-to-One with `staff_details` table (via `bank_id_1`)

**Important Notes**:
- `author_name` is unique - one Git author name can only map to one employee
- Multiple Git author names can map to the same employee (via `bank_id_1`)
- This handles cases where developers commit under different names/machines

**Indexes**:
- Primary Key on `id`
- Unique index on `author_name`

---

## Common Query Patterns

### 1. Get all commits by a staff member

```sql
SELECT c.*
FROM commits c
JOIN author_staff_mapping asm ON c.author_name = asm.author_name
WHERE asm.bank_id_1 = 'BANK123'
ORDER BY c.commit_date DESC;
```

### 2. Calculate productivity metrics for a team

```sql
SELECT
    sd.staff_name,
    sd.rank,
    sd.work_location,
    COUNT(DISTINCT c.id) as total_commits,
    SUM(c.lines_added) as total_lines_added,
    SUM(c.lines_deleted) as total_lines_deleted,
    COUNT(DISTINCT c.repository_id) as repos_touched
FROM staff_details sd
JOIN author_staff_mapping asm ON sd.bank_id_1 = asm.bank_id_1
JOIN commits c ON asm.author_name = c.author_name
WHERE sd.platform_name = 'Mobile Banking'
  AND c.commit_date >= '2024-01-01'
GROUP BY sd.bank_id_1, sd.staff_name, sd.rank, sd.work_location
ORDER BY total_commits DESC;
```

### 3. Get pull request review metrics

```sql
SELECT
    pr.author_name,
    COUNT(DISTINCT pr.id) as total_prs,
    COUNT(DISTINCT CASE WHEN pr.state = 'MERGED' THEN pr.id END) as merged_prs,
    AVG(TIMESTAMPDIFF(HOUR, pr.created_date, pr.merged_date)) as avg_merge_hours,
    COUNT(DISTINCT pa.approver_name) as unique_reviewers
FROM pull_requests pr
LEFT JOIN pr_approvals pa ON pr.id = pa.pull_request_id
WHERE pr.created_date >= '2024-01-01'
GROUP BY pr.author_name;
```

### 4. Find unmapped Git authors

```sql
SELECT DISTINCT c.author_name, c.author_email
FROM commits c
LEFT JOIN author_staff_mapping asm ON c.author_name = asm.author_name
WHERE asm.id IS NULL
ORDER BY c.author_name;
```

---

## Data Flow

1. **Data Ingestion**:
   - Repositories are added via `repositories` table
   - Git commits are fetched and stored in `commits` table
   - Pull requests and approvals are stored in `pull_requests` and `pr_approvals`
   - HR data is imported into `staff_details` table

2. **Author Mapping**:
   - Git author names from commits are identified
   - Manual or semi-automated mapping creates records in `author_staff_mapping`
   - This links Git activity to employee records

3. **Analytics**:
   - Productivity queries join commits → author_staff_mapping → staff_details
   - Organizational slicing uses staff_details fields (rank, location, platform, etc.)
   - Time-series analysis uses commit_date, created_date, merged_date

---

## Maintenance Notes

### Schema Migrations
- Use Alembic or similar tool for schema changes in production
- Never manually ALTER tables in production
- Test migrations in development environment first

### Performance Considerations
- Index on `commits.author_name` for faster joins
- Index on `commits.commit_date` for time-based queries
- Index on `staff_details.bank_id_1` for staff lookups
- Consider partitioning `commits` table by date for very large datasets

### Data Retention
- Commit data grows linearly with development activity
- Consider archiving old commits (> 2 years) if database size becomes an issue
- Maintain staff_details historical snapshots using `as_of_date` field

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial schema with full table and column descriptions |
