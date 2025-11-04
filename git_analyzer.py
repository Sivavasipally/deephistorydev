"""Git repository analysis and data extraction."""

import os
import re
import shutil
import gc
from pathlib import Path
from git import Repo, GitCommandError
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from models import Repository, Commit, PullRequest, PRApproval


class GitAnalyzer:
    """Analyze Git repositories and extract commit and PR data."""

    def __init__(self, clone_dir, git_username=None, git_password=None):
        """Initialize GitAnalyzer.

        Args:
            clone_dir: Directory to clone repositories into
            git_username: Git username for authentication
            git_password: Git password or token for authentication
        """
        self.clone_dir = Path(clone_dir)
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        self.git_username = git_username
        self.git_password = git_password

    def _add_credentials_to_url(self, url):
        """Add credentials to clone URL if provided."""
        if not self.git_username or not self.git_password:
            return url

        parsed = urlparse(url)
        # Add credentials to netloc
        netloc_with_auth = f"{self.git_username}:{self.git_password}@{parsed.netloc}"
        # Reconstruct URL with credentials
        authenticated_url = urlunparse((
            parsed.scheme,
            netloc_with_auth,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return authenticated_url

    def clone_repository(self, clone_url, repo_name):
        """Clone a repository.

        Args:
            clone_url: URL to clone from
            repo_name: Name for the local repository directory

        Returns:
            Path to the cloned repository
        """
        repo_path = self.clone_dir / repo_name

        # Remove existing directory if it exists
        if repo_path.exists():
            self.cleanup_repository(repo_path)

        # Add credentials to URL
        auth_url = self._add_credentials_to_url(clone_url)

        # Clone the repository
        try:
            Repo.clone_from(auth_url, repo_path, branch='master')
        except GitCommandError:
            # Try with 'main' branch if 'master' doesn't exist
            try:
                Repo.clone_from(auth_url, repo_path, branch='main')
            except GitCommandError:
                # Clone without specifying branch
                Repo.clone_from(auth_url, repo_path)

        return repo_path

    def get_commit_stats(self, commit, repo):
        """Get statistics for a commit.

        Args:
            commit: Git commit object
            repo: Git repository object

        Returns:
            Dictionary with lines added, deleted, and files changed
        """
        try:
            stats = commit.stats.total
            return {
                'lines_added': stats.get('insertions', 0),
                'lines_deleted': stats.get('deletions', 0),
                'files_changed': stats.get('files', 0)
            }
        except Exception:
            return {
                'lines_added': 0,
                'lines_deleted': 0,
                'files_changed': 0
            }

    def extract_commits(self, repo_path, branch='master'):
        """Extract all commits from a repository branch.

        Args:
            repo_path: Path to the cloned repository
            branch: Branch to extract commits from

        Returns:
            List of commit dictionaries
        """
        repo = Repo(repo_path)
        commits_data = []

        try:
            # Try to get the specified branch, fall back to main or default
            try:
                commits = list(repo.iter_commits(branch))
            except GitCommandError:
                try:
                    commits = list(repo.iter_commits('main'))
                    branch = 'main'
                except GitCommandError:
                    # Use default branch
                    commits = list(repo.iter_commits())
                    branch = repo.active_branch.name

            for commit in commits:
                stats = self.get_commit_stats(commit, repo)

                commit_data = {
                    'commit_hash': commit.hexsha,
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'committer_name': commit.committer.name,
                    'committer_email': commit.committer.email,
                    'commit_date': datetime.fromtimestamp(commit.committed_date),
                    'message': commit.message.strip(),
                    'lines_added': stats['lines_added'],
                    'lines_deleted': stats['lines_deleted'],
                    'files_changed': stats['files_changed'],
                    'branch': branch
                }
                commits_data.append(commit_data)
        finally:
            # Close the repo to release file handles
            repo.close()

        return commits_data

    def extract_pull_requests(self, repo_path):
        """Extract pull request information from commit messages.

        Note: This extracts PR info from merge commits. For full PR data,
        you would need to use the Git platform's API (GitHub, GitLab, Bitbucket).

        Args:
            repo_path: Path to the cloned repository

        Returns:
            List of pull request dictionaries
        """
        repo = Repo(repo_path)
        prs_data = []
        pr_pattern = re.compile(r'Merge pull request #(\d+)', re.IGNORECASE)

        try:
            # Try master, then main, then default
            try:
                commits = list(repo.iter_commits('master'))
            except GitCommandError:
                try:
                    commits = list(repo.iter_commits('main'))
                except GitCommandError:
                    commits = list(repo.iter_commits())

            for commit in commits:
                # Look for merge commits
                if len(commit.parents) > 1:
                    match = pr_pattern.search(commit.message)
                    if match:
                        pr_number = int(match.group(1))
                        stats = self.get_commit_stats(commit, repo)

                        # Extract PR title from commit message
                        title_lines = commit.message.strip().split('\n')
                        title = title_lines[0] if title_lines else 'No title'

                        pr_data = {
                            'pr_number': pr_number,
                            'title': title,
                            'description': commit.message.strip(),
                            'author_name': commit.author.name,
                            'author_email': commit.author.email,
                            'created_date': datetime.fromtimestamp(commit.committed_date),
                            'merged_date': datetime.fromtimestamp(commit.committed_date),
                            'state': 'merged',
                            'source_branch': 'unknown',
                            'target_branch': 'master',
                            'lines_added': stats['lines_added'],
                            'lines_deleted': stats['lines_deleted'],
                            'commits_count': 1
                        }
                        prs_data.append(pr_data)
        finally:
            # Close the repo to release file handles
            repo.close()

        return prs_data

    def extract_pr_approvals(self, repo_path, pr_data):
        """Extract PR approval information.

        Note: Approval data is typically not available in Git history.
        This is a placeholder that would need API integration.

        Args:
            repo_path: Path to the cloned repository
            pr_data: Pull request data

        Returns:
            List of approval dictionaries
        """
        # Placeholder: In real implementation, this would use platform API
        # For now, we'll extract reviewers from commit messages if available
        approvals = []

        # Example pattern to look for: "Reviewed-by: Name <email>"
        reviewed_by_pattern = re.compile(r'Reviewed-by:\s*(.+?)\s*<(.+?)>', re.IGNORECASE)

        matches = reviewed_by_pattern.findall(pr_data.get('description', ''))
        for name, email in matches:
            approvals.append({
                'approver_name': name.strip(),
                'approver_email': email.strip(),
                'approval_date': pr_data.get('merged_date')
            })

        return approvals

    def cleanup_repository(self, repo_path):
        """Remove cloned repository to save space.

        Args:
            repo_path: Path to the repository to remove
        """
        if Path(repo_path).exists():
            # Force garbage collection to release file handles
            gc.collect()

            # Windows-specific: handle permission errors with retry
            def handle_remove_readonly(func, path, exc):
                """Error handler for Windows readonly files."""
                import stat
                import time
                if exc[0] == PermissionError:
                    # Remove readonly attribute and retry
                    os.chmod(path, stat.S_IWRITE)
                    time.sleep(0.1)  # Brief delay
                    try:
                        func(path)
                    except:
                        pass  # If still fails, ignore

            shutil.rmtree(repo_path, onerror=handle_remove_readonly)
