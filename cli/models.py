"""Database models for Git repository analysis."""

from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, ForeignKey, create_engine, UniqueConstraint, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class Repository(Base):
    """
    Git repository information tracking all analyzed code repositories.
    Each repository represents a unique project tracked in the version control system.
    """
    __tablename__ = 'repositories'
    __table_args__ = {'comment': 'Stores information about Git repositories being analyzed for productivity metrics'}

    id = Column(Integer, primary_key=True, comment='Unique identifier for the repository')
    project_key = Column(String(255), nullable=False, comment='Project key or identifier from the version control system (e.g., Bitbucket project key)')
    slug_name = Column(String(255), nullable=False, comment='Repository slug name - the unique identifier within a project')
    clone_url = Column(String(500), nullable=False, comment='Git clone URL used to fetch repository data')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this repository was first added to the system')

    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(project_key='{self.project_key}', slug_name='{self.slug_name}')>"


class Commit(Base):
    """
    Individual Git commit records tracking all code changes.
    Each commit represents a single code contribution to a repository.
    Used for productivity analysis, code quality metrics, and developer activity tracking.
    """
    __tablename__ = 'commits'
    __table_args__ = {'comment': 'Individual Git commits with metadata for productivity analysis and code contribution tracking'}

    id = Column(Integer, primary_key=True, comment='Unique identifier for the commit record')
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False, comment='Foreign key linking to the repository this commit belongs to')
    commit_hash = Column(String(40), nullable=False, unique=True, comment='Git commit SHA-1 hash - unique identifier for the commit in Git')
    author_name = Column(String(255), comment='Name of the developer who authored the code changes')
    author_email = Column(String(255), comment='Email address of the commit author')
    committer_name = Column(String(255), comment='Name of the person who committed the code (may differ from author)')
    committer_email = Column(String(255), comment='Email address of the committer')
    commit_date = Column(DateTime, comment='Timestamp when the commit was created')
    message = Column(Text, comment='Commit message describing the changes made')
    lines_added = Column(Integer, default=0, comment='Number of lines of code added in this commit')
    lines_deleted = Column(Integer, default=0, comment='Number of lines of code deleted in this commit')
    files_changed = Column(Integer, default=0, comment='Number of files modified in this commit')
    chars_added = Column(Integer, default=0, comment='Number of characters added in this commit')
    chars_deleted = Column(Integer, default=0, comment='Number of characters deleted in this commit')
    file_types = Column(Text, comment='Comma-separated list of file types changed (e.g., "py,js,md")')
    branch = Column(String(255), default='master', comment='Git branch where this commit was made')

    repository = relationship("Repository", back_populates="commits")

    def __repr__(self):
        return f"<Commit(hash='{self.commit_hash[:7]}', author='{self.author_name}')>"


