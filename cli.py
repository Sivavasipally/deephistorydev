"""Command-line interface for Git history extraction."""

import sys
import csv
import click
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

from config import Config
from models import (
    get_engine, init_database, get_session,
    Repository, Commit, PullRequest, PRApproval
)
from git_analyzer import GitAnalyzer


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

    def process_repository(self, repo_info, session):
        """Process a single repository.

        Args:
            repo_info: Repository information dictionary
            session: Database session

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
            # Cleanup cloned repository
            click.echo("Cleaning up...")
            self.analyzer.cleanup_repository(repo_path)

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
                commits, prs, approvals = self.process_repository(repo_info, session)
                total_commits += commits
                total_prs += prs
                total_approvals += approvals

        finally:
            session.close()

        # Summary
        click.echo("\n" + "=" * 60)
        click.echo("Processing Complete!")
        click.echo("=" * 60)
        click.echo(f"Total repositories processed: {len(repositories)}")
        click.echo(f"Total commits extracted: {total_commits}")
        click.echo(f"Total pull requests extracted: {total_prs}")
        click.echo(f"Total approvals extracted: {total_approvals}")
        click.echo("=" * 60)


@click.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--no-cleanup', is_flag=True, help='Keep cloned repositories')
def main(csv_file, no_cleanup):
    """Extract Git history from repositories listed in CSV_FILE.

    The CSV file should contain columns:
    - Project Key
    - Slug Name
    - Clone URL (HTTP) / Self URL
    """
    cli = GitHistoryCLI()
    cli.run(csv_file, cleanup=not no_cleanup)


if __name__ == '__main__':
    main()
