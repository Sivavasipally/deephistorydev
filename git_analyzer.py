"""Git repository analysis and data extraction using GitPython."""

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
    """Analyze Git repositories and extract commit and PR data using GitPython."""

    def __init__(self, clone_dir, git_username=None, git_password=None, bitbucket_config=None):
        """Initialize GitAnalyzer.

        Args:
            clone_dir: Directory to clone repositories into
            git_username: Git username for authentication
            git_password: Git password or token for authentication
            bitbucket_config: Not used - kept for backward compatibility
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

    def extract_pull_requests(self, repo_path, clone_url=None):
        """Extract pull request information from Git history using GitPython.

        Supports multiple PR patterns:
        - GitHub: "Merge pull request #123"
        - Bitbucket: "Merged in feature-branch (pull request #123)"
        - GitLab: "Merge branch 'feature' into 'main'"

        Args:
            repo_path: Path to the cloned repository
            clone_url: Original clone URL (for platform detection)

        Returns:
            List of pull request dictionaries
        """
        repo = Repo(repo_path)
        prs_data = []

        # Multiple PR patterns for different platforms
        pr_patterns = [
            # GitHub pattern: Merge pull request #123 from user/branch
            (r'Merge pull request #(\d+)', 'github'),
            # Bitbucket pattern: Merged in feature-branch (pull request #123)
            (r'Merged in .+ \(pull request #(\d+)\)', 'bitbucket'),
            # Bitbucket alternate: Pull request #123: Title
            (r'Pull request #(\d+):', 'bitbucket'),
            # Generic pattern: PR #123 or pr#123
            (r'(?:PR|pr)\s*#(\d+)', 'generic')
        ]

        try:
            # Try master, then main, then default
            try:
                commits = list(repo.iter_commits('master'))
                default_branch = 'master'
            except GitCommandError:
                try:
                    commits = list(repo.iter_commits('main'))
                    default_branch = 'main'
                except GitCommandError:
                    commits = list(repo.iter_commits())
                    default_branch = repo.active_branch.name if hasattr(repo, 'active_branch') else 'unknown'

            processed_prs = set()  # Track processed PR numbers to avoid duplicates

            for commit in commits:
                # Look for merge commits (have multiple parents)
                if len(commit.parents) > 1:
                    commit_message = commit.message.strip()

                    # Try each pattern
                    for pattern, platform in pr_patterns:
                        match = re.search(pattern, commit_message, re.IGNORECASE)
                        if match:
                            pr_number = int(match.group(1))

                            # Skip if already processed
                            if pr_number in processed_prs:
                                continue

                            processed_prs.add(pr_number)
                            stats = self.get_commit_stats(commit, repo)

                            # Extract PR title
                            title_lines = commit_message.split('\n')
                            title = title_lines[0] if title_lines else 'No title'

                            # Try to extract branch names from commit message
                            source_branch, target_branch = self._extract_branch_names(
                                commit_message, default_branch
                            )

                            pr_data = {
                                'pr_number': pr_number,
                                'title': title,
                                'description': commit_message,
                                'author_name': commit.author.name,
                                'author_email': commit.author.email,
                                'created_date': datetime.fromtimestamp(commit.authored_date),
                                'merged_date': datetime.fromtimestamp(commit.committed_date),
                                'state': 'merged',
                                'source_branch': source_branch,
                                'target_branch': target_branch,
                                'lines_added': stats['lines_added'],
                                'lines_deleted': stats['lines_deleted'],
                                'commits_count': self._count_pr_commits(repo, commit),
                                'platform': platform
                            }
                            prs_data.append(pr_data)
                            break  # Found a match, no need to try other patterns

        finally:
            # Close the repo to release file handles
            repo.close()

        return prs_data

    def _extract_branch_names(self, commit_message, default_target='master'):
        """Extract source and target branch names from commit message.

        Args:
            commit_message: Full commit message
            default_target: Default target branch name

        Returns:
            Tuple of (source_branch, target_branch)
        """
        # Pattern: "Merged in branch-name (pull request #123)"
        bitbucket_pattern = r'Merged in ([^\s\(]+)'
        match = re.search(bitbucket_pattern, commit_message)
        if match:
            return match.group(1), default_target

        # Pattern: "Merge pull request #123 from user/branch-name"
        github_pattern = r'from [^/]+/([^\s]+)'
        match = re.search(github_pattern, commit_message)
        if match:
            return match.group(1), default_target

        # Pattern: "Merge branch 'source' into 'target'"
        gitlab_pattern = r"Merge branch '([^']+)' into '([^']+)'"
        match = re.search(gitlab_pattern, commit_message)
        if match:
            return match.group(1), match.group(2)

        return 'unknown', default_target

    def _count_pr_commits(self, repo, merge_commit):
        """Count commits in a PR by analyzing the merge commit.

        Args:
            repo: Git repository object
            merge_commit: The merge commit object

        Returns:
            Number of commits in the PR
        """
        try:
            # If it's a merge commit, count commits between first parent and second parent
            if len(merge_commit.parents) >= 2:
                # Get commits between main branch (first parent) and feature branch (second parent)
                first_parent = merge_commit.parents[0]
                second_parent = merge_commit.parents[1]

                # Count commits in second parent that aren't in first parent
                pr_commits = list(repo.iter_commits(f'{first_parent.hexsha}..{second_parent.hexsha}'))
                return len(pr_commits)
        except Exception:
            pass

        return 1  # Default to 1 if we can't determine

    def extract_pr_approvals(self, repo_path, pr_data, clone_url=None):
        """Extract PR approval information from Git commit messages using GitPython.

        Looks for approval patterns in commit messages:
        - "Reviewed-by: Name <email>"
        - "Approved-by: Name <email>"
        - "Acked-by: Name <email>"
        - Bitbucket: "approved by @username"
        - GitHub: "Reviewed by @username"

        Args:
            repo_path: Path to the cloned repository
            pr_data: Pull request data dictionary
            clone_url: Original clone URL (optional)

        Returns:
            List of approval dictionaries
        """
        approvals = []
        pr_description = pr_data.get('description', '')

        # Multiple approval patterns for different platforms
        approval_patterns = [
            # Standard Git trailer format
            (r'Reviewed-by:\s*([^<]+?)\s*<([^>]+)>', 'reviewed-by'),
            (r'Approved-by:\s*([^<]+?)\s*<([^>]+)>', 'approved-by'),
            (r'Acked-by:\s*([^<]+?)\s*<([^>]+)>', 'acked-by'),
            (r'Tested-by:\s*([^<]+?)\s*<([^>]+)>', 'tested-by'),
            # GitHub style
            (r'Reviewed by:\s*@?([^\s<]+)', 'github-review'),
            # Bitbucket style
            (r'[Aa]pproved by:\s*@?([^\s<]+)', 'bitbucket-approval'),
            (r'[Aa]pproved by\s+([^<]+?)\s*<([^>]+)>', 'bitbucket-approval-email'),
        ]

        # Extract approvals from PR description/commit message
        for pattern, approval_type in approval_patterns:
            matches = re.findall(pattern, pr_description, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        # Pattern with name and email
                        approver_name = match[0].strip()
                        approver_email = match[1].strip()
                    else:
                        # Pattern with username only
                        approver_name = match[0].strip()
                        approver_email = f"{approver_name}@git"
                else:
                    # Single match (username)
                    approver_name = match.strip()
                    approver_email = f"{approver_name}@git"

                # Avoid duplicates
                if not any(a['approver_email'] == approver_email for a in approvals):
                    approvals.append({
                        'approver_name': approver_name,
                        'approver_email': approver_email,
                        'approval_date': pr_data.get('merged_date'),
                        'approval_type': approval_type
                    })

        # Also check for approvals in PR commits (if we can find them)
        try:
            repo = Repo(repo_path)
            try:
                # Try to find approvals in commit messages of the PR
                # Look for commits near the merge commit time
                merge_date = pr_data.get('merged_date')
                if merge_date:
                    # Get commits around the merge time
                    all_commits = list(repo.iter_commits(max_count=100))
                    for commit in all_commits:
                        commit_date = datetime.fromtimestamp(commit.committed_date)
                        # Look at commits within a week of merge
                        if abs((commit_date - merge_date).days) <= 7:
                            commit_msg = commit.message.strip()
                            # Check for approval patterns in this commit
                            for pattern, approval_type in approval_patterns:
                                matches = re.findall(pattern, commit_msg, re.MULTILINE | re.IGNORECASE)
                                for match in matches:
                                    if isinstance(match, tuple) and len(match) >= 2:
                                        approver_name = match[0].strip()
                                        approver_email = match[1].strip()

                                        # Avoid duplicates
                                        if not any(a['approver_email'] == approver_email for a in approvals):
                                            approvals.append({
                                                'approver_name': approver_name,
                                                'approver_email': approver_email,
                                                'approval_date': commit_date,
                                                'approval_type': approval_type
                                            })
            finally:
                repo.close()
        except Exception:
            pass  # If we can't access repo, just use what we have

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
