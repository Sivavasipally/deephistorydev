"""Staff metrics calculator - computes pre-aggregated metrics during extract phase."""

from sqlalchemy import func, extract
from datetime import datetime, date
from collections import Counter
from .models import (
    StaffMetrics, StaffDetails, AuthorStaffMapping,
    Commit, PullRequest, PRApproval, Repository,
    CurrentYearStaffMetrics
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
        """Calculate metrics for all active staff members (with or without mappings).

        Returns:
            dict: Summary of calculation results
        """
        print("[INFO] Calculating staff metrics...")

        # Get all active staff
        all_staff = self.session.query(StaffDetails).filter(
            StaffDetails.staff_status == 'Active'
        ).all()

        print(f"   Found {len(all_staff)} active staff members")

        # Get all mappings
        all_mappings = self.session.query(AuthorStaffMapping).all()

        # Group mappings by bank_id
        mapping_groups = {}
        for mapping in all_mappings:
            if mapping.bank_id_1:
                if mapping.bank_id_1 not in mapping_groups:
                    mapping_groups[mapping.bank_id_1] = []
                mapping_groups[mapping.bank_id_1].append(mapping)

        total_staff = len(all_staff)
        processed = 0
        updated = 0
        created = 0
        with_mappings = 0
        without_mappings = 0

        for staff in all_staff:
            bank_id = staff.bank_id_1
            try:
                # Get mappings for this staff member (if any)
                author_mappings = mapping_groups.get(bank_id, [])

                if author_mappings:
                    with_mappings += 1
                else:
                    without_mappings += 1

                result = self.calculate_staff_metrics(bank_id, author_mappings if author_mappings else None)
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
            'with_mappings': with_mappings,
            'without_mappings': without_mappings,
            'failed': total_staff - processed
        }

        print(f"\n[SUCCESS] Metrics calculation complete:")
        print(f"   - Processed: {processed}/{total_staff} active staff")
        print(f"   - With mappings: {with_mappings}")
        print(f"   - Without mappings: {without_mappings} (zero metrics)")
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
        # Get staff details first
        staff = self.session.query(StaffDetails).filter(
            StaffDetails.bank_id_1 == bank_id
        ).first()

        if not staff:
            print(f"   ⚠️  No staff details found for {bank_id}")
            return None

        # Get author mappings if not provided
        if author_mappings is None:
            author_mappings = self.session.query(AuthorStaffMapping).filter(
                AuthorStaffMapping.bank_id_1 == bank_id
            ).all()

        # Get all author names for this staff (empty list if no mappings - will result in zero metrics)
        author_names = [m.author_name for m in author_mappings] if author_mappings else []

        # Log if no mappings exist
        if not author_names:
            print(f"   ℹ️  No author mappings found for {bank_id} ({staff.staff_name}) - creating record with zero metrics")

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
        staff_metric.original_staff_type = staff.original_staff_type
        staff_metric.staff_status = staff.staff_status
        staff_metric.work_location = staff.work_location
        staff_metric.rank = staff.rank
        staff_metric.staff_level = staff.staff_level
        staff_metric.hr_role = staff.hr_role
        staff_metric.job_function = staff.job_function
        staff_metric.department_id = staff.department_id
        staff_metric.company_name = staff.company_name
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
        staff_metric.calculation_version = '2.0'

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

        # Now create/update the separate CurrentYearStaffMetrics record
        self._save_current_year_metrics(staff, author_names)

        return action

    def _save_current_year_metrics(self, staff, author_names):
        """Save current year metrics to separate table.

        Args:
            staff: StaffDetails object
            author_names: List of author names for this staff member
        """
        current_year = datetime.now().year
        cy_metrics = self._calculate_current_year_metrics(author_names, current_year)

        # Get or create CurrentYearStaffMetrics record
        cy_staff_metric = self.session.query(CurrentYearStaffMetrics).filter(
            CurrentYearStaffMetrics.bank_id_1 == staff.bank_id_1
        ).first()

        if not cy_staff_metric:
            cy_staff_metric = CurrentYearStaffMetrics(bank_id_1=staff.bank_id_1)
            self.session.add(cy_staff_metric)

        # Update staff identification
        cy_staff_metric.staff_name = staff.staff_name
        cy_staff_metric.staff_email = staff.email_address
        cy_staff_metric.staff_status = staff.staff_status
        cy_staff_metric.staff_pc_code = staff.staff_pc_code
        cy_staff_metric.default_role = staff.default_role

        # Update current year context
        cy_staff_metric.current_year = current_year
        cy_staff_metric.cy_start_date = cy_metrics['start_date']
        cy_staff_metric.cy_end_date = cy_metrics['end_date']

        # Update activity totals
        cy_staff_metric.cy_total_commits = cy_metrics['total_commits']
        cy_staff_metric.cy_total_prs = cy_metrics['total_prs']
        cy_staff_metric.cy_total_approvals_given = cy_metrics['total_approvals_given']
        cy_staff_metric.cy_total_code_reviews_given = cy_metrics['total_code_reviews_given']
        cy_staff_metric.cy_total_code_reviews_received = cy_metrics['total_code_reviews_received']
        cy_staff_metric.cy_total_repositories = cy_metrics['total_repositories']
        cy_staff_metric.cy_total_files_changed = cy_metrics['total_files_changed']
        cy_staff_metric.cy_total_lines_changed = cy_metrics['total_lines_changed']
        cy_staff_metric.cy_total_chars = cy_metrics['total_chars']
        cy_staff_metric.cy_total_code_churn = cy_metrics['total_code_churn']

        # Update diversity metrics
        cy_staff_metric.cy_different_file_types = cy_metrics['different_file_types']
        cy_staff_metric.cy_different_repositories = cy_metrics['different_repositories']
        cy_staff_metric.cy_different_project_keys = cy_metrics['different_project_keys']

        # Update file type distribution percentages
        cy_staff_metric.cy_pct_code = cy_metrics['pct_code']
        cy_staff_metric.cy_pct_config = cy_metrics['pct_config']
        cy_staff_metric.cy_pct_documentation = cy_metrics['pct_documentation']

        # Update monthly averages
        cy_staff_metric.cy_avg_commits_monthly = cy_metrics['avg_commits_monthly']
        cy_staff_metric.cy_avg_prs_monthly = cy_metrics['avg_prs_monthly']
        cy_staff_metric.cy_avg_approvals_monthly = cy_metrics['avg_approvals_monthly']

        # Update details lists
        cy_staff_metric.cy_file_types_list = cy_metrics['file_types_list']
        cy_staff_metric.cy_repositories_list = cy_metrics['repositories_list']
        cy_staff_metric.cy_project_keys_list = cy_metrics['project_keys_list']

        # Update metadata
        cy_staff_metric.last_calculated = datetime.utcnow()
        cy_staff_metric.calculation_version = '2.0'

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

    def _calculate_current_year_metrics(self, author_names, year):
        """Calculate metrics for the current year.

        Args:
            author_names: List of author names to aggregate
            year: Year to calculate metrics for

        Returns:
            dict: Current year metrics
        """
        from datetime import date
        from sqlalchemy import extract

        # Define current year date range
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Query commits in current year
        cy_commits = self.session.query(Commit).filter(
            Commit.author_name.in_(author_names),
            extract('year', Commit.commit_date) == year
        ).all()

        # Query PRs in current year
        cy_prs = self.session.query(PullRequest).filter(
            PullRequest.author_name.in_(author_names),
            extract('year', PullRequest.created_date) == year
        ).all()

        # Query approvals given in current year
        cy_approvals = self.session.query(PRApproval).filter(
            PRApproval.approver_name.in_(author_names),
            extract('year', PRApproval.approval_date) == year
        ).all()

        # Get unique PRs reviewed by this author (code reviews given)
        cy_pr_reviews_given = self.session.query(PRApproval.pull_request_id).filter(
            PRApproval.approver_name.in_(author_names),
            extract('year', PRApproval.approval_date) == year
        ).distinct().all()

        # Get code reviews received (approvals on own PRs)
        cy_pr_ids = [pr.id for pr in cy_prs]
        cy_reviews_received = 0
        if cy_pr_ids:
            cy_reviews_received = self.session.query(PRApproval).filter(
                PRApproval.pull_request_id.in_(cy_pr_ids)
            ).count()

        # Calculate commit metrics
        total_commits = len(cy_commits)
        total_files_changed = sum(c.files_changed or 0 for c in cy_commits)
        total_lines_added = sum(c.lines_added or 0 for c in cy_commits)
        total_lines_deleted = sum(c.lines_deleted or 0 for c in cy_commits)
        total_lines_changed = total_lines_added + total_lines_deleted
        total_chars = sum((c.chars_added or 0) + (c.chars_deleted or 0) for c in cy_commits)
        total_code_churn = total_lines_deleted

        # Get repository info
        repo_ids = set(c.repository_id for c in cy_commits if c.repository_id)
        repositories = self.session.query(Repository).filter(
            Repository.id.in_(repo_ids)
        ).all() if repo_ids else []

        repo_names = [r.slug_name for r in repositories]
        project_keys = list(set(r.project_key for r in repositories if r.project_key))

        # Get file types
        all_file_types = []
        for c in cy_commits:
            if c.file_types:
                all_file_types.extend([ft.strip() for ft in c.file_types.split(',') if ft.strip()])

        unique_file_types = list(set(all_file_types))

        # Calculate file type percentages
        total_file_count = len(all_file_types)
        pct_code = 0.0
        pct_config = 0.0
        pct_documentation = 0.0

        if total_file_count > 0:
            code_extensions = {'java', 'js', 'jsx', 'tsx', 'ts', 'py', 'sql', 'cpp', 'c', 'h', 'cs', 'rb', 'go', 'php', 'swift', 'kt', 'scala', 'r'}
            config_extensions = {'xml', 'json', 'yml', 'yaml', 'properties', 'config', 'conf', 'toml', 'ini', 'env', ''}
            doc_extensions = {'md', 'txt', 'rst', 'adoc', 'asciidoc'}

            code_count = sum(1 for ft in all_file_types if ft.lower() in code_extensions)
            config_count = sum(1 for ft in all_file_types if ft.lower() in config_extensions)
            doc_count = sum(1 for ft in all_file_types if ft.lower() in doc_extensions)

            pct_code = round((code_count / total_file_count) * 100, 2)
            pct_config = round((config_count / total_file_count) * 100, 2)
            pct_documentation = round((doc_count / total_file_count) * 100, 2)

        # Calculate monthly averages (assuming up to current month for current year)
        from datetime import datetime
        current_date = datetime.now()
        if year == current_date.year:
            months_elapsed = current_date.month
        else:
            months_elapsed = 12

        avg_commits_monthly = round(total_commits / months_elapsed, 2) if months_elapsed > 0 else 0.0
        avg_prs_monthly = round(len(cy_prs) / months_elapsed, 2) if months_elapsed > 0 else 0.0
        avg_approvals_monthly = round(len(cy_approvals) / months_elapsed, 2) if months_elapsed > 0 else 0.0

        return {
            'total_commits': total_commits,
            'total_prs': len(cy_prs),
            'total_approvals_given': len(cy_approvals),
            'total_code_reviews_given': len(cy_pr_reviews_given),
            'total_code_reviews_received': cy_reviews_received,
            'total_repositories': len(repo_names),
            'total_files_changed': total_files_changed,
            'total_lines_changed': total_lines_changed,
            'total_chars': total_chars,
            'total_code_churn': total_code_churn,
            'different_file_types': len(unique_file_types),
            'different_repositories': len(repo_names),
            'different_project_keys': len(project_keys),
            'pct_code': pct_code,
            'pct_config': pct_config,
            'pct_documentation': pct_documentation,
            'avg_commits_monthly': avg_commits_monthly,
            'avg_prs_monthly': avg_prs_monthly,
            'avg_approvals_monthly': avg_approvals_monthly,
            'file_types_list': ','.join(sorted(unique_file_types)),
            'repositories_list': ','.join(sorted(repo_names)),
            'project_keys_list': ','.join(sorted(project_keys)),
            'start_date': start_date,
            'end_date': end_date
        }

    def recalculate_after_mapping_change(self, bank_id):
        """Recalculate metrics for a staff member after mapping changes.

        Args:
            bank_id: Bank ID of the staff member

        Returns:
            bool: True if successful
        """
        print(f"[INFO] Recalculating metrics for {bank_id}...")
        try:
            self.calculate_staff_metrics(bank_id)
            self.session.commit()
            print(f"[SUCCESS] Metrics updated for {bank_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Error recalculating metrics for {bank_id}: {e}")
            self.session.rollback()
            return False
