"""
SQLite to MariaDB/MySQL Data Synchronization Tool

This script synchronizes data from SQLite to MariaDB/MySQL with proper:
- ID mapping and regeneration
- Foreign key constraint handling
- Relationship preservation
- Transaction management
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from collections import defaultdict
import json

from cli.models import (
    Repository, Commit, PullRequest, PRApproval, Author,
    StaffDetails, AuthorStaffMapping, StaffMetrics, CurrentYearStaffMetrics
)


class DataSyncManager:
    """Manages data synchronization from SQLite to MariaDB."""

    def __init__(self, sqlite_url, mariadb_url):
        """Initialize sync manager with source and destination databases."""
        self.sqlite_engine = create_engine(sqlite_url)
        self.mariadb_engine = create_engine(mariadb_url)

        # Create sessions
        SQLiteSession = sessionmaker(bind=self.sqlite_engine)
        MariaDBSession = sessionmaker(bind=self.mariadb_engine)

        self.sqlite_session = SQLiteSession()
        self.mariadb_session = MariaDBSession()

        # ID mapping storage: {table_name: {old_id: new_id}}
        self.id_mappings = defaultdict(dict)

        # Statistics
        self.stats = {
            'repositories': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'commits': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'pull_requests': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'pr_approvals': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'authors': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'staff_details': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'author_mappings': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'staff_metrics': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
            'current_year_metrics': {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0},
        }

    def check_target_tables(self):
        """Check if target tables exist in MariaDB."""
        print("\n" + "=" * 80)
        print("CHECKING TARGET DATABASE")
        print("=" * 80)

        inspector = inspect(self.mariadb_engine)
        existing_tables = inspector.get_table_names()

        required_tables = [
            'repositories', 'commits', 'pull_requests', 'pr_approvals',
            'authors', 'staff_details', 'author_staff_mapping',
            'staff_metrics', 'current_year_staff_metrics'
        ]

        missing_tables = [t for t in required_tables if t not in existing_tables]

        if missing_tables:
            print(f"\n[WARNING] Missing tables in target database: {', '.join(missing_tables)}")
            print("          Run migrations first to create the schema.")
            return False

        print("\n[OK] All required tables exist in target database")
        return True

    def sync_repositories(self):
        """Sync repositories table."""
        print("\n" + "=" * 80)
        print("SYNCING REPOSITORIES")
        print("=" * 80)

        repos = self.sqlite_session.query(Repository).all()
        self.stats['repositories']['total'] = len(repos)

        print(f"\nFound {len(repos)} repositories to sync")

        for repo in repos:
            try:
                # Check if already exists by slug
                existing = self.mariadb_session.query(Repository).filter(
                    Repository.slug == repo.slug
                ).first()

                if existing:
                    # Map old ID to existing ID
                    self.id_mappings['repositories'][repo.id] = existing.id
                    self.stats['repositories']['skipped'] += 1
                    print(f"  [SKIP] Repository '{repo.slug}' already exists (ID: {repo.id} -> {existing.id})")
                    continue

                # Create new repository (auto-generates new ID)
                new_repo = Repository(
                    slug=repo.slug,
                    name=repo.name,
                    project_key=repo.project_key,
                    project_name=repo.project_name
                )

                self.mariadb_session.add(new_repo)
                self.mariadb_session.flush()  # Get the new ID

                # Map old ID to new ID
                self.id_mappings['repositories'][repo.id] = new_repo.id
                self.stats['repositories']['synced'] += 1

                print(f"  [SYNC] Repository '{repo.slug}' (ID: {repo.id} -> {new_repo.id})")

            except Exception as e:
                self.stats['repositories']['failed'] += 1
                print(f"  [ERROR] Failed to sync repository '{repo.slug}': {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nRepositories: {self.stats['repositories']['synced']} synced, "
              f"{self.stats['repositories']['skipped']} skipped, "
              f"{self.stats['repositories']['failed']} failed")

    def sync_authors(self):
        """Sync authors table."""
        print("\n" + "=" * 80)
        print("SYNCING AUTHORS")
        print("=" * 80)

        authors = self.sqlite_session.query(Author).all()
        self.stats['authors']['total'] = len(authors)

        print(f"\nFound {len(authors)} authors to sync")

        for author in authors:
            try:
                # Check if already exists by email
                existing = self.mariadb_session.query(Author).filter(
                    Author.email == author.email
                ).first()

                if existing:
                    self.id_mappings['authors'][author.id] = existing.id
                    self.stats['authors']['skipped'] += 1
                    continue

                # Create new author
                new_author = Author(
                    name=author.name,
                    email=author.email
                )

                self.mariadb_session.add(new_author)
                self.mariadb_session.flush()

                self.id_mappings['authors'][author.id] = new_author.id
                self.stats['authors']['synced'] += 1

            except Exception as e:
                self.stats['authors']['failed'] += 1
                print(f"  [ERROR] Failed to sync author '{author.email}': {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nAuthors: {self.stats['authors']['synced']} synced, "
              f"{self.stats['authors']['skipped']} skipped, "
              f"{self.stats['authors']['failed']} failed")

    def sync_commits(self):
        """Sync commits table with proper repository ID mapping."""
        print("\n" + "=" * 80)
        print("SYNCING COMMITS")
        print("=" * 80)

        commits = self.sqlite_session.query(Commit).all()
        self.stats['commits']['total'] = len(commits)

        print(f"\nFound {len(commits)} commits to sync")
        batch_size = 1000
        batch = []

        for i, commit in enumerate(commits, 1):
            try:
                # Check if already exists by hash and repository
                old_repo_id = commit.repository_id
                new_repo_id = self.id_mappings['repositories'].get(old_repo_id)

                if not new_repo_id:
                    self.stats['commits']['skipped'] += 1
                    continue

                existing = self.mariadb_session.query(Commit).filter(
                    Commit.hash == commit.hash,
                    Commit.repository_id == new_repo_id
                ).first()

                if existing:
                    self.id_mappings['commits'][commit.id] = existing.id
                    self.stats['commits']['skipped'] += 1
                    continue

                # Create new commit with mapped repository ID
                new_commit = Commit(
                    repository_id=new_repo_id,
                    hash=commit.hash,
                    author_name=commit.author_name,
                    author_email=commit.author_email,
                    commit_date=commit.commit_date,
                    message=commit.message,
                    branch=commit.branch,
                    files_changed=commit.files_changed,
                    lines_added=commit.lines_added,
                    lines_deleted=commit.lines_deleted,
                    chars_added=commit.chars_added,
                    chars_deleted=commit.chars_deleted,
                    file_types=commit.file_types
                )

                batch.append(new_commit)
                self.stats['commits']['synced'] += 1

                # Flush in batches
                if len(batch) >= batch_size:
                    self.mariadb_session.bulk_save_objects(batch)
                    self.mariadb_session.flush()

                    # Map IDs (note: bulk operations don't auto-populate IDs in the same way)
                    for obj in batch:
                        self.id_mappings['commits'][commit.id] = obj.id if hasattr(obj, 'id') else None

                    batch = []
                    print(f"  [PROGRESS] Synced {i}/{len(commits)} commits")

            except Exception as e:
                self.stats['commits']['failed'] += 1
                print(f"  [ERROR] Failed to sync commit '{commit.hash[:8]}': {str(e)}")

        # Save remaining batch
        if batch:
            self.mariadb_session.bulk_save_objects(batch)

        self.mariadb_session.commit()
        print(f"\nCommits: {self.stats['commits']['synced']} synced, "
              f"{self.stats['commits']['skipped']} skipped, "
              f"{self.stats['commits']['failed']} failed")

    def sync_pull_requests(self):
        """Sync pull requests table with proper repository ID mapping."""
        print("\n" + "=" * 80)
        print("SYNCING PULL REQUESTS")
        print("=" * 80)

        prs = self.sqlite_session.query(PullRequest).all()
        self.stats['pull_requests']['total'] = len(prs)

        print(f"\nFound {len(prs)} pull requests to sync")

        for pr in prs:
            try:
                # Map repository ID
                old_repo_id = pr.repository_id
                new_repo_id = self.id_mappings['repositories'].get(old_repo_id)

                if not new_repo_id:
                    self.stats['pull_requests']['skipped'] += 1
                    continue

                # Check if already exists
                existing = self.mariadb_session.query(PullRequest).filter(
                    PullRequest.pr_id == pr.pr_id,
                    PullRequest.repository_id == new_repo_id
                ).first()

                if existing:
                    self.id_mappings['pull_requests'][pr.id] = existing.id
                    self.stats['pull_requests']['skipped'] += 1
                    continue

                # Create new PR
                new_pr = PullRequest(
                    repository_id=new_repo_id,
                    pr_id=pr.pr_id,
                    title=pr.title,
                    description=pr.description,
                    author_name=pr.author_name,
                    author_email=pr.author_email,
                    created_date=pr.created_date,
                    updated_date=pr.updated_date,
                    state=pr.state,
                    from_branch=pr.from_branch,
                    to_branch=pr.to_branch,
                    commits_count=pr.commits_count
                )

                self.mariadb_session.add(new_pr)
                self.mariadb_session.flush()

                self.id_mappings['pull_requests'][pr.id] = new_pr.id
                self.stats['pull_requests']['synced'] += 1

            except Exception as e:
                self.stats['pull_requests']['failed'] += 1
                print(f"  [ERROR] Failed to sync PR #{pr.pr_id}: {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nPull Requests: {self.stats['pull_requests']['synced']} synced, "
              f"{self.stats['pull_requests']['skipped']} skipped, "
              f"{self.stats['pull_requests']['failed']} failed")

    def sync_pr_approvals(self):
        """Sync PR approvals with proper PR ID mapping."""
        print("\n" + "=" * 80)
        print("SYNCING PR APPROVALS")
        print("=" * 80)

        approvals = self.sqlite_session.query(PRApproval).all()
        self.stats['pr_approvals']['total'] = len(approvals)

        print(f"\nFound {len(approvals)} PR approvals to sync")

        for approval in approvals:
            try:
                # Map pull request ID
                old_pr_id = approval.pull_request_id
                new_pr_id = self.id_mappings['pull_requests'].get(old_pr_id)

                if not new_pr_id:
                    self.stats['pr_approvals']['skipped'] += 1
                    continue

                # Check if already exists
                existing = self.mariadb_session.query(PRApproval).filter(
                    PRApproval.pull_request_id == new_pr_id,
                    PRApproval.user_email == approval.user_email
                ).first()

                if existing:
                    self.stats['pr_approvals']['skipped'] += 1
                    continue

                # Create new approval
                new_approval = PRApproval(
                    pull_request_id=new_pr_id,
                    user_name=approval.user_name,
                    user_email=approval.user_email,
                    status=approval.status,
                    approval_date=approval.approval_date
                )

                self.mariadb_session.add(new_approval)
                self.stats['pr_approvals']['synced'] += 1

            except Exception as e:
                self.stats['pr_approvals']['failed'] += 1
                print(f"  [ERROR] Failed to sync approval: {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nPR Approvals: {self.stats['pr_approvals']['synced']} synced, "
              f"{self.stats['pr_approvals']['skipped']} skipped, "
              f"{self.stats['pr_approvals']['failed']} failed")

    def sync_staff_details(self):
        """Sync staff details table."""
        print("\n" + "=" * 80)
        print("SYNCING STAFF DETAILS")
        print("=" * 80)

        staff = self.sqlite_session.query(StaffDetails).all()
        self.stats['staff_details']['total'] = len(staff)

        print(f"\nFound {len(staff)} staff records to sync")

        for s in staff:
            try:
                # Check if already exists by bank_id_1
                existing = self.mariadb_session.query(StaffDetails).filter(
                    StaffDetails.bank_id_1 == s.bank_id_1
                ).first()

                if existing:
                    self.stats['staff_details']['skipped'] += 1
                    continue

                # Create new staff record
                new_staff = StaffDetails(
                    bank_id_1=s.bank_id_1,
                    staff_id=s.staff_id,
                    staff_name=s.staff_name,
                    email_address=s.email_address,
                    tech_unit=s.tech_unit,
                    platform_name=s.platform_name,
                    staff_type=s.staff_type,
                    original_staff_type=s.original_staff_type,
                    staff_status=s.staff_status,
                    work_location=s.work_location,
                    rank=s.rank,
                    staff_level=s.staff_level,
                    hr_role=s.hr_role,
                    job_function=s.job_function,
                    department_id=s.department_id,
                    company_name=s.company_name,
                    sub_platform=s.sub_platform,
                    staff_grouping=s.staff_grouping,
                    reporting_manager_name=s.reporting_manager_name,
                    staff_pc_code=s.staff_pc_code,
                    default_role=s.default_role
                )

                self.mariadb_session.add(new_staff)
                self.stats['staff_details']['synced'] += 1

            except Exception as e:
                self.stats['staff_details']['failed'] += 1
                print(f"  [ERROR] Failed to sync staff '{s.staff_name}': {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nStaff Details: {self.stats['staff_details']['synced']} synced, "
              f"{self.stats['staff_details']['skipped']} skipped, "
              f"{self.stats['staff_details']['failed']} failed")

    def sync_author_mappings(self):
        """Sync author-staff mappings."""
        print("\n" + "=" * 80)
        print("SYNCING AUTHOR-STAFF MAPPINGS")
        print("=" * 80)

        mappings = self.sqlite_session.query(AuthorStaffMapping).all()
        self.stats['author_mappings']['total'] = len(mappings)

        print(f"\nFound {len(mappings)} author mappings to sync")

        for mapping in mappings:
            try:
                # Check if already exists
                existing = self.mariadb_session.query(AuthorStaffMapping).filter(
                    AuthorStaffMapping.author_name == mapping.author_name,
                    AuthorStaffMapping.bank_id_1 == mapping.bank_id_1
                ).first()

                if existing:
                    self.stats['author_mappings']['skipped'] += 1
                    continue

                # Create new mapping
                new_mapping = AuthorStaffMapping(
                    author_name=mapping.author_name,
                    author_email=mapping.author_email,
                    bank_id_1=mapping.bank_id_1,
                    staff_name=mapping.staff_name,
                    confidence_score=mapping.confidence_score,
                    match_method=mapping.match_method,
                    created_at=mapping.created_at,
                    updated_at=mapping.updated_at
                )

                self.mariadb_session.add(new_mapping)
                self.stats['author_mappings']['synced'] += 1

            except Exception as e:
                self.stats['author_mappings']['failed'] += 1
                print(f"  [ERROR] Failed to sync mapping: {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nAuthor Mappings: {self.stats['author_mappings']['synced']} synced, "
              f"{self.stats['author_mappings']['skipped']} skipped, "
              f"{self.stats['author_mappings']['failed']} failed")

    def sync_staff_metrics(self):
        """Sync staff metrics."""
        print("\n" + "=" * 80)
        print("SYNCING STAFF METRICS")
        print("=" * 80)

        metrics = self.sqlite_session.query(StaffMetrics).all()
        self.stats['staff_metrics']['total'] = len(metrics)

        print(f"\nFound {len(metrics)} staff metrics to sync")

        for metric in metrics:
            try:
                # Check if already exists
                existing = self.mariadb_session.query(StaffMetrics).filter(
                    StaffMetrics.bank_id_1 == metric.bank_id_1
                ).first()

                if existing:
                    self.stats['staff_metrics']['skipped'] += 1
                    continue

                # Create new metric (copy all fields)
                new_metric = StaffMetrics(
                    bank_id_1=metric.bank_id_1,
                    staff_id=metric.staff_id,
                    staff_name=metric.staff_name,
                    email_address=metric.email_address,
                    tech_unit=metric.tech_unit,
                    platform_name=metric.platform_name,
                    staff_type=metric.staff_type,
                    original_staff_type=metric.original_staff_type,
                    staff_status=metric.staff_status,
                    work_location=metric.work_location,
                    rank=metric.rank,
                    staff_level=metric.staff_level,
                    hr_role=metric.hr_role,
                    job_function=metric.job_function,
                    department_id=metric.department_id,
                    company_name=metric.company_name,
                    sub_platform=metric.sub_platform,
                    staff_grouping=metric.staff_grouping,
                    reporting_manager_name=metric.reporting_manager_name,
                    total_commits=metric.total_commits,
                    total_lines_added=metric.total_lines_added,
                    total_lines_deleted=metric.total_lines_deleted,
                    total_files_changed=metric.total_files_changed,
                    total_chars_added=metric.total_chars_added,
                    total_chars_deleted=metric.total_chars_deleted,
                    total_prs_created=metric.total_prs_created,
                    total_prs_merged=metric.total_prs_merged,
                    total_pr_approvals_given=metric.total_pr_approvals_given,
                    repositories_touched=metric.repositories_touched,
                    repository_list=metric.repository_list,
                    first_commit_date=metric.first_commit_date,
                    last_commit_date=metric.last_commit_date,
                    first_pr_date=metric.first_pr_date,
                    last_pr_date=metric.last_pr_date,
                    file_types_worked=metric.file_types_worked,
                    primary_file_type=metric.primary_file_type,
                    last_calculated=metric.last_calculated,
                    calculation_version=metric.calculation_version,
                    avg_lines_per_commit=metric.avg_lines_per_commit,
                    avg_files_per_commit=metric.avg_files_per_commit,
                    code_churn_ratio=metric.code_churn_ratio
                )

                self.mariadb_session.add(new_metric)
                self.stats['staff_metrics']['synced'] += 1

            except Exception as e:
                self.stats['staff_metrics']['failed'] += 1
                print(f"  [ERROR] Failed to sync metrics for '{metric.staff_name}': {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nStaff Metrics: {self.stats['staff_metrics']['synced']} synced, "
              f"{self.stats['staff_metrics']['skipped']} skipped, "
              f"{self.stats['staff_metrics']['failed']} failed")

    def sync_current_year_metrics(self):
        """Sync current year staff metrics."""
        print("\n" + "=" * 80)
        print("SYNCING CURRENT YEAR STAFF METRICS")
        print("=" * 80)

        metrics = self.sqlite_session.query(CurrentYearStaffMetrics).all()
        self.stats['current_year_metrics']['total'] = len(metrics)

        print(f"\nFound {len(metrics)} current year metrics to sync")

        for metric in metrics:
            try:
                # Check if already exists
                existing = self.mariadb_session.query(CurrentYearStaffMetrics).filter(
                    CurrentYearStaffMetrics.bank_id_1 == metric.bank_id_1
                ).first()

                if existing:
                    self.stats['current_year_metrics']['skipped'] += 1
                    continue

                # Create new metric (copy all fields)
                new_metric = CurrentYearStaffMetrics(
                    bank_id_1=metric.bank_id_1,
                    staff_name=metric.staff_name,
                    staff_email=metric.staff_email,
                    staff_status=metric.staff_status,
                    staff_pc_code=metric.staff_pc_code,
                    default_role=metric.default_role,
                    current_year=metric.current_year,
                    cy_start_date=metric.cy_start_date,
                    cy_end_date=metric.cy_end_date,
                    cy_total_commits=metric.cy_total_commits,
                    cy_total_prs=metric.cy_total_prs,
                    cy_total_approvals_given=metric.cy_total_approvals_given,
                    cy_total_code_reviews_given=metric.cy_total_code_reviews_given,
                    cy_total_code_reviews_received=metric.cy_total_code_reviews_received,
                    cy_total_repositories=metric.cy_total_repositories,
                    cy_total_files_changed=metric.cy_total_files_changed,
                    cy_total_lines_changed=metric.cy_total_lines_changed,
                    cy_total_chars=metric.cy_total_chars,
                    cy_total_code_churn=metric.cy_total_code_churn,
                    cy_different_file_types=metric.cy_different_file_types,
                    cy_different_repositories=metric.cy_different_repositories,
                    cy_different_project_keys=metric.cy_different_project_keys,
                    cy_pct_code=metric.cy_pct_code,
                    cy_pct_config=metric.cy_pct_config,
                    cy_pct_documentation=metric.cy_pct_documentation,
                    cy_avg_commits_monthly=metric.cy_avg_commits_monthly,
                    cy_avg_prs_monthly=metric.cy_avg_prs_monthly,
                    cy_avg_approvals_monthly=metric.cy_avg_approvals_monthly,
                    cy_file_types_list=metric.cy_file_types_list,
                    cy_repositories_list=metric.cy_repositories_list,
                    cy_project_keys_list=metric.cy_project_keys_list,
                    last_calculated=metric.last_calculated,
                    calculation_version=metric.calculation_version
                )

                self.mariadb_session.add(new_metric)
                self.stats['current_year_metrics']['synced'] += 1

            except Exception as e:
                self.stats['current_year_metrics']['failed'] += 1
                print(f"  [ERROR] Failed to sync current year metrics for '{metric.staff_name}': {str(e)}")
                self.mariadb_session.rollback()

        self.mariadb_session.commit()
        print(f"\nCurrent Year Metrics: {self.stats['current_year_metrics']['synced']} synced, "
              f"{self.stats['current_year_metrics']['skipped']} skipped, "
              f"{self.stats['current_year_metrics']['failed']} failed")

    def save_id_mappings(self, filename='datasync/id_mappings.json'):
        """Save ID mappings to JSON file for reference."""
        print("\n" + "=" * 80)
        print("SAVING ID MAPPINGS")
        print("=" * 80)

        try:
            with open(filename, 'w') as f:
                json.dump(self.id_mappings, f, indent=2)
            print(f"\n[OK] ID mappings saved to {filename}")
        except Exception as e:
            print(f"\n[ERROR] Failed to save ID mappings: {str(e)}")

    def print_summary(self):
        """Print synchronization summary."""
        print("\n" + "=" * 80)
        print("SYNCHRONIZATION SUMMARY")
        print("=" * 80)

        for table, counts in self.stats.items():
            if counts['total'] > 0:
                print(f"\n{table.upper()}:")
                print(f"  Total:   {counts['total']}")
                print(f"  Synced:  {counts['synced']}")
                print(f"  Skipped: {counts['skipped']}")
                print(f"  Failed:  {counts['failed']}")

        total_synced = sum(c['synced'] for c in self.stats.values())
        total_failed = sum(c['failed'] for c in self.stats.values())

        print(f"\n{'=' * 80}")
        print(f"OVERALL: {total_synced} records synced, {total_failed} failed")
        print(f"{'=' * 80}")

    def run_full_sync(self):
        """Run complete synchronization process."""
        print("\n" + "=" * 80)
        print("STARTING FULL SYNCHRONIZATION")
        print("SQLite -> MariaDB/MySQL")
        print("=" * 80)
        print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Check target database
        if not self.check_target_tables():
            print("\n[ABORT] Cannot proceed without required tables")
            return False

        try:
            # Sync in order respecting foreign key dependencies
            self.sync_repositories()
            self.sync_authors()
            self.sync_commits()
            self.sync_pull_requests()
            self.sync_pr_approvals()
            self.sync_staff_details()
            self.sync_author_mappings()
            self.sync_staff_metrics()
            self.sync_current_year_metrics()

            # Save ID mappings
            self.save_id_mappings()

            # Print summary
            self.print_summary()

            print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n[SUCCESS] Full synchronization completed successfully!")

            return True

        except Exception as e:
            print(f"\n[ERROR] Synchronization failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.sqlite_session.close()
            self.mariadb_session.close()


def main():
    """Main entry point."""
    import os

    # SQLite source
    sqlite_url = "sqlite:///git_history.db"

    # MariaDB target - read from environment
    mariadb_url = os.getenv(
        'MARIADB_URL',
        'mysql+pymysql://user:password@localhost:3306/gpt'
    )

    print("\nData Synchronization Tool")
    print("=" * 80)
    print(f"Source (SQLite): {sqlite_url}")
    print(f"Target (MariaDB): {mariadb_url}")
    print("=" * 80)

    response = input("\nProceed with synchronization? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Synchronization cancelled.")
        return

    sync_manager = DataSyncManager(sqlite_url, mariadb_url)
    sync_manager.run_full_sync()


if __name__ == "__main__":
    main()
