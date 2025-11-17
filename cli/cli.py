"""Command-line interface for Git history extraction."""

import sys
import csv
import click
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

from .config import Config
from .models import (
    get_engine, init_database, get_session,
    Repository, Commit, PullRequest, PRApproval, StaffDetails, StaffMetrics
)
from .git_analyzer import GitAnalyzer
from .staff_metrics_calculator import StaffMetricsCalculator


class GitHistoryCLI:
    """CLI for extracting Git history from repositories."""

    def __init__(self):
        """Initialize CLI."""
        self.config = Config()
        self.db_config = self.config.get_db_config()
        self.engine = get_engine(self.db_config)
        self.credentials = self.config.get_git_credentials()
        self.bitbucket_config = self.config.get_bitbucket_config()
        self.clone_dir = self.config.get_clone_dir()

        # Initialize database
        init_database(self.engine)

        # Initialize Git analyzer with Bitbucket support
        self.analyzer = GitAnalyzer(
            self.clone_dir,
            self.credentials['username'],
            self.credentials['password'],
            self.bitbucket_config
        )

    def read_csv(self, csv_path):
        """Read repositories from CSV file.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of repository dictionaries
        """
        repositories = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Try different delimiters
            sample = f.read(1024)
            f.seek(0)

            # Detect delimiter
            sniffer = csv.Sniffer()
            try:
                delimiter = sniffer.sniff(sample).delimiter
            except:
                delimiter = ','

            reader = csv.DictReader(f, delimiter=delimiter)

            for row in reader:
                # Handle different possible column names
                project_key = (row.get('Project Key') or
                             row.get('project_key') or
                             row.get('ProjectKey') or '').strip()

                slug_name = (row.get('Slug Name') or
                           row.get('slug_name') or
                           row.get('SlugName') or '').strip()

                clone_url = (row.get('Clone URL (HTTP)') or
                           row.get('Self URL') or
                           row.get('clone_url') or
                           row.get('CloneURL') or '').strip()

                if project_key and clone_url:
                    repositories.append({
                        'project_key': project_key,
                        'slug_name': slug_name or project_key,
                        'clone_url': clone_url
                    })

        return repositories

    def process_repository(self, repo_info, session, cleanup=True):
        """Process a single repository.

        Args:
            repo_info: Repository information dictionary
            session: Database session
            cleanup: Whether to cleanup the cloned repository after processing

        Returns:
            Tuple of (commits_count, prs_count, approvals_count)
        """
        click.echo(f"\n{'='*60}")
        click.echo(f"Processing: {repo_info['project_key']} / {repo_info['slug_name']}")
        click.echo(f"{'='*60}")

        # Create or get repository record
        repo = session.query(Repository).filter_by(
            project_key=repo_info['project_key'],
            slug_name=repo_info['slug_name']
        ).first()

        if not repo:
            repo = Repository(
                project_key=repo_info['project_key'],
                slug_name=repo_info['slug_name'],
                clone_url=repo_info['clone_url']
            )
            session.add(repo)
            session.commit()
        else:
            click.echo("Repository already exists in database, updating data...")

        # Clone repository
        click.echo(f"Cloning repository from {repo_info['clone_url']}...")
        click.echo("Note: Large repositories may take several minutes to clone...")
        try:
            repo_path = self.analyzer.clone_repository(
                repo_info['clone_url'],
                f"{repo_info['project_key']}_{repo_info['slug_name']}"
            )
            click.echo(f"[OK] Repository cloned successfully")
        except KeyboardInterrupt:
            click.echo("\n[CANCELLED] Clone operation cancelled by user", err=True)
            return 0, 0, 0
        except Exception as e:
            click.echo(f"[ERROR] Failed to clone repository: {e}", err=True)
            click.echo("Tip: Very large repositories (like Linux kernel) may timeout or fail. Use smaller repos for testing.", err=True)
            return 0, 0, 0

        commits_count = 0
        prs_count = 0
        approvals_count = 0

        try:
            # Extract commits
            click.echo("Extracting commits...")
            commits_data = self.analyzer.extract_commits(repo_path)

            for commit_data in tqdm(commits_data, desc="Saving commits", unit="commit"):
                # Check if commit already exists
                existing_commit = session.query(Commit).filter_by(
                    commit_hash=commit_data['commit_hash']
                ).first()

                if not existing_commit:
                    commit = Commit(
                        repository_id=repo.id,
                        **commit_data
                    )
                    session.add(commit)
                    commits_count += 1

            session.commit()
            click.echo(f"[OK] Saved {commits_count} new commits")

            # Extract pull requests (passing clone URL for API detection)
            click.echo("Extracting pull requests...")
            prs_data = self.analyzer.extract_pull_requests(repo_path, repo_info['clone_url'])

            for pr_data in tqdm(prs_data, desc="Saving PRs", unit="PR"):
                # Check if PR already exists
                existing_pr = session.query(PullRequest).filter_by(
                    repository_id=repo.id,
                    pr_number=pr_data['pr_number']
                ).first()

                if not existing_pr:
                    pr = PullRequest(
                        repository_id=repo.id,
                        **pr_data
                    )
                    session.add(pr)
                    session.flush()  # Get the PR id

                    # Extract approvals (passing clone URL for API detection)
                    approvals_data = self.analyzer.extract_pr_approvals(
                        repo_path, pr_data, repo_info['clone_url']
                    )
                    for approval_data in approvals_data:
                        approval = PRApproval(
                            pull_request_id=pr.id,
                            **approval_data
                        )
                        session.add(approval)
                        approvals_count += 1

                    prs_count += 1

            session.commit()
            click.echo(f"[OK] Saved {prs_count} new pull requests")
            click.echo(f"[OK] Saved {approvals_count} new approvals")

        except Exception as e:
            click.echo(f"Error processing repository: {e}", err=True)
            session.rollback()
        finally:
            # Cleanup cloned repository if requested
            if cleanup:
                click.echo("Cleaning up...")
                self.analyzer.cleanup_repository(repo_path)
            else:
                click.echo(f"[KEPT] Repository retained at: {repo_path}")

        return commits_count, prs_count, approvals_count

    def run(self, csv_path, cleanup=True):
        """Run the CLI tool.

        Args:
            csv_path: Path to CSV file with repository information
            cleanup: Whether to cleanup cloned repositories after processing
        """
        click.echo("=" * 60)
        click.echo("Git History Extraction Tool")
        click.echo("=" * 60)
        click.echo(f"Database: {self.db_config['type']}")
        click.echo(f"CSV File: {csv_path}")
        click.echo("=" * 60)

        # Read CSV
        click.echo("\nReading CSV file...")
        try:
            repositories = self.read_csv(csv_path)
            click.echo(f"Found {len(repositories)} repositories to process")
        except Exception as e:
            click.echo(f"Error reading CSV file: {e}", err=True)
            sys.exit(1)

        if not repositories:
            click.echo("No repositories found in CSV file", err=True)
            sys.exit(1)

        # Process repositories
        session = get_session(self.engine)
        total_commits = 0
        total_prs = 0
        total_approvals = 0

        try:
            for repo_info in repositories:
                commits, prs, approvals = self.process_repository(repo_info, session, cleanup)
                total_commits += commits
                total_prs += prs
                total_approvals += approvals

        finally:
            session.close()

        # Calculate staff metrics after extraction
        click.echo("\n" + "=" * 60)
        click.echo("Calculating Staff Metrics...")
        click.echo("=" * 60)

        metrics_session = get_session(self.engine)
        try:
            calculator = StaffMetricsCalculator(metrics_session)
            metrics_summary = calculator.calculate_all_staff_metrics()
        finally:
            metrics_session.close()

        # Summary
        click.echo("\n" + "=" * 60)
        click.echo("Processing Complete!")
        click.echo("=" * 60)
        click.echo(f"Total repositories processed: {len(repositories)}")
        click.echo(f"Total commits extracted: {total_commits}")
        click.echo(f"Total pull requests extracted: {total_prs}")
        click.echo(f"Total approvals extracted: {total_approvals}")
        click.echo(f"Staff metrics calculated: {metrics_summary.get('processed', 0)}/{metrics_summary.get('total_staff', 0)}")
        click.echo("=" * 60)


