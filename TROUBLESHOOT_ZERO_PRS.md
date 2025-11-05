# Troubleshooting: Zero PRs Detected

## Problem

You see this output when running extraction:

```
Extracting pull requests...
  Total commits: 129
  Merge commits: 3
  PRs detected: 0
```

This means the repository has merge commits but none matched our PR detection patterns.

## Root Cause

The merge commit messages in your Bitbucket repository don't contain PR numbers in a format we recognize, OR they don't contain PR numbers at all.

## Diagnosis Steps

### Step 1: Run with Enhanced Debug Output

The latest version of the code will now show you the actual merge commit messages:

```bash
python cli.py your_repos.csv
```

Look for output like:

```
[WARNING] Merge commits found but no PR patterns matched!
Sample merge commit messages (first 100 chars):
  1. Merge branch 'feature-xyz' into 'master'
  2. Merge branch 'develop'
  3. merged from dev branch
```

### Step 2: Extract Full Merge Commit Messages

Run the extraction with `--no-cleanup` to keep the cloned repository:

```bash
python cli.py your_repos.csv --no-cleanup
```

Then use the helper script to see full merge commit messages:

```bash
python show_merge_commits.py ./repositories/PROJ_your-repo
```

This will show the complete commit messages.

### Step 3: Analyze the Pattern

Look at the merge commit messages and answer:

**Question 1**: Do they contain PR numbers at all?
- ✅ Yes → Go to Question 2
- ❌ No → See Solution 1 below

**Question 2**: What format do they use?
Examples:
- `Merged in branch-name (pull request #123)` ← Bitbucket default
- `Merge pull request #123 from user/branch` ← GitHub
- `PR #123: Title` ← Manual reference
- `pull request #123` ← Somewhere in message
- `PR-123` or `PR 123` ← Different separator

**Question 3**: Are the merges done via Bitbucket web UI or manually?
- Web UI merges usually include PR numbers
- Manual `git merge` commands usually don't

## Solutions

### Solution 1: PR Numbers Not in Commits

**Cause**: Your team's workflow doesn't include PR numbers in merge commits.

**Fix Options**:

#### Option A: Configure Bitbucket (Recommended)

1. Go to Repository Settings → Default merge strategy
2. Enable: "Include pull request ID in commit message"
3. Choose merge strategy: "Merge commit" (not "Squash")
4. Save changes

From now on, all merged PRs will have the format:
```
Merged in branch-name (pull request #123)
```

#### Option B: Train Team to Add PR References

Ask developers to include PR numbers manually when merging:

```bash
git merge feature-branch -m "Merge feature-branch

Implements feature XYZ (PR #123)

Reviewed-by: Alice <alice@company.com>"
```

#### Option C: Use Bitbucket API (Alternative)

If you need historical data and can't change commit messages:
- We can add Bitbucket REST API integration
- Requires API token and permissions
- Can fetch all PRs including open/declined ones
- More complex setup

### Solution 2: Different Format Pattern

**Cause**: Your Bitbucket uses a different commit message format.

**Fix**: Share the actual merge commit messages with me, and I'll add the pattern.

**Current Patterns We Support**:
```python
pr_patterns = [
    r'Merge pull request #(\d+)'                    # GitHub
    r'Merged in .+ \(pull request #(\d+)\)'         # Bitbucket standard
    r'Pull request #(\d+):'                         # Bitbucket alternate
    r'(?:PR|pr|Pr|pR)\s*[:#]?\s*(\d+)'             # Generic (PR #123, pr:123, etc.)
    r'\(pull request #(\d+)\)'                      # Squash-merge
]
```

**Examples of formats we can add**:
```python
r'PR-(\d+)'                      # PR-123
r'pull-request/(\d+)'            # pull-request/123
r'#(\d+)'                        # Just #123 (risky - many false positives)
r'refs/pull-requests/(\d+)'     # Bitbucket refs format
```

### Solution 3: Manual Merges Without PR References

**Cause**: Developers are merging branches manually via command line without referencing PRs.

