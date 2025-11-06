"""Database models for Git repository analysis."""

from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class Repository(Base):
    """Repository information."""
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    project_key = Column(String(255), nullable=False)
    slug_name = Column(String(255), nullable=False)
    clone_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(project_key='{self.project_key}', slug_name='{self.slug_name}')>"


class Commit(Base):
    """Git commit information."""
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    commit_hash = Column(String(40), nullable=False, unique=True)
    author_name = Column(String(255))
    author_email = Column(String(255))
    committer_name = Column(String(255))
    committer_email = Column(String(255))
    commit_date = Column(DateTime)
    message = Column(Text)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)
    branch = Column(String(255), default='master')

    repository = relationship("Repository", back_populates="commits")

    def __repr__(self):
        return f"<Commit(hash='{self.commit_hash[:7]}', author='{self.author_name}')>"


class PullRequest(Base):
    """Pull request information."""
    __tablename__ = 'pull_requests'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    pr_number = Column(Integer)
    title = Column(String(500))
    description = Column(Text)
    author_name = Column(String(255))
    author_email = Column(String(255))
    created_date = Column(DateTime)
    merged_date = Column(DateTime)
    state = Column(String(50))  # open, closed, merged
    source_branch = Column(String(255))
    target_branch = Column(String(255))
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    commits_count = Column(Integer, default=0)

    repository = relationship("Repository", back_populates="pull_requests")
    approvals = relationship("PRApproval", back_populates="pull_request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PullRequest(number={self.pr_number}, title='{self.title}')>"


class PRApproval(Base):
    """Pull request approval information."""
    __tablename__ = 'pr_approvals'

    id = Column(Integer, primary_key=True)
    pull_request_id = Column(Integer, ForeignKey('pull_requests.id'), nullable=False)
    approver_name = Column(String(255))
    approver_email = Column(String(255))
    approval_date = Column(DateTime)

    pull_request = relationship("PullRequest", back_populates="approvals")

    def __repr__(self):
        return f"<PRApproval(approver='{self.approver_name}')>"


class StaffDetails(Base):
    """Staff details information from HR data."""
    __tablename__ = 'staff_details'

    id = Column(Integer, primary_key=True)
    bank_id_1 = Column(String(50))
    as_of_date = Column(Date)
    reporting_period = Column(String(50))
    tech_unit = Column(String(255))
    staff_first_name = Column(String(255))
    staff_last_name = Column(String(255))
    staff_name = Column(String(255))
    staff_id = Column(String(50))
    citizenship = Column(String(100))
    original_staff_type = Column(String(100))
    staff_type = Column(String(100))
    staff_status = Column(String(100))
    sub_status = Column(String(100))
    movement_status = Column(String(100))
    rank = Column(String(100))
    hr_role = Column(String(255))
    staff_start_date = Column(Date)
    staff_end_date = Column(Date)
    reporting_manager_1bank_id = Column(String(50))
    reporting_manager_staff_id = Column(String(50))
    reporting_manager_name = Column(String(255))
    staff_pc_code = Column(String(50))
    work_type1 = Column(String(100))
    work_type2 = Column(String(100))
    reporting_location = Column(String(255))
    work_location = Column(String(255))
    primary_seating = Column(String(255))
    company_name = Column(String(255))
    company_short_name = Column(String(100))
    last_work_day = Column(Date)
    department_id = Column(String(50))
    gender = Column(String(20))
    hc_included = Column(String(20))
    reason_for_hc_included_no = Column(String(255))
    email_address = Column(String(255))
    platform_index = Column(String(50))
    platform_lead = Column(String(255))
    platform_name = Column(String(255))
    platform_unit = Column(String(255))
    sub_platform = Column(String(255))
    staff_grouping = Column(String(100))
    job_function = Column(String(255))
    default_role = Column(String(255))
    division = Column(String(255))
    staff_level = Column(String(100))
    people_cost_type = Column(String(100))
    fte = Column(Float)
    effective_date = Column(Date)
    created_by = Column(String(255))
    date_created = Column(DateTime)
    modified_by = Column(String(255))
    date_modified = Column(DateTime)
    movement_date = Column(Date)
    reporting_manager_pc_code = Column(String(50))
    contract_start_date = Column(Date)
    contract_end_date = Column(Date)
    original_tenure_start_date = Column(Date)
    effective_billing_date = Column(Date)
    billing_pc_code = Column(String(50))
    skill_set_type = Column(String(255))
    po_number = Column(String(100))
    mcr_number = Column(String(100))
    assignment_id = Column(String(100))

    def __repr__(self):
        return f"<StaffDetails(staff_id='{self.staff_id}', staff_name='{self.staff_name}')>"


class AuthorStaffMapping(Base):
    """Mapping between commit authors and staff details."""
    __tablename__ = 'author_staff_mapping'

    id = Column(Integer, primary_key=True)
    author_name = Column(String(255), nullable=False, unique=True)
    author_email = Column(String(255))
    bank_id_1 = Column(String(50))
    staff_id = Column(String(50))
    staff_name = Column(String(255))
    mapped_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    def __repr__(self):
        return f"<AuthorStaffMapping(author='{self.author_name}', bank_id='{self.bank_id_1}')>"


def get_engine(db_config):
    """Create database engine based on configuration."""
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
    """Initialize database schema."""
    Base.metadata.create_all(engine)


def get_session(engine):
    """Get database session."""
    Session = sessionmaker(bind=engine)
    return Session()