class PullRequest(Base):
    """
    Pull request (PR) records for code review and collaboration tracking.
    Represents proposed code changes submitted for review before merging.
    Critical for measuring code quality, collaboration, and review processes.
    """
    __tablename__ = 'pull_requests'
    __table_args__ = {'comment': 'Pull requests for code review tracking, collaboration metrics, and merge success analysis'}

    id = Column(Integer, primary_key=True, comment='Unique identifier for the pull request record')
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False, comment='Foreign key linking to the repository this PR belongs to')
    pr_number = Column(Integer, comment='Pull request number within the repository')
    title = Column(String(500), comment='Title or summary of the pull request')
    description = Column(Text, comment='Detailed description of changes proposed in the PR')
    author_name = Column(String(255), comment='Name of the developer who created the pull request')
    author_email = Column(String(255), comment='Email address of the PR author')
    created_date = Column(DateTime, comment='Timestamp when the PR was created')
    merged_date = Column(DateTime, comment='Timestamp when the PR was merged (null if not merged)')
    state = Column(String(50), comment='Current state of the PR: open, closed, or merged')
    source_branch = Column(String(255), comment='Git branch containing the proposed changes')
    target_branch = Column(String(255), comment='Git branch where changes will be merged (typically main/master)')
    lines_added = Column(Integer, default=0, comment='Total number of lines added across all commits in this PR')
    lines_deleted = Column(Integer, default=0, comment='Total number of lines deleted across all commits in this PR')
    commits_count = Column(Integer, default=0, comment='Number of commits included in this pull request')

    repository = relationship("Repository", back_populates="pull_requests")
    approvals = relationship("PRApproval", back_populates="pull_request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PullRequest(number={self.pr_number}, title='{self.title}')>"


class PRApproval(Base):
    """
    Pull request approval records tracking code review approvals.
    Each approval represents a reviewer's sign-off on proposed code changes.
    Used for measuring code review participation and quality assurance processes.
    """
    __tablename__ = 'pr_approvals'
    __table_args__ = {'comment': 'Tracks who approved pull requests and when - used for code review metrics and quality analysis'}

    id = Column(Integer, primary_key=True, comment='Unique identifier for the approval record')
    pull_request_id = Column(Integer, ForeignKey('pull_requests.id'), nullable=False, comment='Foreign key linking to the pull request that was approved')
    approver_name = Column(String(255), comment='Name of the reviewer who approved the pull request')
    approver_email = Column(String(255), comment='Email address of the approver')
    approval_date = Column(DateTime, comment='Timestamp when the approval was given')

    pull_request = relationship("PullRequest", back_populates="approvals")

    def __repr__(self):
        return f"<PRApproval(approver='{self.approver_name}')>"


class StaffDetails(Base):
    """
    Comprehensive staff/employee information from HR systems.
    Contains organizational structure, employment details, and metadata for all staff members.
    Used to link Git activity to actual employees and analyze productivity by organizational attributes.
    """
    __tablename__ = 'staff_details'
    __table_args__ = {'comment': 'HR master data for staff members including organizational structure, employment details, and demographic information'}

    # Primary Identification
    id = Column(Integer, primary_key=True, comment='Unique auto-increment identifier for the record')
    bank_id_1 = Column(String(50), comment='Primary bank/organization identifier for the staff member - key for linking to Git authors')
    staff_id = Column(String(50), comment='Employee ID or staff number from HR system')
    email_address = Column(String(255), comment='Official work email address of the staff member')

    # Personal Information
    staff_first_name = Column(String(255), comment='First name of the staff member')
    staff_last_name = Column(String(255), comment='Last name/surname of the staff member')
    staff_name = Column(String(255), comment='Full name of the staff member (typically first name + last name)')
    citizenship = Column(String(100), comment='Citizenship or nationality of the staff member')
    gender = Column(String(20), comment='Gender of the staff member')

    # Employment Status and Dates
    staff_status = Column(String(100), comment='Current employment status (e.g., Active, Inactive, On Leave)')
    sub_status = Column(String(100), comment='Detailed sub-status within the main employment status')
    movement_status = Column(String(100), comment='Status related to organizational movements (e.g., Transfer, Promotion)')
    staff_start_date = Column(Date, comment='Date when the staff member started employment')
    staff_end_date = Column(Date, comment='Date when the staff member ended employment (null if currently active)')
    last_work_day = Column(Date, comment='Last working day for the staff member')
    movement_date = Column(Date, comment='Date of last organizational movement or status change')

    # Staff Type and Classification
    original_staff_type = Column(String(100), comment='Original classification of staff type before any changes')
    staff_type = Column(String(100), comment='Current staff type (e.g., Permanent, Contract, Temporary, Consultant)')
    rank = Column(String(100), comment='Job rank or grade level within the organization')
    staff_level = Column(String(100), comment='Hierarchical level of the staff member')
    hr_role = Column(String(255), comment='Role designation from HR perspective')
    job_function = Column(String(255), comment='Primary job function or responsibility area')
    default_role = Column(String(255), comment='Default role assignment for the staff member')
    skill_set_type = Column(String(255), comment='Type or category of skills the staff member possesses')

    # Organizational Structure
    tech_unit = Column(String(255), comment='Technology unit or tech division the staff belongs to')
    division = Column(String(255), comment='Corporate division or business unit')
    department_id = Column(String(50), comment='Department identifier code')
    platform_index = Column(String(50), comment='Index or code for the platform/product')
    platform_name = Column(String(255), comment='Name of the platform or product the staff works on')
    platform_unit = Column(String(255), comment='Unit within the platform organization')
    platform_lead = Column(String(500), comment='Name of the platform lead or manager')
    sub_platform = Column(String(255), comment='Sub-platform or component within the main platform')
    staff_grouping = Column(String(100), comment='Grouping classification for the staff member (e.g., by skill, project, team)')

    # Reporting Structure
    reporting_manager_1bank_id = Column(String(50), comment='Bank ID of the direct reporting manager')
    reporting_manager_staff_id = Column(String(50), comment='Staff ID of the direct reporting manager')
    reporting_manager_name = Column(String(255), comment='Full name of the direct reporting manager')
    reporting_manager_pc_code = Column(String(50), comment='Profit center code of the reporting manager')

    # Work Location and Type
    work_location = Column(String(255), comment='Primary work location or office (e.g., Singapore, New York, Remote)')
    reporting_location = Column(String(255), comment='Official reporting location for HR purposes')
    primary_seating = Column(String(255), comment='Primary seating location or desk assignment')
    work_type1 = Column(String(100), comment='Primary work type classification')
    work_type2 = Column(String(100), comment='Secondary work type classification')

    # Company and Legal Entity
    company_name = Column(String(255), comment='Full legal name of the employing company')
    company_short_name = Column(String(100), comment='Abbreviated company name')

    # Financial and Billing
    staff_pc_code = Column(String(50), comment='Profit center code for the staff member')
    billing_pc_code = Column(String(50), comment='Profit center code used for billing purposes')
    people_cost_type = Column(String(100), comment='Type of cost classification for people costs')
    fte = Column(Float, comment='Full-Time Equivalent - proportion of full-time work (e.g., 1.0 = full-time, 0.5 = half-time)')
    hc_included = Column(String(20), comment='Flag indicating if headcount is included in official counts (Yes/No)')
    reason_for_hc_included_no = Column(String(255), comment='Explanation if headcount is not included in official counts')

    # Contract Information
    contract_start_date = Column(Date, comment='Start date of current employment contract')
    contract_end_date = Column(Date, comment='End date of current employment contract')
    original_tenure_start_date = Column(Date, comment='Original start date of tenure (may differ from current contract start)')
    po_number = Column(String(100), comment='Purchase Order number for contract staff')
    mcr_number = Column(String(100), comment='MCR (Managed Contractor Resource) number')
    assignment_id = Column(String(100), comment='Assignment identifier for contract or project-based staff')

    # Data Management
    as_of_date = Column(Date, comment='Snapshot date - the date this record represents (for historical tracking)')
    reporting_period = Column(String(50), comment='Reporting period this record belongs to (e.g., 2024-Q1, January-2024)')
    effective_date = Column(Date, comment='Date when this record becomes effective')
    effective_billing_date = Column(Date, comment='Date when billing information becomes effective')
    created_by = Column(String(255), comment='Username or system that created this record')
    date_created = Column(DateTime, comment='Timestamp when this record was created in the database')
    modified_by = Column(String(255), comment='Username or system that last modified this record')
    date_modified = Column(DateTime, comment='Timestamp when this record was last modified')

    def __repr__(self):
        return f"<StaffDetails(staff_id='{self.staff_id}', staff_name='{self.staff_name}')>"


class AuthorStaffMapping(Base):
    """
    Mapping table linking Git commit authors to organizational staff records.
    This is the critical bridge that connects version control activity to HR employee data.
    Enables attribution of code contributions to specific employees for productivity analytics.
    """
    __tablename__ = 'author_staff_mapping'
    __table_args__ = {'comment': 'Maps Git commit author names/emails to staff members - enables linking code contributions to employees'}

    id = Column(Integer, primary_key=True, comment='Unique identifier for the mapping record')
    author_name = Column(String(255), nullable=False, unique=True, comment='Git author name as it appears in commits (e.g., "John Doe") - must be unique')
    author_email = Column(String(255), comment='Git author email address as it appears in commits')
    bank_id_1 = Column(String(50), comment='Bank ID from staff_details table - links to the employee')
    staff_id = Column(String(50), comment='Employee ID from staff_details table')
    staff_name = Column(String(255), comment='Official staff name from HR system (may differ from Git author name)')
    mapped_date = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this mapping was created')
    notes = Column(Text, comment='Additional notes about the mapping (e.g., why multiple Git names map to one person, special cases)')

    def __repr__(self):
        return f"<AuthorStaffMapping(author='{self.author_name}', bank_id='{self.bank_id_1}')>"


class StaffMetrics(Base):
    """
    Pre-calculated productivity metrics for staff members.
    This table stores aggregated metrics computed during CLI extract phase,
    eliminating the need for complex frontend calculations and improving performance.
    Updated whenever new commits are extracted or staff mappings change.
    """
    __tablename__ = 'staff_metrics'
    __table_args__ = {'comment': 'Pre-calculated productivity metrics for staff members - computed during extract phase for fast dashboard loading'}

    # Primary Identification
    id = Column(Integer, primary_key=True, comment='Unique identifier for the metric record')
    bank_id_1 = Column(String(50), nullable=False, unique=True, index=True, comment='Bank ID from staff_details - links to employee (unique per staff)')
    staff_id = Column(String(50), comment='Employee ID from staff_details')
    staff_name = Column(String(255), comment='Staff member name from HR system')
    email_address = Column(String(255), comment='Staff email address')

    # Organizational Fields (denormalized for fast queries)
    tech_unit = Column(String(255), comment='Technology unit from staff_details')
    platform_name = Column(String(255), comment='Platform name from staff_details')
    staff_type = Column(String(100), comment='Staff type from staff_details')
    original_staff_type = Column(String(100), comment='Original staff type from staff_details')
    staff_status = Column(String(100), comment='Staff status from staff_details')
    work_location = Column(String(255), comment='Work location from staff_details')
    rank = Column(String(100), comment='Job rank from staff_details')
    staff_level = Column(String(100), comment='Staff level from staff_details')
    hr_role = Column(String(255), comment='HR role from staff_details')
    job_function = Column(String(255), comment='Job function from staff_details')
    department_id = Column(String(50), comment='Department ID from staff_details')
    company_name = Column(String(255), comment='Company name from staff_details')
    sub_platform = Column(String(255), comment='Sub-platform from staff_details')
    staff_grouping = Column(String(100), comment='Staff grouping from staff_details')
    reporting_manager_name = Column(String(255), comment='Reporting manager from staff_details')

    # Commit Metrics
    total_commits = Column(Integer, default=0, comment='Total number of commits by this staff member')
    total_lines_added = Column(Integer, default=0, comment='Total lines of code added across all commits')
    total_lines_deleted = Column(Integer, default=0, comment='Total lines of code deleted across all commits')
    total_files_changed = Column(Integer, default=0, comment='Total number of files changed across all commits')
    total_chars_added = Column(Integer, default=0, comment='Total characters added across all commits')
    total_chars_deleted = Column(Integer, default=0, comment='Total characters deleted across all commits')

    # Pull Request Metrics
    total_prs_created = Column(Integer, default=0, comment='Total number of pull requests created by this staff member')
    total_prs_merged = Column(Integer, default=0, comment='Total number of pull requests merged')
    total_pr_approvals_given = Column(Integer, default=0, comment='Total number of PR approvals given by this staff member')

    # Repository Metrics
    repositories_touched = Column(Integer, default=0, comment='Number of unique repositories this staff has committed to')
    repository_list = Column(Text, comment='Comma-separated list of repository names')

    # Activity Timeline
    first_commit_date = Column(DateTime, comment='Date of first commit by this staff member')
    last_commit_date = Column(DateTime, comment='Date of most recent commit')
    first_pr_date = Column(DateTime, comment='Date of first PR created')
    last_pr_date = Column(DateTime, comment='Date of most recent PR created')

    # Technology Insights
    file_types_worked = Column(Text, comment='Comma-separated list of file types/extensions worked on (e.g., "py,js,md")')
    primary_file_type = Column(String(50), comment='Most frequently modified file type')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Timestamp when metrics were last calculated')
    calculation_version = Column(String(20), default='1.0', comment='Version of calculation logic used')

    # Derived Metrics
    avg_lines_per_commit = Column(Float, default=0.0, comment='Average lines changed per commit')
    avg_files_per_commit = Column(Float, default=0.0, comment='Average files changed per commit')
    code_churn_ratio = Column(Float, default=0.0, comment='Ratio of deleted to added lines (churn indicator)')

    def __repr__(self):
        return f"<StaffMetrics(bank_id='{self.bank_id_1}', staff_name='{self.staff_name}', commits={self.total_commits})>"


class CurrentYearStaffMetrics(Base):
    """Current year metrics for staff members (separate table)."""
    __tablename__ = 'current_year_staff_metrics'

    # Primary Key
    id = Column(Integer, primary_key=True, comment='Auto-incrementing primary key')

    # Staff Identification
    bank_id_1 = Column(String(100), nullable=False, unique=True, index=True, comment='Primary staff identifier (bank ID)')
    staff_name = Column(String(255), nullable=False, comment='Full name of the staff member')
    staff_email = Column(String(255), comment='Staff email address')
    staff_status = Column(String(50), comment='Staff status (Active/Inactive)')
    staff_pc_code = Column(String(100), comment='Staff PC code from staff_details')
    default_role = Column(String(255), comment='Default role from staff_details')

    # Current Year Context
    current_year = Column(Integer, nullable=False, comment='Year for which current year metrics are calculated')
    cy_start_date = Column(Date, comment='Start date for current year metrics')
    cy_end_date = Column(Date, comment='End date for current year metrics')

    # Activity Totals
    cy_total_commits = Column(Integer, default=0, comment='Total commits in current year')
    cy_total_prs = Column(Integer, default=0, comment='Total PRs created in current year')
    cy_total_approvals_given = Column(Integer, default=0, comment='Total PR approvals given in current year')
    cy_total_code_reviews_given = Column(Integer, default=0, comment='Total code reviews given in current year (PRs reviewed)')
    cy_total_code_reviews_received = Column(Integer, default=0, comment='Total code reviews received in current year (own PRs reviewed)')
    cy_total_repositories = Column(Integer, default=0, comment='Number of unique repositories touched in current year')
    cy_total_files_changed = Column(Integer, default=0, comment='Total files changed in current year')
    cy_total_lines_changed = Column(Integer, default=0, comment='Total lines (added+deleted) in current year')
    cy_total_chars = Column(Integer, default=0, comment='Total characters (added+deleted) in current year')
    cy_total_code_churn = Column(Integer, default=0, comment='Code churn (lines deleted) in current year')

    # Diversity Metrics
    cy_different_file_types = Column(Integer, default=0, comment='Number of different file types worked in current year')
    cy_different_repositories = Column(Integer, default=0, comment='Number of different repositories in current year')
    cy_different_project_keys = Column(Integer, default=0, comment='Number of different project keys in current year')

    # File Type Distribution Percentages
    cy_pct_code = Column(Float, default=0.0, comment='Percentage of code files (java, js, jsx, tsx, sql, py, etc.)')
    cy_pct_config = Column(Float, default=0.0, comment='Percentage of config files (xml, json, yml, properties, config, no-extension)')
    cy_pct_documentation = Column(Float, default=0.0, comment='Percentage of documentation files (md)')

    # Monthly Averages
    cy_avg_commits_monthly = Column(Float, default=0.0, comment='Average commits per month in current year')
    cy_avg_prs_monthly = Column(Float, default=0.0, comment='Average PRs per month in current year')
    cy_avg_approvals_monthly = Column(Float, default=0.0, comment='Average approvals per month in current year')

    # Details Lists
    cy_file_types_list = Column(Text, comment='Comma-separated list of file types in current year')
    cy_repositories_list = Column(Text, comment='Comma-separated list of repositories in current year')
    cy_project_keys_list = Column(Text, comment='Comma-separated list of project keys in current year')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Timestamp when metrics were last calculated')
    calculation_version = Column(String(20), default='1.0', comment='Version of calculation logic used')

    def __repr__(self):
        return f"<CurrentYearStaffMetrics(bank_id='{self.bank_id_1}', staff_name='{self.staff_name}', year={self.current_year}, commits={self.cy_total_commits})>"


class CommitMetrics(Base):
    """Pre-calculated commit metrics by date/author/repository."""
    __tablename__ = 'commit_metrics'

    # Primary Key
    id = Column(Integer, primary_key=True, comment='Unique record ID')

    # Dimensions
    commit_date = Column(Date, nullable=False, index=True, comment='Commit date (normalized to date only)')
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False, index=True, comment='Repository FK')
    author_email = Column(String(255), index=True, comment='Author email for grouping')
    author_name = Column(String(255), comment='Author display name')
    branch = Column(String(255), index=True, comment='Git branch name')

    # Aggregated Metrics
    commit_count = Column(Integer, default=0, comment='Number of commits')
    total_lines_added = Column(Integer, default=0, comment='Total lines added')
    total_lines_deleted = Column(Integer, default=0, comment='Total lines deleted')
    total_files_changed = Column(Integer, default=0, comment='Total files modified')
    total_chars_added = Column(Integer, default=0, comment='Total characters added')
    total_chars_deleted = Column(Integer, default=0, comment='Total characters deleted')

    # File Type Breakdown (JSON)
    file_types_json = Column(Text, comment='JSON: {"py": 5, "js": 3, ...}')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Last calculation timestamp')
    calculation_version = Column(String(20), default='1.0', comment='Calculator version')

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('commit_date', 'repository_id', 'author_email', 'branch', name='uq_commit_metrics'),
        Index('idx_commit_metrics_date_repo', 'commit_date', 'repository_id'),
    )

    def __repr__(self):
        return f"<CommitMetrics(date={self.commit_date}, author={self.author_name}, commits={self.commit_count})>"


