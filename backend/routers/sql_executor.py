"""SQL executor router with AI query generation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any
import requests
import pandas as pd

from cli.config import Config
from cli.models import get_engine

router = APIRouter()

class SQLQuery(BaseModel):
    """SQL query model."""
    query: str

class AIQueryRequest(BaseModel):
    """AI query generation request."""
    prompt: str

class AIQueryResponse(BaseModel):
    """AI query generation response."""
    generated_sql: str

@router.post("/execute", response_model=Dict[str, Any])
async def execute_sql(sql_query: SQLQuery = Body(...)):
    """Execute a SQL query and return results."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)

        # Execute query
        df = pd.read_sql_query(sql_query.query, engine)

        # Convert to JSON-serializable format
        result = df.to_dict(orient='records')

        # Convert datetime objects to ISO format
        for row in result:
            for key, value in row.items():
                if hasattr(value, 'isoformat'):
                    row[key] = value.isoformat()
                elif pd.isna(value):
                    row[key] = None

        return {
            "success": True,
            "rows": len(result),
            "columns": list(df.columns),
            "data": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "rows": 0,
            "columns": [],
            "data": []
        }

@router.post("/generate-query", response_model=AIQueryResponse)
async def generate_sql_query(request: AIQueryRequest = Body(...)):
    """Generate SQL query from natural language using AI."""
    try:
        # Enhanced schema string with detailed comments for AI context
        schema_string = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                          DATABASE SCHEMA REFERENCE                           ║
║                        DeepHistory Analytics Platform                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
📦 TABLE: repositories
Purpose: Stores all Git repositories being tracked
═══════════════════════════════════════════════════════════════════════════════
┌─ id                INTEGER PRIMARY KEY     → Unique repository identifier
├─ project_key       VARCHAR(255)           → Bitbucket project key (e.g., 'MYPROJ')
├─ slug_name         VARCHAR(255)           → Repository slug (e.g., 'my-repo')
├─ clone_url         VARCHAR(500)           → Git clone URL
└─ created_at        DATETIME               → When repository was added to system

Relationships:
  ├─→ commits (one-to-many via repository_id)
  └─→ pull_requests (one-to-many via repository_id)

Common Queries:
  • List all repositories: SELECT * FROM repositories
  • Find by project: SELECT * FROM repositories WHERE project_key = 'MYPROJ'

═══════════════════════════════════════════════════════════════════════════════
💾 TABLE: commits
Purpose: Stores all Git commits with full metadata
═══════════════════════════════════════════════════════════════════════════════
┌─ id                INTEGER PRIMARY KEY     → Unique commit record ID
├─ repository_id    INTEGER                 → FK to repositories.id
├─ commit_hash      VARCHAR(40) UNIQUE      → Git SHA-1 hash
├─ author_name      VARCHAR(255)           → Commit author display name
├─ author_email     VARCHAR(255)           → Commit author email
├─ committer_name   VARCHAR(255)           → Git committer name
├─ committer_email  VARCHAR(255)           → Git committer email
├─ commit_date      DATETIME               → When commit was created
├─ message          TEXT                   → Commit message
├─ lines_added      INTEGER                → Lines of code added
├─ lines_deleted    INTEGER                → Lines of code deleted
├─ files_changed    INTEGER                → Number of files modified
└─ branch           VARCHAR(255)           → Git branch name

Relationships:
  └─→ repositories (many-to-one via repository_id)

Join with Staff:
  commits.author_email → author_staff_mapping.author_email → staff_details.bank_id_1

Common Queries:
  • Commits by author: SELECT * FROM commits WHERE author_email = 'user@example.com'
  • Commits in date range: SELECT * FROM commits WHERE commit_date BETWEEN '2024-01-01' AND '2024-12-31'
  • Top contributors: SELECT author_name, COUNT(*) FROM commits GROUP BY author_name ORDER BY COUNT(*) DESC

