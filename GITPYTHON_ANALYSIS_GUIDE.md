# GitPython-Based Analysis Guide

## Overview

The Git History Deep Analyzer uses **GitPython** to extract complete repository history including commits, pull requests, and approvals directly from Git commit history. This approach works with any Git platform (GitHub, Bitbucket, GitLab, etc.) without requiring API access.

## How It Works

### Commit Extraction
Uses GitPython to iterate through all commits and extract:
- Author information (name, email)
- Commit dates
- Commit messages
- Lines added/deleted/changed
- Files modified

### Pull Request Detection
Analyzes merge commits to identify PRs using pattern matching:

**Bitbucket Patterns**:
- `Merged in feature-branch (pull request #123)`
- `Pull request #123: Title`

**GitHub Patterns**:
- `Merge pull request #123 from user/branch`

**GitLab Patterns**:
- `Merge branch 'feature' into 'main'`

**Generic Patterns**:
- `PR #123` or `pr#123`

### Approval Extraction
Parses commit messages for approval indicators:

**Standard Git Trailers**:
- `Reviewed-by: Name <email>`
- `Approved-by: Name <email>`
- `Acked-by: Name <email>`
- `Tested-by: Name <email>`

**Platform-Specific**:
- `Reviewed by: @username` (GitHub)
- `Approved by: @username` (Bitbucket)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Only GitPython is required - no API keys needed!

### 2. Configure Environment

Edit `.env` file:

```ini
# Database Configuration
DB_TYPE=sqlite
SQLITE_DB_PATH=git_history.db

# Git Credentials (for cloning private repos)
GIT_USERNAME=your_git_username
GIT_PASSWORD=your_git_password_or_token

# Clone Directory
CLONE_DIR=./repositories
```

**Note**: Bitbucket configuration is optional and not used for Git-based analysis.

## Usage

### 1. Prepare CSV File

Create a CSV with your repositories:

```csv
Project Key,Slug Name,Clone URL (HTTP)
PROJ,my-repo,https://bitbucket.org/workspace/my-repo.git
TEAM,api,https://github.com/team/api.git
DEVOPS,infra,https://gitlab.com/devops/infra.git
```

### 2. Run Extraction

```bash
python cli.py repositories.csv
```

### 3. View Results

```bash
streamlit run dashboard.py
```

## Features

### Multi-Platform Support

| Platform | PR Detection | Approval Detection | Commit Analysis |
|----------|-------------|-------------------|-----------------|
| **Bitbucket** | ✅ Yes | ✅ Yes | ✅ Yes |
| **GitHub** | ✅ Yes | ✅ Yes | ✅ Yes |
| **GitLab** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Others** | ✅ Generic | ✅ Generic | ✅ Yes |

### What Gets Extracted

#### For All Platforms

**Commits** (100% accurate):
- ✅ Commit hash
- ✅ Author name and email
- ✅ Commit date
- ✅ Commit message
- ✅ Lines added/deleted
- ✅ Files changed
- ✅ Branch information

**Pull Requests** (from merge commits):
- ✅ PR number
- ✅ Title (from commit message)
- ✅ Description (full commit message)
- ✅ Author (from commit)
- ✅ Merge date
- ✅ Source/target branches (when available)
- ✅ Lines changed
- ✅ Commit count in PR

**Approvals** (from commit messages):
- ✅ Approver name
- ✅ Approver email
- ✅ Approval date (estimated from commit date)
- ✅ Approval type (reviewed-by, approved-by, etc.)

## Advantages of GitPython Approach

### 1. No API Required
- ✅ Works without API keys
- ✅ No rate limits
- ✅ No API setup needed
- ✅ Works with all Git platforms

### 2. Historical Data
- ✅ Complete Git history
- ✅ Works with old repositories
- ✅ No API availability issues
- ✅ Offline analysis possible

### 3. Simplicity
- ✅ Single dependency (GitPython)
- ✅ No authentication complexity
- ✅ Easy to set up
- ✅ Portable across platforms

### 4. Consistency
- ✅ Same analysis for all platforms
- ✅ Uniform data structure
- ✅ Predictable results

## Limitations and Considerations

### Pull Request Data

**What You Get**:
- ✅ Merged PRs (from merge commits)
- ✅ PR numbers (when in commit message)
- ✅ Merge dates
- ✅ Basic metadata

**What You Don't Get**:
- ❌ Open (unmerged) PRs
- ❌ Declined PRs
- ❌ PR discussions/comments
- ❌ Detailed PR metadata (unless in commit message)

### Approval Data

**What You Get**:
- ✅ Approvals documented in commit messages
- ✅ Standard Git trailers
- ✅ Manual approval notes

**What You Don't Get**:
- ❌ Web UI approval clicks (unless noted in commits)
- ❌ Approval timestamps (uses commit date as estimate)
- ❌ Approval states (approved vs changes requested)

### Workarounds

**For More Complete PR Data**:
1. Use consistent commit message formats
2. Include PR numbers in merge commits
3. Document approvals in commit messages
4. Use Git trailers (Reviewed-by, Approved-by)

**Example Good Practice**:
```
Merged in feature-xyz (pull request #123)

Add new dashboard widget

Reviewed-by: John Doe <john@example.com>
Approved-by: Jane Smith <jane@example.com>
```

## Best Practices

### 1. Commit Message Standards

Encourage your team to use structured commit messages:

```
PR #123: Short title

Longer description of changes.

Reviewed-by: Reviewer Name <reviewer@company.com>
Approved-by: Approver Name <approver@company.com>
```

### 2. Merge Commit Format

**Bitbucket** (automatic):
```
Merged in feature-branch (pull request #123)
```

**GitHub** (automatic):
```
Merge pull request #123 from user/feature-branch
```

