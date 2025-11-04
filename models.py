"""Database models for Git repository analysis."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
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