═══════════════════════════════════════════════════════════════════════════════
🔀 TABLE: pull_requests
Purpose: Stores all pull requests with merge status and metadata
═══════════════════════════════════════════════════════════════════════════════
┌─ id                INTEGER PRIMARY KEY     → Unique PR record ID
├─ repository_id    INTEGER                 → FK to repositories.id
├─ pr_number        INTEGER                 → PR number within repository
├─ title            VARCHAR(500)           → PR title
├─ description      TEXT                   → PR description/body
├─ author_name      VARCHAR(255)           → PR creator name
├─ author_email     VARCHAR(255)           → PR creator email
├─ created_date     DATETIME               → When PR was created
├─ merged_date      DATETIME               → When PR was merged (NULL if not merged)
├─ state            VARCHAR(50)            → PR state: OPEN, MERGED, DECLINED
├─ source_branch    VARCHAR(255)           → Source branch name
├─ target_branch    VARCHAR(255)           → Target branch name
├─ lines_added      INTEGER                → Total lines added in PR
├─ lines_deleted    INTEGER                → Total lines deleted in PR
└─ commits_count    INTEGER                → Number of commits in PR

Relationships:
  ├─→ repositories (many-to-one via repository_id)
  └─→ pr_approvals (one-to-many via pull_request_id)

Common Queries:
  • Open PRs: SELECT * FROM pull_requests WHERE state = 'OPEN'
  • Merged PRs: SELECT * FROM pull_requests WHERE merged_date IS NOT NULL
  • PR merge rate: SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM pull_requests) FROM pull_requests WHERE state = 'MERGED'

═══════════════════════════════════════════════════════════════════════════════
✅ TABLE: pr_approvals
Purpose: Stores all PR approvals/reviews
═══════════════════════════════════════════════════════════════════════════════
┌─ id                INTEGER PRIMARY KEY     → Unique approval record ID
├─ pull_request_id  INTEGER                 → FK to pull_requests.id
├─ approver_name    VARCHAR(255)           → Approver display name
├─ approver_email   VARCHAR(255)           → Approver email
└─ approval_date    DATETIME               → When approval was given

Relationships:
  └─→ pull_requests (many-to-one via pull_request_id)

Common Queries:
  • Approvals by user: SELECT * FROM pr_approvals WHERE approver_email = 'user@example.com'
  • Top reviewers: SELECT approver_name, COUNT(*) FROM pr_approvals GROUP BY approver_name ORDER BY COUNT(*) DESC

═══════════════════════════════════════════════════════════════════════════════
👥 TABLE: staff_details
Purpose: Master table of all staff members with organizational data
═══════════════════════════════════════════════════════════════════════════════
┌─ id                    INTEGER PRIMARY KEY     → Unique staff record ID
├─ bank_id_1            VARCHAR(50)            → Primary employee ID (unique identifier)
├─ staff_id             VARCHAR(50)            → Secondary staff ID
├─ staff_name           VARCHAR(255)           → Full name (supports UTF-8/multilingual)
├─ email_address        VARCHAR(255)           → Official email address
├─ staff_start_date     DATE                   → Employment start date
├─ staff_end_date       DATE                   → Employment end date (NULL if active)
├─ tech_unit            VARCHAR(255)           → Technology unit/division
├─ platform_name        VARCHAR(255)           → Platform/product name
├─ staff_type           VARCHAR(100)           → Employee type (FTE, Contractor, etc.)
├─ staff_status         VARCHAR(100)           → Status (Active, Inactive, etc.)
├─ rank                 VARCHAR(100)           → Job rank/level
└─ department_id        VARCHAR(50)            → Department identifier

Relationships:
  └─→ author_staff_mapping (one-to-many via bank_id_1)

Common Queries:
  • Active staff: SELECT * FROM staff_details WHERE staff_status = 'Active'
  • Staff by platform: SELECT * FROM staff_details WHERE platform_name = 'Platform X'
  • Tech unit counts: SELECT tech_unit, COUNT(*) FROM staff_details GROUP BY tech_unit

═══════════════════════════════════════════════════════════════════════════════
🔗 TABLE: author_staff_mapping
Purpose: Maps Git authors (name/email) to staff members
═══════════════════════════════════════════════════════════════════════════════
┌─ id                INTEGER PRIMARY KEY     → Unique mapping record ID
├─ author_name      VARCHAR(255) UNIQUE     → Git author name (unique)
├─ author_email     VARCHAR(255)           → Git author email
├─ bank_id_1        VARCHAR(50)            → FK to staff_details.bank_id_1
├─ staff_id         VARCHAR(50)            → Staff ID (denormalized)
├─ staff_name       VARCHAR(255)           → Staff name (denormalized)
├─ mapped_date      DATETIME               → When mapping was created
└─ notes            TEXT                   → Additional mapping notes

