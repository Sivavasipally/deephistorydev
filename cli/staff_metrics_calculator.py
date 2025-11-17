"""Staff metrics calculator - computes pre-aggregated metrics during extract phase."""

from sqlalchemy import func
from datetime import datetime
from collections import Counter
from .models import (
    StaffMetrics, StaffDetails, AuthorStaffMapping,
    Commit, PullRequest, PRApproval, Repository
)


class StaffMetricsCalculator:
    """Calculate and update pre-aggregated staff metrics."""

    def __init__(self, session):
        """Initialize calculator with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def calculate_all_staff_metrics(self):
        """Calculate metrics for all mapped staff members.

        Returns:
            dict: Summary of calculation results
        """
        print("🔄 Calculating staff metrics...")

        # Get all staff with mappings
        mappings = self.session.query(AuthorStaffMapping).all()

        # Group by bank_id
        bank_id_groups = {}
        for mapping in mappings:
            if mapping.bank_id_1:
                if mapping.bank_id_1 not in bank_id_groups:
                    bank_id_groups[mapping.bank_id_1] = []
                bank_id_groups[mapping.bank_id_1].append(mapping)

        total_staff = len(bank_id_groups)
        processed = 0
        updated = 0
        created = 0

        print(f"   Found {total_staff} unique staff members with mappings")

        for bank_id, author_mappings in bank_id_groups.items():
            try:
                result = self.calculate_staff_metrics(bank_id, author_mappings)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                processed += 1

                if processed % 10 == 0:
                    print(f"   Processed {processed}/{total_staff} staff members...")

            except Exception as e:
                print(f"   ⚠️  Error processing {bank_id}: {e}")
                continue

        # Commit all changes
        self.session.commit()

        summary = {
            'total_staff': total_staff,
            'processed': processed,
            'created': created,
            'updated': updated,
            'failed': total_staff - processed
        }

        print(f"\n✅ Metrics calculation complete:")
        print(f"   - Processed: {processed}/{total_staff}")
        print(f"   - Created: {created} new records")
        print(f"   - Updated: {updated} existing records")
        if summary['failed'] > 0:
            print(f"   - Failed: {summary['failed']}")

        return summary

    def calculate_staff_metrics(self, bank_id, author_mappings=None):
        """Calculate metrics for a single staff member.

        Args:
            bank_id: Bank ID of the staff member
            author_mappings: List of AuthorStaffMapping objects (optional, will query if not provided)

        Returns:
            str: 'created' or 'updated' indicating the action taken
        """
        # Get author mappings if not provided
        if author_mappings is None:
            author_mappings = self.session.query(AuthorStaffMapping).filter(
                AuthorStaffMapping.bank_id_1 == bank_id
            ).all()

        if not author_mappings:
            return None

        # Get staff details
        staff = self.session.query(StaffDetails).filter(
            StaffDetails.bank_id_1 == bank_id
        ).first()

        if not staff:
            print(f"   ⚠️  No staff details found for {bank_id}")
            return None

        # Get all author names for this staff
        author_names = [m.author_name for m in author_mappings]

        # Calculate commit metrics
        commit_metrics = self._calculate_commit_metrics(author_names)

        # Calculate PR metrics
        pr_metrics = self._calculate_pr_metrics(author_names)

        # Calculate approval metrics
        approval_metrics = self._calculate_approval_metrics(author_names)

        # Get or create StaffMetrics record
        staff_metric = self.session.query(StaffMetrics).filter(
            StaffMetrics.bank_id_1 == bank_id
        ).first()

        action = 'updated'
        if not staff_metric:
            staff_metric = StaffMetrics(bank_id_1=bank_id)
            self.session.add(staff_metric)
            action = 'created'

        # Update basic staff info
        staff_metric.staff_id = staff.staff_id
        staff_metric.staff_name = staff.staff_name
        staff_metric.email_address = staff.email_address

        # Update organizational fields
        staff_metric.tech_unit = staff.tech_unit
        staff_metric.platform_name = staff.platform_name
        staff_metric.staff_type = staff.staff_type
        staff_metric.staff_status = staff.staff_status
        staff_metric.work_location = staff.work_location
        staff_metric.rank = staff.rank
        staff_metric.sub_platform = staff.sub_platform
        staff_metric.staff_grouping = staff.staff_grouping
        staff_metric.reporting_manager_name = staff.reporting_manager_name

        # Update commit metrics
        staff_metric.total_commits = commit_metrics['total_commits']
        staff_metric.total_lines_added = commit_metrics['total_lines_added']
        staff_metric.total_lines_deleted = commit_metrics['total_lines_deleted']
        staff_metric.total_files_changed = commit_metrics['total_files_changed']
        staff_metric.total_chars_added = commit_metrics['total_chars_added']
        staff_metric.total_chars_deleted = commit_metrics['total_chars_deleted']

        # Update PR metrics
        staff_metric.total_prs_created = pr_metrics['total_prs']
        staff_metric.total_prs_merged = pr_metrics['total_merged']

        # Update approval metrics
        staff_metric.total_pr_approvals_given = approval_metrics['total_approvals']

        # Update repository metrics
        staff_metric.repositories_touched = commit_metrics['repositories_touched']
        staff_metric.repository_list = commit_metrics['repository_list']

        # Update activity timeline
        staff_metric.first_commit_date = commit_metrics['first_commit_date']
        staff_metric.last_commit_date = commit_metrics['last_commit_date']
        staff_metric.first_pr_date = pr_metrics['first_pr_date']
        staff_metric.last_pr_date = pr_metrics['last_pr_date']

        # Update technology insights
        staff_metric.file_types_worked = commit_metrics['file_types_worked']
        staff_metric.primary_file_type = commit_metrics['primary_file_type']

        # Update metadata
        staff_metric.last_calculated = datetime.utcnow()
        staff_metric.calculation_version = '1.0'

        # Calculate derived metrics
        if staff_metric.total_commits > 0:
            total_lines = staff_metric.total_lines_added + staff_metric.total_lines_deleted
            staff_metric.avg_lines_per_commit = round(total_lines / staff_metric.total_commits, 2)
            staff_metric.avg_files_per_commit = round(staff_metric.total_files_changed / staff_metric.total_commits, 2)
        else:
            staff_metric.avg_lines_per_commit = 0.0
            staff_metric.avg_files_per_commit = 0.0

        if staff_metric.total_lines_added > 0:
            staff_metric.code_churn_ratio = round(
                staff_metric.total_lines_deleted / staff_metric.total_lines_added, 3
            )
        else:
            staff_metric.code_churn_ratio = 0.0

        return action

    def _calculate_commit_metrics(self, author_names):
        """Calculate commit-related metrics for given authors.

        Args:
            author_names: List of author names to aggregate

        Returns:
            dict: Commit metrics
        """
        # Query all commits by these authors
        commits = self.session.query(Commit).filter(
            Commit.author_name.in_(author_names)
        ).all()

        if not commits:
            return {
                'total_commits': 0,
                'total_lines_added': 0,
                'total_lines_deleted': 0,
                'total_files_changed': 0,
                'total_chars_added': 0,
                'total_chars_deleted': 0,
                'repositories_touched': 0,
                'repository_list': '',
                'first_commit_date': None,
                'last_commit_date': None,
                'file_types_worked': '',
                'primary_file_type': ''
            }

        # Aggregate metrics
        total_lines_added = sum(c.lines_added or 0 for c in commits)
        total_lines_deleted = sum(c.lines_deleted or 0 for c in commits)
        total_files_changed = sum(c.files_changed or 0 for c in commits)
        total_chars_added = sum(c.chars_added or 0 for c in commits)
        total_chars_deleted = sum(c.chars_deleted or 0 for c in commits)

        # Get repository info
        repo_ids = set(c.repository_id for c in commits if c.repository_id)
        repositories = self.session.query(Repository).filter(
            Repository.id.in_(repo_ids)
        ).all()

        repo_names = [r.slug_name for r in repositories]

        # Get file types
        all_file_types = []
        for c in commits:
            if c.file_types:
                all_file_types.extend(c.file_types.split(','))

        # Count file type frequency
        file_type_counter = Counter(all_file_types)
        primary_file_type = file_type_counter.most_common(1)[0][0] if file_type_counter else ''
        unique_file_types = list(set(all_file_types))

        # Get date range
        commit_dates = [c.commit_date for c in commits if c.commit_date]
        first_commit_date = min(commit_dates) if commit_dates else None
        last_commit_date = max(commit_dates) if commit_dates else None

        return {
            'total_commits': len(commits),
            'total_lines_added': total_lines_added,
            'total_lines_deleted': total_lines_deleted,
            'total_files_changed': total_files_changed,
            'total_chars_added': total_chars_added,
            'total_chars_deleted': total_chars_deleted,
            'repositories_touched': len(repo_names),
            'repository_list': ','.join(repo_names),
            'first_commit_date': first_commit_date,
            'last_commit_date': last_commit_date,
            'file_types_worked': ','.join(unique_file_types),
            'primary_file_type': primary_file_type
        }

    def _calculate_pr_metrics(self, author_names):
        """Calculate PR-related metrics for given authors.

        Args:
            author_names: List of author names to aggregate

        Returns:
            dict: PR metrics
        """
        # Query all PRs by these authors
        prs = self.session.query(PullRequest).filter(
            PullRequest.author_name.in_(author_names)
        ).all()

        if not prs:
            return {
                'total_prs': 0,
                'total_merged': 0,
                'first_pr_date': None,
                'last_pr_date': None
            }

        # Count merged PRs
        merged_prs = [pr for pr in prs if pr.state == 'MERGED' or pr.merged_date is not None]

        # Get date range
        pr_dates = [pr.created_date for pr in prs if pr.created_date]
        first_pr_date = min(pr_dates) if pr_dates else None
        last_pr_date = max(pr_dates) if pr_dates else None

        return {
            'total_prs': len(prs),
            'total_merged': len(merged_prs),
            'first_pr_date': first_pr_date,
            'last_pr_date': last_pr_date
        }

    def _calculate_approval_metrics(self, author_names):
        """Calculate PR approval metrics for given authors.

        Args:
            author_names: List of author names to aggregate

        Returns:
            dict: Approval metrics
        """
        # Query all approvals given by these authors
        approvals = self.session.query(PRApproval).filter(
            PRApproval.approver_name.in_(author_names)
        ).all()

        return {
            'total_approvals': len(approvals)
        }

    def recalculate_after_mapping_change(self, bank_id):
        """Recalculate metrics for a staff member after mapping changes.

        Args:
            bank_id: Bank ID of the staff member

        Returns:
            bool: True if successful
        """
        print(f"🔄 Recalculating metrics for {bank_id}...")
        try:
            self.calculate_staff_metrics(bank_id)
            self.session.commit()
            print(f"✅ Metrics updated for {bank_id}")
            return True
        except Exception as e:
            print(f"❌ Error recalculating metrics for {bank_id}: {e}")
            self.session.rollback()
            return False