**Manual** (if squashing):
```
PR #123: Feature title

Include PR number in title or body.
```

### 3. Approval Documentation

Add Git trailers to commits or merge commits:

```bash
git commit -m "Feature implementation

Reviewed-by: Alice <alice@company.com>
Approved-by: Bob <bob@company.com>"
```

### 4. Consistent Workflow

- ✅ Always include PR numbers in merge commits
- ✅ Use Git trailers for approvals
- ✅ Don't rewrite merge commit history
- ✅ Preserve merge commits (don't squash everything)

## Platform-Specific Notes

### Bitbucket

**Automatic Merge Commits**:
Bitbucket automatically creates merge commits with this format:
```
Merged in feature-branch (pull request #123)
```

**Detection**: ✅ Excellent - PR number and branch included

**Recommendations**:
- Keep default merge commit format
- Add approval trailers if needed
- Use descriptive branch names

### GitHub

**Automatic Merge Commits**:
GitHub creates merge commits like:
```
Merge pull request #123 from user/branch
```

**Detection**: ✅ Good - PR number and branch included

**Recommendations**:
- Avoid squash-and-merge if you want PR tracking
- Use merge commits or rebase-and-merge
- Enable merge commit messages

### GitLab

**Automatic Merge Commits**:
GitLab format:
```
Merge branch 'feature' into 'main'
```

**Detection**: ⚠️ Fair - No PR number by default

**Recommendations**:
- Include MR number in commit message
- Use merge request templates
- Add MR number to title

## Troubleshooting

### "No PRs found"

**Cause**: No merge commits or PR numbers not in commit messages

**Solution**:
1. Check if repository uses merge commits (not squash)
2. Look at a sample merge commit: `git log --merges -1`
3. Verify PR number is in commit message
4. Update team workflow to include PR numbers

### "No approvals found"

**Cause**: Approvals not documented in commit messages

**Solution**:
1. Check commit messages for approval patterns
2. Add Git trailers to commits
3. Update team workflow to document approvals
4. Example: `git commit --trailer "Reviewed-by: Name <email>"`

### "Wrong branch detected"

**Cause**: Branch names not in commit message

**Solution**:
1. Check merge commit message format
2. Ensure platform includes branch names in merges
3. May need to configure merge commit templates

### "Duplicate PRs"

**Cause**: Multiple merge commits for same PR

**Solution**:
- This is handled automatically
- Duplicate PR numbers are deduplicated
- Only first occurrence is stored

## Data Quality Tips

### To Maximize PR Detection:

1. **Use Merge Commits**: Don't squash all PRs
2. **Include PR Numbers**: In merge commit messages
3. **Consistent Format**: Follow platform conventions
4. **Branch Names**: Use descriptive names

### To Maximize Approval Detection:

1. **Git Trailers**: Use standard trailer format
2. **Document in Commits**: Add approval info to merge commits
3. **Consistent Names**: Use real names and emails
4. **Team Training**: Educate team on Git practices

### To Improve Data Accuracy:

1. **Don't Rewrite History**: Preserve merge commits
2. **Linear History**: Use rebase carefully
3. **Complete Messages**: Include all relevant info
4. **Regular Extraction**: Run analysis periodically

## Example Workflow

### Good Example

```bash
# Feature branch work
git checkout -b feature-xyz
git commit -m "Implement feature"

# Create PR (Bitbucket/GitHub web UI)

# Get review feedback, make changes
git commit -m "Address review comments"

# PR approved, merge
# Bitbucket creates: "Merged in feature-xyz (pull request #123)"
# or manually:
git checkout main
git merge --no-ff feature-xyz -m "Merged in feature-xyz (pull request #123)

Feature XYZ implementation

Reviewed-by: Alice Smith <alice@company.com>
Approved-by: Bob Jones <bob@company.com>"
```

### What Gets Extracted

```
PR #123:
- Title: "Merged in feature-xyz (pull request #123)"
- Author: Your Name
- Merged: 2024-01-15
- Branch: feature-xyz → main
- Approvals:
  - Alice Smith <alice@company.com>
  - Bob Jones <bob@company.com>
```

## Dashboard Integration

The extracted data appears in:

1. **Overview**: PR counts
2. **Authors Analytics**:
   - PRs Created (from PR author)
   - PRs Approved (from approval trailers)
3. **Detailed PRs View**: Full PR list with filters
4. **Top PR Approvers**: Based on extracted approvals

## Comparison with API Approach

| Aspect | GitPython | API-Based |
|--------|-----------|-----------|
| **Setup** | ✅ Simple | ⚠️ Complex |
| **Dependencies** | ✅ Minimal | ⚠️ Multiple |
| **Authentication** | ✅ Git only | ⚠️ API tokens |
| **Rate Limits** | ✅ None | ⚠️ Yes |
| **Historical Data** | ✅ Complete | ⚠️ May be limited |
| **Open PRs** | ❌ No | ✅ Yes |
| **Approval Detail** | ⚠️ If documented | ✅ Complete |
| **Platform Support** | ✅ All platforms | ⚠️ Platform-specific |

## Summary

The GitPython-based approach provides:
- ✅ **Universal support** for all Git platforms
- ✅ **No API complexity** or rate limits
- ✅ **Complete Git history** analysis
- ✅ **Simple setup** with minimal dependencies
- ⚠️ **Best-effort PR/approval extraction** based on commit messages

**Recommendation**: This approach is ideal for teams that:
- Use multiple Git platforms
- Want simple setup without API configuration
- Follow good Git commit message practices
- Need historical analysis
- Want to avoid API rate limits

For teams needing complete PR metadata (including open PRs, detailed approvals with timestamps, etc.), API integration would be needed, but GitPython provides excellent results for most use cases.