class PRMetrics(Base):
    """Pre-calculated pull request metrics by date/author/repository."""
    __tablename__ = 'pr_metrics'

    # Primary Key
    id = Column(Integer, primary_key=True, comment='Unique record ID')

    # Dimensions
    pr_date = Column(Date, nullable=False, index=True, comment='PR created date (normalized)')
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False, index=True, comment='Repository FK')
    author_email = Column(String(255), index=True, comment='PR author email')
    author_name = Column(String(255), comment='PR author name')
    state = Column(String(50), index=True, comment='PR state: OPEN, MERGED, DECLINED')

    # Aggregated Metrics
    pr_count = Column(Integer, default=0, comment='Number of PRs')
    merged_count = Column(Integer, default=0, comment='Number of merged PRs')
    declined_count = Column(Integer, default=0, comment='Number of declined PRs')
    open_count = Column(Integer, default=0, comment='Number of open PRs')

    total_lines_added = Column(Integer, default=0, comment='Total lines added in PRs')
    total_lines_deleted = Column(Integer, default=0, comment='Total lines deleted in PRs')
    total_commits_in_prs = Column(Integer, default=0, comment='Total commits within PRs')

    # Timing Metrics
    avg_time_to_merge_hours = Column(Float, default=0.0, comment='Average hours from creation to merge')
    total_approvals_received = Column(Integer, default=0, comment='Total approvals received on PRs')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Last calculation timestamp')
    calculation_version = Column(String(20), default='1.0', comment='Calculator version')

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('pr_date', 'repository_id', 'author_email', 'state', name='uq_pr_metrics'),
        Index('idx_pr_metrics_date_repo', 'pr_date', 'repository_id'),
    )

    def __repr__(self):
        return f"<PRMetrics(date={self.pr_date}, author={self.author_name}, prs={self.pr_count})>"