@click.group()
def cli():
    """Git History Deep Analyzer - Extract and analyze Git repository data."""
    pass


@cli.command('extract')
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--no-cleanup', is_flag=True, help='Keep cloned repositories')
def extract_repos(csv_file, no_cleanup):
    """Extract Git history from repositories listed in CSV_FILE.

    The CSV file should contain columns:
    - Project Key
    - Slug Name
    - Clone URL (HTTP) / Self URL
    """
    git_cli = GitHistoryCLI()
    git_cli.run(csv_file, cleanup=not no_cleanup)


@cli.command('import-staff')
@click.argument('file_path', type=click.Path(exists=True))
def import_staff(file_path):
    """Import staff details from Excel or CSV file.

    The file should contain columns matching the staff details schema.
    Supports both .xlsx and .csv formats.
    """
    import pandas as pd
    from dateutil import parser

    click.echo("=" * 60)
    click.echo("Staff Details Import Tool")
    click.echo("=" * 60)

    # Initialize database
    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)
    init_database(engine)

    click.echo(f"Database: {db_config['type']}")
    click.echo(f"File: {file_path}")
    click.echo("=" * 60)

    # Detect file type and read
    file_path_obj = Path(file_path)
    file_ext = file_path_obj.suffix.lower()

    try:
        if file_ext in ['.xlsx', '.xls']:
            click.echo("\nReading Excel file...")
            df = pd.read_excel(file_path)
        elif file_ext == '.csv':
            click.echo("\nReading CSV file...")
            df = pd.read_csv(file_path)
        else:
            click.echo(f"Error: Unsupported file format '{file_ext}'. Use .xlsx or .csv", err=True)
            sys.exit(1)

        click.echo(f"Found {len(df)} rows")

        # Column mapping from Excel/CSV names to database field names
        column_mapping = {
            '1BankID': 'bank_id_1',
            'AS Of Date': 'as_of_date',
            'Reporting Period': 'reporting_period',
            'TechUnit': 'tech_unit',
            'Staff First Name': 'staff_first_name',
            'Staff Last Name': 'staff_last_name',
            'Staff Name': 'staff_name',
            'Staff Id': 'staff_id',
            'Citizenship': 'citizenship',
            'Original Staff Type': 'original_staff_type',
            'Staff Type': 'staff_type',
            'Staff Status': 'staff_status',
            'Sub Status': 'sub_status',
            'Movement Status': 'movement_status',
            'Rank': 'rank',
            'HR Role': 'hr_role',
            'Staff Start Date': 'staff_start_date',
            'Staff End Date': 'staff_end_date',
            'Reporting Manager 1BankID': 'reporting_manager_1bank_id',
            'Reporting Manager Staff Id': 'reporting_manager_staff_id',
            'Reporting Manager Name': 'reporting_manager_name',
            'Staff PCCode': 'staff_pc_code',
            'Work Type1': 'work_type1',
            'Work Type2': 'work_type2',
            'Reporting Location': 'reporting_location',
            'Work Location': 'work_location',
            'Primary Seating': 'primary_seating',
            'Company Name': 'company_name',
            'Company Short Name': 'company_short_name',
            'Last work day': 'last_work_day',
            'Department ID': 'department_id',
            'Gender': 'gender',
            'HC included': 'hc_included',
            'Reason for HC Included No': 'reason_for_hc_included_no',
            'Email Address': 'email_address',
            'Platform Index': 'platform_index',
            'Platform Lead': 'platform_lead',
            'Platform Name': 'platform_name',
            'Platform Unit': 'platform_unit',
            'Sub-platform': 'sub_platform',
            'Staff Grouping': 'staff_grouping',
            'Job Function': 'job_function',
            'Default Role': 'default_role',
            'Division': 'division',
            'Staff Level': 'staff_level',
            'People Cost Type': 'people_cost_type',
            'FTE': 'fte',
            'Effective Date': 'effective_date',
            'Created By': 'created_by',
            'Date Created': 'date_created',
            'Modified By': 'modified_by',
            'Date Modified': 'date_modified',
            'Movement Date': 'movement_date',
            'Reporting Manager PCcode': 'reporting_manager_pc_code',
            'Contract start date': 'contract_start_date',
            'Contract end date': 'contract_end_date',
            'Original Tenure Start Date': 'original_tenure_start_date',
            'Effective billing Date': 'effective_billing_date',
            'Billing PC Code': 'billing_pc_code',
            'Skill Set Type': 'skill_set_type',
            'PO Number': 'po_number',
            'MCR Number': 'mcr_number',
            'Assignment ID': 'assignment_id'
        }

        # Date columns that need parsing
        date_columns = [
            'as_of_date', 'staff_start_date', 'staff_end_date', 'last_work_day',
            'effective_date', 'date_created', 'date_modified', 'movement_date',
            'contract_start_date', 'contract_end_date', 'original_tenure_start_date',
            'effective_billing_date'
        ]

        # Rename columns to match database schema
        df_renamed = df.rename(columns=column_mapping)

        # Process data
        session = get_session(engine)
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        try:
            for idx, row in tqdm(df_renamed.iterrows(), total=len(df_renamed), desc="Importing staff", unit="record"):
                try:
                    # Prepare data dictionary
                    staff_data = {}

                    for col in df_renamed.columns:
                        if col in column_mapping.values():
                            value = row[col]

                            # Handle NaN/None values
                            if pd.isna(value):
                                staff_data[col] = None
                            # Handle date columns
                            elif col in date_columns:
                                try:
                                    if isinstance(value, str):
                                        staff_data[col] = parser.parse(value).date()
                                    elif hasattr(value, 'date'):
                                        staff_data[col] = value.date()
                                    else:
                                        staff_data[col] = value
                                except:
                                    staff_data[col] = None
                            # Handle FTE (float)
                            elif col == 'fte':
                                try:
                                    staff_data[col] = float(value) if value else None
                                except:
                                    staff_data[col] = None
                            # Handle datetime columns
                            elif col in ['date_created', 'date_modified']:
                                try:
                                    if isinstance(value, str):
                                        staff_data[col] = parser.parse(value)
                                    else:
                                        staff_data[col] = value
                                except:
                                    staff_data[col] = None
                            else:
                                staff_data[col] = str(value) if value else None

                    # Check if record exists (by staff_id)
                    staff_id = staff_data.get('staff_id')
                    if staff_id:
                        existing = session.query(StaffDetails).filter_by(staff_id=staff_id).first()

                        if existing:
                            # Update existing record
                            for key, value in staff_data.items():
                                setattr(existing, key, value)
                            updated_count += 1
                        else:
                            # Create new record
                            staff = StaffDetails(**staff_data)
                            session.add(staff)
                            imported_count += 1
                    else:
                        # No staff_id, still import but might be duplicate
                        staff = StaffDetails(**staff_data)
                        session.add(staff)
                        imported_count += 1

                    # Commit every 100 records
                    if (idx + 1) % 100 == 0:
                        session.commit()

                except Exception as e:
                    click.echo(f"\nWarning: Skipped row {idx + 1}: {e}")
                    skipped_count += 1
                    session.rollback()
                    continue

            # Final commit
            session.commit()

            click.echo("\n" + "=" * 60)
            click.echo("Import Complete!")
            click.echo("=" * 60)
            click.echo(f"New records imported: {imported_count}")
            click.echo(f"Records updated: {updated_count}")
            click.echo(f"Records skipped: {skipped_count}")
            click.echo(f"Total processed: {len(df_renamed)}")

        except Exception as e:
            click.echo(f"\nError during import: {e}", err=True)
            session.rollback()
            sys.exit(1)
        finally:
            session.close()

    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        sys.exit(1)


