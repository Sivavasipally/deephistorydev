"""Database models for Git repository analysis."""

from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, ForeignKey, create_engine
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
    platform_lead = Column(String(255), comment='Name of the platform lead or manager')
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