class RepositoryMetrics(Base):
    """Pre-calculated repository-level metrics."""
    __tablename__ = 'repository_metrics'

    # Primary Key
    id = Column(Integer, primary_key=True, comment='Unique record ID')

    # Dimensions
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False, unique=True, index=True, comment='Repository FK')
    project_key = Column(String(255), comment='Bitbucket project key (denormalized)')
    slug_name = Column(String(255), comment='Repository slug (denormalized)')

    # Commit Metrics
    total_commits = Column(Integer, default=0, comment='Total commits in repository')
    total_authors = Column(Integer, default=0, comment='Unique contributors count')
    total_lines_added = Column(Integer, default=0, comment='Total lines added')
    total_lines_deleted = Column(Integer, default=0, comment='Total lines deleted')
    total_files_changed = Column(Integer, default=0, comment='Total files modified')

    # PR Metrics
    total_prs = Column(Integer, default=0, comment='Total pull requests')
    total_prs_merged = Column(Integer, default=0, comment='Total merged PRs')
    total_prs_open = Column(Integer, default=0, comment='Currently open PRs')
    merge_rate = Column(Float, default=0.0, comment='PR merge rate percentage')

    # Activity Timeline
    first_commit_date = Column(DateTime, comment='First commit in repository')
    last_commit_date = Column(DateTime, comment='Most recent commit')
    first_pr_date = Column(DateTime, comment='First PR created')
    last_pr_date = Column(DateTime, comment='Most recent PR')

    # Activity Indicators
    days_since_last_commit = Column(Integer, default=0, comment='Days since last activity')
    is_active = Column(Boolean, default=True, comment='Active if commits in last 90 days')

    # Top Contributors (JSON)
    top_contributors_json = Column(Text, comment='JSON array of top 10 contributors')

    # File Types (JSON)
    file_types_json = Column(Text, comment='JSON: {"py": 150, "js": 80, ...}')

    # Branch Stats
    total_branches = Column(Integer, default=0, comment='Number of branches')
    main_branch_name = Column(String(255), comment='Main branch name (master/main)')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Last calculation timestamp')
    calculation_version = Column(String(20), default='1.0', comment='Calculator version')

    def __repr__(self):
        return f"<RepositoryMetrics(slug={self.slug_name}, commits={self.total_commits}, prs={self.total_prs})>"