@cli.command('calculate-metrics')
@click.option('--all', 'calc_all', is_flag=True, help='Calculate all metric tables')
@click.option('--staff', is_flag=True, help='Calculate staff_metrics only')
@click.option('--commits', is_flag=True, help='Calculate commit_metrics only')
@click.option('--prs', is_flag=True, help='Calculate pr_metrics only')
@click.option('--repositories', is_flag=True, help='Calculate repository_metrics only')
@click.option('--authors', is_flag=True, help='Calculate author_metrics only')
@click.option('--teams', is_flag=True, help='Calculate team_metrics only')
@click.option('--daily', is_flag=True, help='Calculate daily_metrics only')
@click.option('--force', is_flag=True, help='Force recalculation (ignore timestamps)')
def calculate_metrics(calc_all, staff, commits, prs, repositories, authors, teams, daily, force):
    """Calculate pre-aggregated metrics for fast API queries.

    This command calculates and stores metrics in dedicated tables to avoid
    expensive real-time calculations. Metrics are automatically updated during
    extract, but this command allows manual recalculation.

    Examples:
        # Calculate all metrics
        python -m cli calculate-metrics --all

        # Calculate only staff metrics
        python -m cli calculate-metrics --staff

        # Calculate multiple specific metrics
        python -m cli calculate-metrics --commits --prs --repositories

        # Force recalculation of all metrics
        python -m cli calculate-metrics --all --force
    """
    from .unified_metrics_calculator import UnifiedMetricsCalculator

    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)
    session = get_session(engine)

    try:
        click.echo("\n" + "=" * 80)
        click.echo("METRICS CALCULATION")
        click.echo("=" * 80)

        calculator = UnifiedMetricsCalculator(session)

        # Determine what to calculate
        if calc_all or not any([staff, commits, prs, repositories, authors, teams, daily]):
            # Calculate all if --all or no specific flags
            click.echo("Calculating all metrics...")
            summary = calculator.calculate_all_metrics(force=force)

        else:
            # Calculate only selected metrics
            summary = {}

            if staff:
                click.echo("\n📊 Calculating Staff Metrics...")
                staff_calc = StaffMetricsCalculator(session)
                summary['Staff Metrics'] = staff_calc.calculate_all_staff_metrics()

            if authors:
                click.echo("\n👤 Calculating Author Metrics...")
                summary['Author Metrics'] = calculator.calculate_author_metrics(force=force)

            if repositories:
                click.echo("\n📦 Calculating Repository Metrics...")
                summary['Repository Metrics'] = calculator.calculate_repository_metrics(force=force)

            if commits:
                click.echo("\n💾 Calculating Commit Metrics...")
                summary['Commit Metrics'] = calculator.calculate_commit_metrics(force=force)

            if prs:
                click.echo("\n🔀 Calculating PR Metrics...")
                summary['PR Metrics'] = calculator.calculate_pr_metrics(force=force)

            if teams:
                click.echo("\n👥 Calculating Team Metrics...")
                summary['Team Metrics'] = calculator.calculate_team_metrics(force=force)

            if daily:
                click.echo("\n📅 Calculating Daily Metrics...")
                summary['Daily Metrics'] = calculator.calculate_daily_metrics(force=force)

        # Print summary
        click.echo("\n" + "=" * 80)
        click.echo("CALCULATION SUMMARY")
        click.echo("=" * 80)

        for metric_type, result in summary.items():
            if 'error' in result:
                click.echo(f"❌ {metric_type}: ERROR - {result['error']}")
            else:
                processed = result.get('processed', 0)
                created = result.get('created', 0)
                updated = result.get('updated', 0)
                click.echo(f"✅ {metric_type}: {processed} records processed ({created} created, {updated} updated)")

        click.echo("=" * 80)
        click.echo("\n✨ Metrics calculation complete!")
        click.echo("\nNext steps:")
        click.echo("  • Metrics are now available in the database")
        click.echo("  • Backend APIs will use pre-calculated data for fast queries")
        click.echo("  • Run 'python -m cli calculate-metrics --all' periodically to refresh")

    except Exception as e:
        click.echo(f"\n❌ Error during metrics calculation: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    cli()
