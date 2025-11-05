# Jira Ticket-Based PR Detection

## Problem Identified

Your Bitbucket repository's merge commits don't contain actual PR numbers. Instead, they look like this:

```
Merge branch 'master' of https://bitbucket... into feature/CG-25002
```

This is a **manual merge** that references a **Jira ticket** (`CG-25002`) in the branch name, but no Bitbucket PR number.

## Solution Implemented

I've enhanced the PR detection to extract Jira tickets from branch names and use them as PR identifiers.

### New Patterns Added

**File**: [git_analyzer.py](git_analyzer.py#L201-L206)

```python
# Branch-based patterns (extract ticket/PR number from branch name)
# Pattern: feature/PROJ-12345 or feature/CG-25002
(r'into\s+(?:feature|bugfix|hotfix)[/\-]([A-Z]+-\d+)', 'branch-ticket'),
(r'from\s+(?:feature|bugfix|hotfix)[/\-]([A-Z]+-\d+)', 'branch-ticket'),
# Pattern: Merge branch 'feature-123' or similar
(r'Merge branch.*?(?:feature|bugfix|hotfix)[/\-]?(\d{3,})', 'branch-number')
```

### How It Works

For your commit message:
```
Merge branch 'master' ... into feature/CG-25002
```

**Pattern matches**: `into feature/CG-25002`
**Extracted**: `CG-25002`
**PR Number**: `25002` (numeric part)
**PR Title**: `[CG-25002] Merge branch 'master'...`

## What Gets Extracted

### Your Example Commit

**Input**:
```
Hash: 15be4896
Message: Merge branch 'master' of https://bitbucket.sgp.dbs.com:8443/dsfit/git/scm/clicon-sg/user-sync-job into feature/CG-25002
```

**Extracted PR**:
- **PR Number**: 25002
- **Title**: `[CG-25002] Merge branch 'master' of https://bitbucket...`
- **Author**: Sai Teja Borra
- **Merged Date**: 2022-09-06
- **Source Branch**: feature/CG-25002
- **Target Branch**: master
- **Platform**: branch-ticket

### Supported Branch Patterns

The patterns will match:

✅ `into feature/CG-25002`
✅ `into feature/PROJ-1234`
✅ `into bugfix/BUG-5678`
✅ `into hotfix/HOT-9999`
✅ `from feature/TICKET-123`
✅ `feature-25002` (numeric only)
✅ `feature/25002` (numeric only)

❌ `feature` (no number)
❌ `test/my-branch` (no ticket format)

## Important Notes

### This is NOT the Same as Real PR Numbers

- **Jira Ticket**: `CG-25002` (project tracking)
- **Bitbucket PR**: `#123` (pull request ID)

We're using Jira tickets as **pseudo-PR identifiers** because your commits don't have actual PR numbers.

### Limitations

1. **Only works for feature branches** with Jira tickets in the name
2. **Manual merges without tickets** won't be detected
3. **Empty commit messages** (like your first 2 merge commits) won't be detected
4. **Same ticket merged multiple times** will show as 1 PR (first occurrence)

### What About Empty Commit Messages?

Your repository has 2 merge commits with **completely empty messages**:

```
Hash: 20b5752a
Full Commit Message: (empty)
```

These **cannot be detected** because there's no text to analyze. This is unusual and suggests:
- Manual merge with no message: `git merge --no-edit`
- Merge commit message was deleted
- Git configuration issue

## Testing the Fix

### Run Extraction Again

```bash
# Clean up old repository
rmdir /s /q repositories\CLICON-CORE_user-sync-job

# Re-run extraction
python cli.py your_repos.csv
```

### Expected Output

```
Extracting pull requests...
  Total commits: 129
  Merge commits: 3
  PRs detected: 1    ← Should now be 1 (was 0)
```

**Why only 1?**
- Merge commit #1: Empty message → No detection
- Merge commit #2: Empty message (not shown) → No detection
- Merge commit #3: Has `feature/CG-25002` → ✅ Detected!

### Verify in Dashboard

```bash
streamlit run dashboard.py
```

Check:
1. **Overview** → Total Pull Requests = 1
2. **Detailed PRs** → Shows PR #25002 with title `[CG-25002] Merge branch...`
3. **Authors Analytics** → Sai Teja Borra shows 1 PR created

## Better Solution for the Future

To get **better PR detection** and **all 3 merge commits** tracked:

### Option 1: Use Bitbucket Web UI for Merges

Instead of manual `git merge`, merge PRs through Bitbucket web interface:

1. Create PR in Bitbucket
2. Get reviews/approvals
3. Click "Merge" in Bitbucket UI
4. Bitbucket automatically creates commit message:
   ```
   Merged in feature/CG-25002 (pull request #123)

   CG-25002: Implement user sync feature
   ```

**Result**: Commit has both Jira ticket AND PR number!

### Option 2: Configure Bitbucket Commit Message Template

**Repository Settings** → **Default merge strategy**:
- Enable: "Include pull request ID in commit message"
- Template: `Merged in {branch} (pull request #{pr_id})`

### Option 3: Create Merge Script

Create a script to ensure consistent merge messages:

```bash
#!/bin/bash
# merge_with_ticket.sh

BRANCH=$1

if [ -z "$BRANCH" ]; then
    echo "Usage: merge_with_ticket.sh <branch>"
    exit 1
fi

# Extract ticket from branch name
TICKET=$(echo "$BRANCH" | grep -oE '[A-Z]+-[0-9]+')

if [ -z "$TICKET" ]; then
    echo "Error: No Jira ticket found in branch name"
    exit 1
fi

# Perform merge with proper message
git merge --no-ff "$BRANCH" -m "Merged in $BRANCH

$TICKET: Feature implementation from $BRANCH

Reviewed-by: YourName <your@email.com>"
```

Usage:
```bash
./merge_with_ticket.sh feature/CG-25002
```

### Option 4: Fix Empty Commit Messages

For commits with empty messages, you can rewrite history (dangerous!):

```bash
# DO NOT DO THIS if already pushed to shared repository!
git rebase -i HEAD~10  # Last 10 commits

# In editor, change "pick" to "reword" for empty commits
# Save and add proper messages
```

## Summary

### What Changed

✅ Added pattern to extract Jira tickets from branch names
✅ Uses ticket number (e.g., 25002 from CG-25002) as PR number
✅ Prepends full ticket to PR title for reference
✅ Works with manual merges that include branch names

### Current Status

**Your repository**: 3 merge commits
- ✅ 1 will be detected (has feature/CG-25002)
- ❌ 2 will not be detected (empty messages)

**Detection rate**: 33% (1 out of 3)

### To Improve Detection Rate

1. Use Bitbucket web UI for merges (→ 100% detection)
2. Configure merge commit templates (→ 100% detection)
3. Use merge scripts with proper messages (→ 100% detection)
4. Fix empty commit messages (if possible)

## Next Steps

1. **Test the fix**: Re-run extraction and verify 1 PR is detected
2. **Review PR in dashboard**: Check that CG-25002 shows correctly
3. **For future PRs**: Use Bitbucket web UI to merge
4. **For historical data**: Consider if you need 100% coverage:
   - If yes → Need Bitbucket API integration
   - If no → This solution is good enough (gets most PRs)

## Questions?

**Q: Can we detect PRs without any branch name or ticket?**
A: No. We need some identifier in the commit message. Empty messages have nothing to extract.

**Q: What about the other 2 empty merge commits?**
A: They cannot be detected without additional information. You could:
- Look up the commit hashes in Bitbucket web UI to find associated PRs
- Use Bitbucket API to match commits to PRs
- Accept that historical data is incomplete

**Q: Will this work for all future merges?**
A: Only if:
- Branches include Jira tickets (feature/TICKET-123)
- OR you start using Bitbucket web UI merges
- OR you add PR numbers manually to commit messages

The best solution is to enforce Bitbucket web UI merges going forward, which includes PR numbers automatically.