Relationships:
  ├─→ staff_details (many-to-one via bank_id_1)
  ├─→ commits (one-to-many via author_email)
  └─→ pull_requests (one-to-many via author_email)

Purpose: Resolves Git identities to staff members for productivity tracking

Common Queries:
  • Find staff by Git author: SELECT s.* FROM staff_details s JOIN author_staff_mapping m ON s.bank_id_1 = m.bank_id_1 WHERE m.author_email = 'git@example.com'

═══════════════════════════════════════════════════════════════════════════════
⚡ TABLE: staff_metrics (PRE-CALCULATED)
Purpose: Pre-aggregated staff productivity metrics (calculated during CLI extract)
Performance: 45x faster than real-time calculations (70ms vs 3.2s)
═══════════════════════════════════════════════════════════════════════════════
┌─ id                        INTEGER PRIMARY KEY     → Unique metrics record ID
├─ bank_id_1                VARCHAR(50) UNIQUE      → FK to staff_details.bank_id_1 (indexed)
├─ staff_id                 VARCHAR(50)            → Staff ID
├─ staff_name               VARCHAR(255)           → Staff name
├─ email_address            VARCHAR(255)           → Email address
│
├─ Organizational Fields (9 fields):
│  ├─ tech_unit             VARCHAR(255)           → Technology unit
│  ├─ platform_name         VARCHAR(255)           → Platform name
│  ├─ staff_type            VARCHAR(100)           → Employee type
│  ├─ staff_status          VARCHAR(100)           → Employment status
│  ├─ work_location         VARCHAR(255)           → Work location
│  ├─ rank                  VARCHAR(100)           → Job rank
│  ├─ sub_platform          VARCHAR(255)           → Sub-platform
│  ├─ staff_grouping        VARCHAR(100)           → Staff grouping
│  └─ reporting_manager_name VARCHAR(255)          → Manager name
│
├─ Commit Metrics (6 fields):
│  ├─ total_commits         INTEGER DEFAULT 0      → Total commits by staff
│  ├─ total_lines_added     INTEGER DEFAULT 0      → Total lines of code added
│  ├─ total_lines_deleted   INTEGER DEFAULT 0      → Total lines of code deleted
│  ├─ total_files_changed   INTEGER DEFAULT 0      → Total files modified
│  ├─ total_chars_added     INTEGER DEFAULT 0      → Total characters added
│  └─ total_chars_deleted   INTEGER DEFAULT 0      → Total characters deleted
│
├─ PR Metrics (3 fields):
│  ├─ total_prs_created     INTEGER DEFAULT 0      → PRs created by staff
│  ├─ total_prs_merged      INTEGER DEFAULT 0      → PRs merged
│  └─ total_pr_approvals_given INTEGER DEFAULT 0   → Approvals given by staff
│
├─ Repository Metrics (2 fields):
│  ├─ repositories_touched  INTEGER DEFAULT 0      → Number of repos contributed to
│  └─ repository_list       TEXT                   → Comma-separated repo names
│
├─ Activity Timeline (4 fields):
│  ├─ first_commit_date     DATETIME               → First commit date
│  ├─ last_commit_date      DATETIME               → Most recent commit date
│  ├─ first_pr_date         DATETIME               → First PR created date
│  └─ last_pr_date          DATETIME               → Most recent PR date
│
├─ Technology Insights (2 fields):
│  ├─ file_types_worked     TEXT                   → JSON list of file extensions
│  └─ primary_file_type     VARCHAR(50)            → Most common file type
│
├─ Metadata (2 fields):
│  ├─ last_calculated       DATETIME               → When metrics were calculated
│  └─ calculation_version   VARCHAR(20)            → Calculator version
│
└─ Derived Metrics (3 fields):
   ├─ avg_lines_per_commit  FLOAT DEFAULT 0.0      → Average lines per commit
   ├─ avg_files_per_commit  FLOAT DEFAULT 0.0      → Average files per commit
   └─ code_churn_ratio      FLOAT DEFAULT 0.0      → Lines deleted / lines added

Relationships:
  └─→ staff_details (one-to-one via bank_id_1)