**Fix Options**:

#### Option A: Enforce Web UI Merges

Make it a team policy to only merge via Bitbucket web UI, which automatically includes PR numbers.

#### Option B: Create Merge Script

Create a script that ensures PR numbers are included:

```bash
#!/bin/bash
# merge_with_pr.sh

BRANCH=$1
PR_NUMBER=$2

if [ -z "$BRANCH" ] || [ -z "$PR_NUMBER" ]; then
    echo "Usage: merge_with_pr.sh <branch> <pr_number>"
    exit 1
fi

git merge --no-ff "$BRANCH" -m "Merged in $BRANCH (pull request #$PR_NUMBER)"
```

Usage:
```bash
./merge_with_pr.sh feature-xyz 123
```

## Testing the Fix

After implementing a solution:

### 1. Create a Test PR

1. Create a new branch: `git checkout -b test-pr-detection`
2. Make a small change: `echo "test" > test.txt`
3. Commit: `git commit -am "Test PR detection"`
4. Push and create PR in Bitbucket
5. Merge via web UI with PR number in message
6. Note the PR number

### 2. Re-run Extraction

```bash
# Delete old database to start fresh
rm git_history.db

# Run extraction
python cli.py your_repos.csv --no-cleanup
```

### 3. Verify

Check the output:
```
Extracting pull requests...
  Total commits: 130   ← +1 from before
  Merge commits: 4     ← +1 from before
  PRs detected: 1      ← Should be 1 now!
```

### 4. Check Dashboard

```bash
streamlit run dashboard.py
```

Verify:
- Overview → "Total Pull Requests" shows 1
- Detailed PRs → Your test PR appears in the list

## Common Bitbucket Formats

Different Bitbucket configurations produce different formats:

### Format 1: Default Bitbucket (Current)
```
Merged in feature-branch (pull request #123)

Feature description
```
**Status**: ✅ Supported by pattern `r'Merged in .+ \(pull request #(\d+)\)'`

### Format 2: Bitbucket Cloud with Custom Template
```
Pull request #123: Feature title

Merged feature-branch into master
```
**Status**: ✅ Supported by pattern `r'Pull request #(\d+):'`

### Format 3: Bitbucket Server/Data Center
```
Merge pull request #123 in PROJ/repo from feature to master

* commit 'abc123':
  Feature implementation
```
**Status**: ✅ Supported by pattern `r'Merge pull request #(\d+)'`

### Format 4: Squash Merge
```
feature-branch: Implement feature XYZ (pull request #123)

- Added feature X
- Updated feature Y
```
**Status**: ✅ Supported by pattern `r'\(pull request #(\d+)\)'`

### Format 5: Manual Merge (No PR Number)
```
Merge branch 'feature-branch'
```
**Status**: ❌ NOT supported (no PR number to extract)

### Format 6: Custom Format (Example)
```
[PR-123] Merge feature-branch
```
**Status**: ❌ NOT supported yet (can be added)

## Next Steps

1. **Run extraction again** to see the sample commit messages
2. **Share the output** with the sample messages
3. **I'll add the appropriate pattern** if needed
4. **Re-run extraction** to verify

## Quick Reference Commands

```bash
# Run extraction and see debug output
python cli.py repos.csv

# Run without cleanup to keep repository
python cli.py repos.csv --no-cleanup

# Show merge commit messages
python show_merge_commits.py ./repositories/PROJ_repo

# Check what's in the cloned repo
cd repositories/PROJ_repo
git log --merges -10 --oneline

# Full messages
git log --merges -5 --pretty=format:"%H%n%s%n%b%n---"

# Clean up
cd ../..
rm -rf repositories/PROJ_repo
```

## Contact

If none of the above helps, please share:

1. **Output from extraction** (with sample merge commit messages)
2. **Output from show_merge_commits.py**
3. **Screenshot of a merged PR in Bitbucket** (showing the commit)
4. **Bitbucket version** (Cloud, Server, or Data Center)

With this information, I can create the exact pattern needed for your repository.