class AuthorMetrics(Base):
    """Pre-calculated author-level metrics (before staff mapping)."""
    __tablename__ = 'author_metrics'

    # Primary Key
    id = Column(Integer, primary_key=True, comment='Unique record ID')

    # Dimensions
    author_email = Column(String(255), nullable=False, unique=True, index=True, comment='Git author email (unique)')
    author_name = Column(String(255), comment='Git author display name')

    # Staff Mapping
    bank_id_1 = Column(String(50), index=True, comment='Mapped staff bank ID (if mapped)')
    is_mapped = Column(Boolean, default=False, comment='True if mapped to staff')

    # Commit Metrics
    total_commits = Column(Integer, default=0, comment='Total commits by author')
    total_lines_added = Column(Integer, default=0, comment='Total lines added')
    total_lines_deleted = Column(Integer, default=0, comment='Total lines deleted')
    total_files_changed = Column(Integer, default=0, comment='Total files modified')
    total_chars_added = Column(Integer, default=0, comment='Total characters added')
    total_chars_deleted = Column(Integer, default=0, comment='Total characters deleted')

    # PR Metrics
    total_prs_created = Column(Integer, default=0, comment='PRs created by author')
    total_prs_merged = Column(Integer, default=0, comment='PRs merged')
    total_pr_approvals_given = Column(Integer, default=0, comment='Approvals given by author')

    # Repository Metrics
    repositories_touched = Column(Integer, default=0, comment='Number of repositories contributed to')
    repository_list = Column(Text, comment='Comma-separated repository names')

    # Activity Timeline
    first_commit_date = Column(DateTime, comment='First commit by author')
    last_commit_date = Column(DateTime, comment='Most recent commit')
    first_pr_date = Column(DateTime, comment='First PR created')
    last_pr_date = Column(DateTime, comment='Most recent PR')

    # Technology Insights
    file_types_worked = Column(Text, comment='JSON list of file types')
    primary_file_type = Column(String(50), comment='Most common file extension')

    # Derived Metrics
    avg_lines_per_commit = Column(Float, default=0.0, comment='Average lines per commit')
    avg_files_per_commit = Column(Float, default=0.0, comment='Average files per commit')
    code_churn_ratio = Column(Float, default=0.0, comment='Lines deleted / lines added')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Last calculation timestamp')
    calculation_version = Column(String(20), default='1.0', comment='Calculator version')

    def __repr__(self):
        return f"<AuthorMetrics(email={self.author_email}, commits={self.total_commits}, mapped={self.is_mapped})>"


