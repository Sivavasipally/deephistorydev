"""Unified metrics calculator - calculates all pre-aggregated metrics tables.

This module orchestrates the calculation of all metric tables:
- CommitMetrics: Daily commit metrics by date/author/repository
- PRMetrics: Daily PR metrics by date/author/repository
- RepositoryMetrics: Repository-level aggregations
- AuthorMetrics: Author-level statistics (before staff mapping)
- TeamMetrics: Team/platform/tech unit aggregations
- DailyMetrics: Daily organization-wide metrics

Usage:
    from cli.unified_metrics_calculator import UnifiedMetricsCalculator

    calculator = UnifiedMetricsCalculator(session)
    summary = calculator.calculate_all_metrics()
"""

import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sqlalchemy import func, distinct, case
from sqlalchemy.orm import Session

from .models import (
    # Source tables
    Commit, PullRequest, PRApproval, Repository,
    StaffDetails, AuthorStaffMapping,
    # Metric tables
    CommitMetrics, PRMetrics, RepositoryMetrics,
    AuthorMetrics, TeamMetrics, DailyMetrics
)


class UnifiedMetricsCalculator:
    """Orchestrates calculation of all metric tables."""

    def __init__(self, session: Session):
        self.session = session
        self.version = "1.0"

    def calculate_all_metrics(self, force=False):
        """Calculate all metric tables.

        Args:
            force: If True, recalculate even if recently calculated

        Returns:
            dict: Summary of calculations for each metric type
        """
        print("\n" + "=" * 80)
        print("UNIFIED METRICS CALCULATION")
        print("=" * 80)

        summary = {}

        # Calculate staff metrics first (if staff data exists)
        print(f"\n{'-' * 80}")
        print(f"[INFO] Staff Metrics")
        print(f"{'-' * 80}")
        try:
            from .staff_metrics_calculator import StaffMetricsCalculator
            staff_calc = StaffMetricsCalculator(self.session)
            staff_result = staff_calc.calculate_all_staff_metrics()
            summary["Staff Metrics"] = staff_result
            print(f"   [SUCCESS] Staff Metrics: {staff_result.get('processed', 0)} records processed")
            if staff_result.get('created', 0) > 0:
                print(f"      - Created: {staff_result['created']}")
            if staff_result.get('updated', 0) > 0:
                print(f"      - Updated: {staff_result['updated']}")
        except Exception as e:
            print(f"   [WARNING] Staff Metrics: {e} (skipping - may need staff data imported first)")
            summary["Staff Metrics"] = {"error": str(e), "processed": 0}

        # Calculate in optimal order (dependencies first)
        calculators = [
            ("Author Metrics", self.calculate_author_metrics),
            ("Repository Metrics", self.calculate_repository_metrics),
            ("Commit Metrics", self.calculate_commit_metrics),
            ("PR Metrics", self.calculate_pr_metrics),
            ("Team Metrics", self.calculate_team_metrics),
            ("Daily Metrics", self.calculate_daily_metrics),
        ]

        for name, calculator_func in calculators:
            print(f"\n{'-' * 80}")
            print(f"[INFO] {name}")
            print(f"{'-' * 80}")

            try:
                result = calculator_func(force=force)
                summary[name] = result

                print(f"   [SUCCESS] {name}: {result.get('processed', 0)} records processed")
                if result.get('created', 0) > 0:
                    print(f"      - Created: {result['created']}")
                if result.get('updated', 0) > 0:
                    print(f"      - Updated: {result['updated']}")

            except Exception as e:
                print(f"   [ERROR] Error in {name}: {e}")
                import traceback
                traceback.print_exc()
                summary[name] = {"error": str(e), "processed": 0}

        print("\n" + "=" * 80)
        print("✅ METRICS CALCULATION COMPLETE")
        print("=" * 80)

        return summary

    def calculate_commit_metrics(self, force=False):
        """Calculate commit_metrics table (daily commit aggregations)."""
        print("   Aggregating commits by date/author/repository/branch...")

        # Query all commits grouped by dimensions
        query = self.session.query(
            func.date(Commit.commit_date).label('commit_date'),
            Commit.repository_id,
            Commit.author_email,
            Commit.author_name,
            Commit.branch,
            func.count(Commit.id).label('commit_count'),
            func.sum(Commit.lines_added).label('total_lines_added'),
            func.sum(Commit.lines_deleted).label('total_lines_deleted'),
            func.sum(Commit.files_changed).label('total_files_changed'),
            func.sum(Commit.chars_added).label('total_chars_added'),
            func.sum(Commit.chars_deleted).label('total_chars_deleted'),
        ).group_by(
            func.date(Commit.commit_date),
            Commit.repository_id,
            Commit.author_email,
            Commit.branch
        )

        results = query.all()

        created = 0
        updated = 0

        for row in results:
            # Check if record exists
            existing = self.session.query(CommitMetrics).filter_by(
                commit_date=row.commit_date,
                repository_id=row.repository_id,
                author_email=row.author_email,
                branch=row.branch or 'unknown'
            ).first()

            # Get file types for this group
            file_types = self._get_file_types_for_commits(
                row.commit_date, row.repository_id, row.author_email, row.branch
            )

            data = {
                'author_name': row.author_name,
                'commit_count': row.commit_count or 0,
                'total_lines_added': row.total_lines_added or 0,
                'total_lines_deleted': row.total_lines_deleted or 0,
                'total_files_changed': row.total_files_changed or 0,
                'total_chars_added': row.total_chars_added or 0,
                'total_chars_deleted': row.total_chars_deleted or 0,
                'file_types_json': json.dumps(file_types) if file_types else None,
                'last_calculated': datetime.utcnow(),
                'calculation_version': self.version
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                new_record = CommitMetrics(
                    commit_date=row.commit_date,
                    repository_id=row.repository_id,
                    author_email=row.author_email,
                    branch=row.branch or 'unknown',
                    **data
                )
                self.session.add(new_record)
                created += 1

        self.session.commit()

        return {
            'processed': len(results),
            'created': created,
            'updated': updated
        }

    def _get_file_types_for_commits(self, date, repo_id, author_email, branch):
        """Get file types breakdown for a commit group."""
        # This would require storing file-level data, which we don't have
        # For now, return empty dict
        return {}

    def calculate_pr_metrics(self, force=False):
        """Calculate pr_metrics table (daily PR aggregations)."""
        print("   Aggregating pull requests by date/author/repository/state...")

        query = self.session.query(
            func.date(PullRequest.created_date).label('pr_date'),
            PullRequest.repository_id,
            PullRequest.author_email,
            PullRequest.author_name,
            PullRequest.state,
            func.count(PullRequest.id).label('pr_count'),
            func.sum(PullRequest.lines_added).label('total_lines_added'),
            func.sum(PullRequest.lines_deleted).label('total_lines_deleted'),
            func.sum(PullRequest.commits_count).label('total_commits_in_prs'),
        ).group_by(
            func.date(PullRequest.created_date),
            PullRequest.repository_id,
            PullRequest.author_email,
            PullRequest.state
        )

        results = query.all()

        created = 0
        updated = 0

        for row in results:
            existing = self.session.query(PRMetrics).filter_by(
                pr_date=row.pr_date,
                repository_id=row.repository_id,
                author_email=row.author_email,
                state=row.state
            ).first()

            # Calculate state counts
            merged_count = row.pr_count if row.state == 'MERGED' else 0
            declined_count = row.pr_count if row.state == 'DECLINED' else 0
            open_count = row.pr_count if row.state == 'OPEN' else 0

            # Calculate avg time to merge for merged PRs
            avg_time_to_merge = self._calculate_avg_time_to_merge(
                row.pr_date, row.repository_id, row.author_email
            ) if row.state == 'MERGED' else 0.0

            # Count approvals
            total_approvals = self._count_pr_approvals(
                row.pr_date, row.repository_id, row.author_email
            )

            data = {
                'author_name': row.author_name,
                'pr_count': row.pr_count or 0,
                'merged_count': merged_count,
                'declined_count': declined_count,
                'open_count': open_count,
                'total_lines_added': row.total_lines_added or 0,
                'total_lines_deleted': row.total_lines_deleted or 0,
                'total_commits_in_prs': row.total_commits_in_prs or 0,
                'avg_time_to_merge_hours': avg_time_to_merge,
                'total_approvals_received': total_approvals,
                'last_calculated': datetime.utcnow(),
                'calculation_version': self.version
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                new_record = PRMetrics(
                    pr_date=row.pr_date,
                    repository_id=row.repository_id,
                    author_email=row.author_email,
                    state=row.state,
                    **data
                )
                self.session.add(new_record)
                created += 1

        self.session.commit()

        return {
            'processed': len(results),
            'created': created,
            'updated': updated
        }

    def _calculate_avg_time_to_merge(self, date, repo_id, author_email):
        """Calculate average time to merge for PRs."""
        prs = self.session.query(PullRequest).filter(
            func.date(PullRequest.created_date) == date,
            PullRequest.repository_id == repo_id,
            PullRequest.author_email == author_email,
            PullRequest.state == 'MERGED',
            PullRequest.merged_date.isnot(None)
        ).all()

        if not prs:
            return 0.0

        total_hours = 0
        count = 0

        for pr in prs:
            if pr.merged_date and pr.created_date:
                delta = pr.merged_date - pr.created_date
                total_hours += delta.total_seconds() / 3600
                count += 1

        return total_hours / count if count > 0 else 0.0

    def _count_pr_approvals(self, date, repo_id, author_email):
        """Count approvals for PRs created on date by author."""
        pr_ids = self.session.query(PullRequest.id).filter(
            func.date(PullRequest.created_date) == date,
            PullRequest.repository_id == repo_id,
            PullRequest.author_email == author_email
        ).all()

        pr_ids = [pr_id[0] for pr_id in pr_ids]

        if not pr_ids:
            return 0

        count = self.session.query(func.count(PRApproval.id)).filter(
            PRApproval.pull_request_id.in_(pr_ids)
        ).scalar()

        return count or 0

    def calculate_repository_metrics(self, force=False):
        """Calculate repository_metrics table."""
        print("   Calculating repository-level aggregations...")

        repositories = self.session.query(Repository).all()

        created = 0
        updated = 0

        for repo in repositories:
            existing = self.session.query(RepositoryMetrics).filter_by(
                repository_id=repo.id
            ).first()

            # Commit metrics
            commit_stats = self.session.query(
                func.count(Commit.id).label('total_commits'),
                func.count(distinct(Commit.author_email)).label('total_authors'),
                func.sum(Commit.lines_added).label('total_lines_added'),
                func.sum(Commit.lines_deleted).label('total_lines_deleted'),
                func.sum(Commit.files_changed).label('total_files_changed'),
                func.min(Commit.commit_date).label('first_commit_date'),
                func.max(Commit.commit_date).label('last_commit_date'),
            ).filter(Commit.repository_id == repo.id).first()

            # PR metrics
            pr_stats = self.session.query(
                func.count(PullRequest.id).label('total_prs'),
                func.sum(case((PullRequest.state == 'MERGED', 1), else_=0)).label('total_prs_merged'),
                func.sum(case((PullRequest.state == 'OPEN', 1), else_=0)).label('total_prs_open'),
                func.min(PullRequest.created_date).label('first_pr_date'),
                func.max(PullRequest.created_date).label('last_pr_date'),
            ).filter(PullRequest.repository_id == repo.id).first()

            total_commits = commit_stats.total_commits or 0
            total_prs = pr_stats.total_prs or 0
            total_prs_merged = pr_stats.total_prs_merged or 0

            merge_rate = (total_prs_merged / total_prs * 100) if total_prs > 0 else 0.0

            # Days since last commit
            days_since_last = 0
            is_active = False
            if commit_stats.last_commit_date:
                delta = datetime.utcnow() - commit_stats.last_commit_date
                days_since_last = delta.days
                is_active = days_since_last <= 90

            # Top contributors
            top_contributors = self._get_top_contributors(repo.id)

            # Branch count
            branch_count = self.session.query(
                func.count(distinct(Commit.branch))
            ).filter(Commit.repository_id == repo.id).scalar() or 0

            data = {
                'project_key': repo.project_key,
                'slug_name': repo.slug_name,
                'total_commits': total_commits,
                'total_authors': commit_stats.total_authors or 0,
                'total_lines_added': commit_stats.total_lines_added or 0,
                'total_lines_deleted': commit_stats.total_lines_deleted or 0,
                'total_files_changed': commit_stats.total_files_changed or 0,
                'total_prs': total_prs,
                'total_prs_merged': total_prs_merged,
                'total_prs_open': pr_stats.total_prs_open or 0,
                'merge_rate': merge_rate,
                'first_commit_date': commit_stats.first_commit_date,
                'last_commit_date': commit_stats.last_commit_date,
                'first_pr_date': pr_stats.first_pr_date,
                'last_pr_date': pr_stats.last_pr_date,
                'days_since_last_commit': days_since_last,
                'is_active': is_active,
                'top_contributors_json': json.dumps(top_contributors),
                'total_branches': branch_count,
                'last_calculated': datetime.utcnow(),
                'calculation_version': self.version
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                new_record = RepositoryMetrics(
                    repository_id=repo.id,
                    **data
                )
                self.session.add(new_record)
                created += 1

        self.session.commit()

        return {
            'processed': len(repositories),
            'created': created,
            'updated': updated
        }

    def _get_top_contributors(self, repo_id, limit=10):
        """Get top contributors for a repository."""
        results = self.session.query(
            Commit.author_name,
            Commit.author_email,
            func.count(Commit.id).label('commits')
        ).filter(
            Commit.repository_id == repo_id
        ).group_by(
            Commit.author_email
        ).order_by(
            func.count(Commit.id).desc()
        ).limit(limit).all()

        return [
            {'name': r.author_name, 'email': r.author_email, 'commits': r.commits}
            for r in results
        ]

    def calculate_author_metrics(self, force=False):
        """Calculate author_metrics table."""
        print("   Calculating author-level statistics...")

        # Get all unique authors from commits
        authors = self.session.query(
            Commit.author_email,
            func.max(Commit.author_name).label('author_name')
        ).group_by(Commit.author_email).all()

        created = 0
        updated = 0

        for author in authors:
            existing = self.session.query(AuthorMetrics).filter_by(
                author_email=author.author_email
            ).first()

            # Check staff mapping
            mapping = self.session.query(AuthorStaffMapping).filter_by(
                author_email=author.author_email
            ).first()

            bank_id_1 = mapping.bank_id_1 if mapping else None
            is_mapped = mapping is not None

            # Commit stats
            commit_stats = self.session.query(
                func.count(Commit.id).label('total_commits'),
                func.sum(Commit.lines_added).label('total_lines_added'),
                func.sum(Commit.lines_deleted).label('total_lines_deleted'),
                func.sum(Commit.files_changed).label('total_files_changed'),
                func.sum(Commit.chars_added).label('total_chars_added'),
                func.sum(Commit.chars_deleted).label('total_chars_deleted'),
                func.min(Commit.commit_date).label('first_commit_date'),
                func.max(Commit.commit_date).label('last_commit_date'),
                func.count(distinct(Commit.repository_id)).label('repositories_touched'),
            ).filter(Commit.author_email == author.author_email).first()

            # PR stats
            pr_stats = self.session.query(
                func.count(PullRequest.id).label('total_prs_created'),
                func.sum(case((PullRequest.state == 'MERGED', 1), else_=0)).label('total_prs_merged'),
                func.min(PullRequest.created_date).label('first_pr_date'),
                func.max(PullRequest.created_date).label('last_pr_date'),
            ).filter(PullRequest.author_email == author.author_email).first()

            # PR approvals given
            approvals_count = self.session.query(
                func.count(PRApproval.id)
            ).filter(PRApproval.approver_email == author.author_email).scalar() or 0

            # Repository list
            repo_names = self.session.query(Repository.slug_name).join(
                Commit, Commit.repository_id == Repository.id
            ).filter(
                Commit.author_email == author.author_email
            ).distinct().all()
            repo_list = ','.join([r.slug_name for r in repo_names])

            total_commits = commit_stats.total_commits or 0
            total_lines = (commit_stats.total_lines_added or 0) + (commit_stats.total_lines_deleted or 0)
            total_files = commit_stats.total_files_changed or 0

            avg_lines = total_lines / total_commits if total_commits > 0 else 0.0
            avg_files = total_files / total_commits if total_commits > 0 else 0.0
            churn_ratio = (commit_stats.total_lines_deleted or 0) / (commit_stats.total_lines_added or 1)

            data = {
                'author_name': author.author_name,
                'bank_id_1': bank_id_1,
                'is_mapped': is_mapped,
                'total_commits': total_commits,
                'total_lines_added': commit_stats.total_lines_added or 0,
                'total_lines_deleted': commit_stats.total_lines_deleted or 0,
                'total_files_changed': total_files,
                'total_chars_added': commit_stats.total_chars_added or 0,
                'total_chars_deleted': commit_stats.total_chars_deleted or 0,
                'total_prs_created': pr_stats.total_prs_created or 0,
                'total_prs_merged': pr_stats.total_prs_merged or 0,
                'total_pr_approvals_given': approvals_count,
                'repositories_touched': commit_stats.repositories_touched or 0,
                'repository_list': repo_list,
                'first_commit_date': commit_stats.first_commit_date,
                'last_commit_date': commit_stats.last_commit_date,
                'first_pr_date': pr_stats.first_pr_date,
                'last_pr_date': pr_stats.last_pr_date,
                'avg_lines_per_commit': avg_lines,
                'avg_files_per_commit': avg_files,
                'code_churn_ratio': churn_ratio,
                'last_calculated': datetime.utcnow(),
                'calculation_version': self.version
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                new_record = AuthorMetrics(
                    author_email=author.author_email,
                    **data
                )
                self.session.add(new_record)
                created += 1

        self.session.commit()

        return {
            'processed': len(authors),
            'created': created,
            'updated': updated
        }

    def calculate_team_metrics(self, force=False):
        """Calculate team_metrics table."""
        print("   Calculating team/platform/tech unit aggregations...")

        # Define aggregation dimensions
        dimensions = [
            ('tech_unit', 'tech_unit'),
            ('platform', 'platform_name'),
            ('rank', 'rank'),
            ('location', 'work_location'),
        ]

        created = 0
        updated = 0
        processed = 0

        for agg_level, field_name in dimensions:
            print(f"      Processing {agg_level}...")

            # Get unique values for this dimension
            values = self.session.query(
                getattr(StaffDetails, field_name)
            ).filter(
                getattr(StaffDetails, field_name).isnot(None),
                getattr(StaffDetails, field_name) != ''
            ).distinct().all()

            for (value,) in values:
                if not value:
                    continue

                # Calculate metrics for this team
                result = self._calculate_team_metric(agg_level, value, field_name, 'all_time')

                existing = self.session.query(TeamMetrics).filter_by(
                    aggregation_level=agg_level,
                    aggregation_value=value,
                    time_period='all_time'
                ).first()

                if existing:
                    for key, val in result.items():
                        setattr(existing, key, val)
                    updated += 1
                else:
                    new_record = TeamMetrics(
                        aggregation_level=agg_level,
                        aggregation_value=value,
                        time_period='all_time',
                        **result
                    )
                    self.session.add(new_record)
                    created += 1

                processed += 1

        self.session.commit()

        return {
            'processed': processed,
            'created': created,
            'updated': updated
        }

    def _calculate_team_metric(self, agg_level, agg_value, field_name, time_period):
        """Calculate metrics for a specific team."""
        from .staff_metrics_calculator import StaffMetricsCalculator
        from .models import StaffMetrics

        # Get staff in this team
        staff_list = self.session.query(StaffDetails).filter(
            getattr(StaffDetails, field_name) == agg_value
        ).all()

        total_staff = len(staff_list)
        bank_ids = [s.bank_id_1 for s in staff_list]

        # Get staff metrics for this team
        staff_metrics = self.session.query(StaffMetrics).filter(
            StaffMetrics.bank_id_1.in_(bank_ids)
        ).all()

        active_contributors = sum(1 for sm in staff_metrics if sm.total_commits > 0)
        active_rate = (active_contributors / total_staff * 100) if total_staff > 0 else 0.0

        total_commits = sum(sm.total_commits for sm in staff_metrics)
        total_lines_added = sum(sm.total_lines_added for sm in staff_metrics)
        total_lines_deleted = sum(sm.total_lines_deleted for sm in staff_metrics)
        total_files_changed = sum(sm.total_files_changed for sm in staff_metrics)
        total_prs_created = sum(sm.total_prs_created for sm in staff_metrics)
        total_prs_merged = sum(sm.total_prs_merged for sm in staff_metrics)
        total_pr_approvals = sum(sm.total_pr_approvals_given for sm in staff_metrics)

        merge_rate = (total_prs_merged / total_prs_created * 100) if total_prs_created > 0 else 0.0

        # Repository list
        all_repos = set()
        for sm in staff_metrics:
            if sm.repository_list:
                all_repos.update(sm.repository_list.split(','))

        # Top contributors
        top_contributors = sorted(
            [{'name': sm.staff_name, 'commits': sm.total_commits} for sm in staff_metrics],
            key=lambda x: x['commits'],
            reverse=True
        )[:10]

        return {
            'total_staff': total_staff,
            'active_contributors': active_contributors,
            'active_rate': active_rate,
            'total_commits': total_commits,
            'total_lines_added': total_lines_added,
            'total_lines_deleted': total_lines_deleted,
            'total_files_changed': total_files_changed,
            'total_prs_created': total_prs_created,
            'total_prs_merged': total_prs_merged,
            'total_pr_approvals': total_pr_approvals,
            'merge_rate': merge_rate,
            'repositories_touched': len(all_repos),
            'repository_list': ','.join(sorted(all_repos)),
            'avg_commits_per_person': total_commits / total_staff if total_staff > 0 else 0.0,
            'avg_prs_per_person': total_prs_created / total_staff if total_staff > 0 else 0.0,
            'avg_lines_per_person': (total_lines_added + total_lines_deleted) / total_staff if total_staff > 0 else 0.0,
            'top_contributors_json': json.dumps(top_contributors),
            'last_calculated': datetime.utcnow(),
            'calculation_version': self.version
        }

    def calculate_daily_metrics(self, force=False):
        """Calculate daily_metrics table."""
        print("   Calculating daily organization-wide metrics...")

        # Get date range from commits
        date_range = self.session.query(
            func.min(func.date(Commit.commit_date)).label('min_date'),
            func.max(func.date(Commit.commit_date)).label('max_date')
        ).first()

        if not date_range.min_date or not date_range.max_date:
            return {'processed': 0, 'created': 0, 'updated': 0}

        created = 0
        updated = 0

        # Iterate through each date
        current_date = date_range.min_date

        while current_date <= date_range.max_date:
            existing = self.session.query(DailyMetrics).filter_by(
                metric_date=current_date
            ).first()

            # Daily commit stats
            commit_stats = self.session.query(
                func.count(Commit.id).label('commits_today'),
                func.count(distinct(Commit.author_email)).label('authors_active'),
                func.sum(Commit.lines_added).label('lines_added'),
                func.sum(Commit.lines_deleted).label('lines_deleted'),
                func.sum(Commit.files_changed).label('files_changed'),
                func.count(distinct(Commit.repository_id)).label('repos_active')
            ).filter(
                func.date(Commit.commit_date) == current_date
            ).first()

            # Daily PR stats
            pr_stats = self.session.query(
                func.count(PullRequest.id).label('prs_created'),
            ).filter(
                func.date(PullRequest.created_date) == current_date
            ).first()

            prs_merged = self.session.query(
                func.count(PullRequest.id)
            ).filter(
                func.date(PullRequest.merged_date) == current_date
            ).scalar() or 0

            # PR approvals
            approvals = self.session.query(
                func.count(PRApproval.id)
            ).filter(
                func.date(PRApproval.approval_date) == current_date
            ).scalar() or 0

            # Cumulative stats
            cumulative_commits = self.session.query(
                func.count(Commit.id)
            ).filter(
                func.date(Commit.commit_date) <= current_date
            ).scalar() or 0

            cumulative_prs = self.session.query(
                func.count(PullRequest.id)
            ).filter(
                func.date(PullRequest.created_date) <= current_date
            ).scalar() or 0

            cumulative_authors = self.session.query(
                func.count(distinct(Commit.author_email))
            ).filter(
                func.date(Commit.commit_date) <= current_date
            ).scalar() or 0

            # Day of week
            day_of_week = current_date.strftime('%A')
            is_weekend = day_of_week in ['Saturday', 'Sunday']

            data = {
                'commits_today': commit_stats.commits_today or 0,
                'authors_active_today': commit_stats.authors_active or 0,
                'prs_created_today': pr_stats.prs_created or 0,
                'prs_merged_today': prs_merged,
                'pr_approvals_today': approvals,
                'lines_added_today': commit_stats.lines_added or 0,
                'lines_deleted_today': commit_stats.lines_deleted or 0,
                'files_changed_today': commit_stats.files_changed or 0,
                'repositories_active_today': commit_stats.repos_active or 0,
                'cumulative_commits': cumulative_commits,
                'cumulative_prs': cumulative_prs,
                'cumulative_authors': cumulative_authors,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'last_calculated': datetime.utcnow(),
                'calculation_version': self.version
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                new_record = DailyMetrics(
                    metric_date=current_date,
                    **data
                )
                self.session.add(new_record)
                created += 1

            current_date += timedelta(days=1)

        # Calculate moving averages
        self._calculate_moving_averages()

        self.session.commit()

        total_days = (date_range.max_date - date_range.min_date).days + 1

        return {
            'processed': total_days,
            'created': created,
            'updated': updated
        }

    def _calculate_moving_averages(self):
        """Calculate 7-day and 30-day moving averages for daily metrics."""
        all_metrics = self.session.query(DailyMetrics).order_by(DailyMetrics.metric_date).all()

        for i, metric in enumerate(all_metrics):
            # 7-day average
            start_idx = max(0, i - 6)
            recent_7 = all_metrics[start_idx:i+1]
            avg_7 = sum(m.commits_today for m in recent_7) / len(recent_7) if recent_7 else 0.0
            metric.commits_7day_avg = avg_7

            # 30-day average
            start_idx = max(0, i - 29)
            recent_30 = all_metrics[start_idx:i+1]
            avg_30 = sum(m.commits_today for m in recent_30) / len(recent_30) if recent_30 else 0.0
            metric.commits_30day_avg = avg_30