⚡ PERFORMANCE TIP: Always use staff_metrics instead of joining commits/PRs/staff_details!

Common Queries:
  • Top contributors: SELECT * FROM staff_metrics ORDER BY total_commits DESC LIMIT 10
  • Active staff with commits: SELECT * FROM staff_metrics WHERE total_commits > 0
  • Platform stats: SELECT platform_name, SUM(total_commits) FROM staff_metrics GROUP BY platform_name

═══════════════════════════════════════════════════════════════════════════════
📊 COMMON QUERY PATTERNS
═══════════════════════════════════════════════════════════════════════════════

1. Staff Productivity Summary:
   SELECT s.staff_name, sm.total_commits, sm.total_prs_created, sm.total_lines_added
   FROM staff_metrics sm
   JOIN staff_details s ON sm.bank_id_1 = s.bank_id_1
   WHERE s.staff_status = 'Active'
   ORDER BY sm.total_commits DESC

2. Team Commit Activity (use pre-calc table):
   SELECT tech_unit, SUM(total_commits) as team_commits
   FROM staff_metrics
   GROUP BY tech_unit
   ORDER BY team_commits DESC

3. PR Merge Rate by Author:
   SELECT author_name,
          COUNT(*) as total_prs,
          SUM(CASE WHEN state = 'MERGED' THEN 1 ELSE 0 END) as merged_prs,
          ROUND(SUM(CASE WHEN state = 'MERGED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as merge_rate
   FROM pull_requests
   GROUP BY author_name
   HAVING COUNT(*) > 5

4. Repository Activity Timeline:
   SELECT DATE(commit_date) as date, COUNT(*) as commits
   FROM commits
   WHERE commit_date >= DATE('now', '-30 days')
   GROUP BY DATE(commit_date)
   ORDER BY date

5. Top Code Reviewers:
   SELECT approver_name, COUNT(*) as approvals
   FROM pr_approvals
   GROUP BY approver_name
   ORDER BY approvals DESC
   LIMIT 10

═══════════════════════════════════════════════════════════════════════════════
💡 QUERY GENERATION TIPS
═══════════════════════════════════════════════════════════════════════════════

✅ DO:
  • Use staff_metrics for staff productivity queries (45x faster)
  • Use DATETIME functions: DATE(), strftime(), BETWEEN
  • Use proper JOINs with FK relationships
  • Add ORDER BY and LIMIT for large result sets
  • Use GROUP BY for aggregations

❌ DON'T:
  • Join commits + pull_requests + staff_details when staff_metrics exists
  • Use SELECT * without LIMIT on large tables
  • Forget to filter by date ranges for large datasets
  • Use LIKE '%pattern%' without indexes

═══════════════════════════════════════════════════════════════════════════════
🔑 KEY RELATIONSHIPS DIAGRAM
═══════════════════════════════════════════════════════════════════════════════

repositories ─┬─→ commits (1:N via repository_id)
              └─→ pull_requests (1:N via repository_id)

pull_requests ──→ pr_approvals (1:N via pull_request_id)

staff_details ─┬─→ author_staff_mapping (1:N via bank_id_1)
               └─→ staff_metrics (1:1 via bank_id_1) ⚡ PRE-CALCULATED

commits/pull_requests ──→ author_staff_mapping ──→ staff_details
                         (via author_email)       (via bank_id_1)

═══════════════════════════════════════════════════════════════════════════════
"""

        # API call to Dify
        url = "https://dify.api.apps.k8s.sp.ut.dbs.corp/v1/completion-messages"
        headers = {
            "Authorization": "Bearer app-4int1WqBf4BB4s7k84YUpJd",
            "Content-Type": "application/json"
        }

        payload = {
            "sqlschema": schema_string,
            "promptforData": request.prompt,
            "response_mode": "blocking",
            "user": "api_user"
        }

        # Disable SSL verification and suppress warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)

        if response.status_code == 200:
            result = response.json()
            generated_sql = result.get('answer', '').strip()

            # Clean up SQL (remove markdown code blocks)
            if generated_sql.startswith('```sql'):
                generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()
            elif generated_sql.startswith('```'):
                generated_sql = generated_sql.replace('```', '').strip()

            return AIQueryResponse(generated_sql=generated_sql)
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"AI API Error: {response.text}"
            )

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating query: {str(e)}")