class TeamMetrics(Base):
    """Pre-calculated team/platform/tech unit aggregations."""
    __tablename__ = 'team_metrics'

    # Primary Key
    id = Column(Integer, primary_key=True, comment='Unique record ID')

    # Dimensions
    aggregation_level = Column(String(50), nullable=False, index=True, comment='Level: tech_unit, platform, rank, location')
    aggregation_value = Column(String(255), nullable=False, index=True, comment='Value: "Tech Unit A", "Platform X", etc.')
    time_period = Column(String(20), index=True, comment='Time period: all_time, 2024, 2024-Q1, 2024-01')

    # Team Composition
    total_staff = Column(Integer, default=0, comment='Total staff members')
    active_contributors = Column(Integer, default=0, comment='Staff with commits')
    active_rate = Column(Float, default=0.0, comment='Percentage of staff with commits')

    # Commit Metrics
    total_commits = Column(Integer, default=0, comment='Total commits by team')
    total_lines_added = Column(Integer, default=0, comment='Total lines added')
    total_lines_deleted = Column(Integer, default=0, comment='Total lines deleted')
    total_files_changed = Column(Integer, default=0, comment='Total files modified')

    # PR Metrics
    total_prs_created = Column(Integer, default=0, comment='Total PRs created')
    total_prs_merged = Column(Integer, default=0, comment='Total PRs merged')
    total_pr_approvals = Column(Integer, default=0, comment='Total PR approvals given')
    merge_rate = Column(Float, default=0.0, comment='PR merge rate percentage')

    # Repository Metrics
    repositories_touched = Column(Integer, default=0, comment='Repositories team contributed to')
    repository_list = Column(Text, comment='Comma-separated repository names')

    # Averages per Person
    avg_commits_per_person = Column(Float, default=0.0, comment='Average commits per staff member')
    avg_prs_per_person = Column(Float, default=0.0, comment='Average PRs per staff member')
    avg_lines_per_person = Column(Float, default=0.0, comment='Average lines per staff member')

    # Top Contributors (JSON)
    top_contributors_json = Column(Text, comment='JSON array: [{"name": "...", "commits": 100}, ...]')

    # Technology Insights
    file_types_json = Column(Text, comment='JSON: {"py": 500, "js": 300, ...}')
    primary_technologies = Column(Text, comment='Comma-separated top 5 file types')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Last calculation timestamp')
    calculation_version = Column(String(20), default='1.0', comment='Calculator version')

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('aggregation_level', 'aggregation_value', 'time_period', name='uq_team_metrics'),
        Index('idx_team_metrics_level_value', 'aggregation_level', 'aggregation_value'),
    )

    def __repr__(self):
        return f"<TeamMetrics(level={self.aggregation_level}, value={self.aggregation_value}, period={self.time_period})>"


class DailyMetrics(Base):
    """Pre-calculated daily organization-wide metrics."""
    __tablename__ = 'daily_metrics'

    # Primary Key
    id = Column(Integer, primary_key=True, comment='Unique record ID')

    # Dimension
    metric_date = Column(Date, nullable=False, unique=True, index=True, comment='Metrics date')

    # Daily Activity
    commits_today = Column(Integer, default=0, comment='Commits on this date')
    authors_active_today = Column(Integer, default=0, comment='Unique authors with commits')
    prs_created_today = Column(Integer, default=0, comment='PRs created')
    prs_merged_today = Column(Integer, default=0, comment='PRs merged')
    pr_approvals_today = Column(Integer, default=0, comment='PR approvals given')

    # Code Volume
    lines_added_today = Column(Integer, default=0, comment='Lines added')
    lines_deleted_today = Column(Integer, default=0, comment='Lines deleted')
    files_changed_today = Column(Integer, default=0, comment='Files modified')

    # Repository Activity
    repositories_active_today = Column(Integer, default=0, comment='Repositories with commits')

    # Cumulative Metrics (up to this date)
    cumulative_commits = Column(Integer, default=0, comment='Total commits up to date')
    cumulative_prs = Column(Integer, default=0, comment='Total PRs up to date')
    cumulative_authors = Column(Integer, default=0, comment='Total unique authors up to date')

    # Day of Week Analysis
    day_of_week = Column(String(10), comment='Monday, Tuesday, ...')
    is_weekend = Column(Boolean, default=False, comment='True if Saturday/Sunday')

    # Moving Averages (7-day and 30-day)
    commits_7day_avg = Column(Float, default=0.0, comment='7-day moving average of commits')
    commits_30day_avg = Column(Float, default=0.0, comment='30-day moving average of commits')

    # Metadata
    last_calculated = Column(DateTime, default=datetime.utcnow, comment='Last calculation timestamp')
    calculation_version = Column(String(20), default='1.0', comment='Calculator version')

    def __repr__(self):
        return f"<DailyMetrics(date={self.metric_date}, commits={self.commits_today}, authors={self.authors_active_today})>"


def get_engine(db_config):
    """
    Create SQLAlchemy database engine based on configuration.

    Supports multiple database types (SQLite for development, MariaDB/MySQL for production).
    The engine manages connection pooling and database dialect-specific behavior.

    Args:
        db_config (dict): Database configuration dictionary containing:
            - type (str): Database type - 'sqlite' or 'mariadb'
            - For SQLite:
                - path (str): File path to SQLite database file
            - For MariaDB:
                - host (str): Database server hostname or IP
                - port (int): Database server port (typically 3306)
                - user (str): Database username
                - password (str): Database password
                - database (str): Database name/schema

    Returns:
        sqlalchemy.engine.Engine: Configured database engine ready for use

    Raises:
        ValueError: If database type is not supported

    Examples:
        >>> # SQLite configuration
        >>> sqlite_config = {'type': 'sqlite', 'path': 'data/productivity.db'}
        >>> engine = get_engine(sqlite_config)

        >>> # MariaDB configuration
        >>> mariadb_config = {
        ...     'type': 'mariadb',
        ...     'host': 'localhost',
        ...     'port': 3306,
        ...     'user': 'analytics_user',
        ...     'password': 'secure_password',
        ...     'database': 'git_analytics'
        ... }
        >>> engine = get_engine(mariadb_config)
    """
    if db_config['type'] == 'sqlite':
        return create_engine(f"sqlite:///{db_config['path']}", echo=False)
    elif db_config['type'] == 'mariadb':
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        return create_engine(connection_string, echo=False)
    else:
        raise ValueError(f"Unsupported database type: {db_config['type']}")


def init_database(engine):
    """
    Initialize the database schema by creating all tables.

    Creates all tables defined in the SQLAlchemy models if they don't exist.
    This is idempotent - safe to call multiple times, won't recreate existing tables.
    Uses the table definitions from all model classes (Repository, Commit, PullRequest,
    PRApproval, StaffDetails, AuthorStaffMapping).

    Args:
        engine (sqlalchemy.engine.Engine): Database engine from get_engine()

    Returns:
        None

    Note:
        - This does NOT drop existing tables or modify existing table structures
        - For schema migrations, use a proper migration tool like Alembic
        - Table comments and column comments are created if the database supports them

    Example:
        >>> from config import Config
        >>> config = Config()
        >>> db_config = config.get_db_config()
        >>> engine = get_engine(db_config)
        >>> init_database(engine)  # Creates all tables
    """
    Base.metadata.create_all(engine)


def get_session(engine):
    """
    Create and return a new database session for executing queries.

    Sessions represent a workspace for your database operations and manage
    the lifecycle of database transactions. Each session should be closed
    when done to release database connections back to the pool.

    Args:
        engine (sqlalchemy.engine.Engine): Database engine from get_engine()

    Returns:
        sqlalchemy.orm.Session: Database session for querying and committing changes

    Best Practices:
        - Always close sessions when done: session.close()
        - Use try/finally blocks to ensure sessions are closed even on errors
        - Or use context managers for automatic cleanup

    Example:
        >>> engine = get_engine(db_config)
        >>> session = get_session(engine)
        >>> try:
        ...     # Query the database
        ...     repos = session.query(Repository).all()
        ...     for repo in repos:
        ...         print(repo.slug_name)
        ... finally:
        ...     session.close()  # Always close the session
    """
    Session = sessionmaker(bind=engine)
    return Session()
