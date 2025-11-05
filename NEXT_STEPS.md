# Next Steps - Testing PR Detection Fix

## What Was Fixed

We've enhanced the PR and approval detection in `git_analyzer.py` to handle Bitbucket repositories better, especially those using squash-merge workflows.

### Key Changes:
1. **Squash-merge support** - Now detects PRs in non-merge commits
2. **More flexible patterns** - Detects various PR reference formats
3. **Better error handling** - Works with any branch name
4. **Debug output** - Shows what's being detected
5. **Enhanced approval patterns** - More ways to detect approvals

## How to Test

### Step 1: Re-run Extraction on Your Bitbucket Repository

```bash
# Make sure your .env file has correct credentials
python cli.py your_bitbucket_repos.csv
```

**Watch for the new debug output**:
```
Repository: PROJ/my-repo
Cloning...
[OK] Cloned successfully
Extracting commits...
Extracting pull requests...
  Total commits: 250        ← Total commits in the repository
  Merge commits: 75         ← Traditional merge commits found
  PRs detected: 68          ← PRs detected from patterns
```

### Step 2: Check the Numbers

**If "PRs detected" is now > 0**: Success! The fix worked.

**If "PRs detected" is still 0**, check:

1. **Are there commits?**
   - If "Total commits: 0" → Clone issue (check credentials)
   - If commits exist → Continue to step 2

2. **Run the diagnostic tool**:
   ```bash
   python diagnose_repo.py ./repositories/PROJ_your-repo
   ```

   This will show:
   - Actual commit messages
   - Which patterns match (or don't match)
   - Available branches
   - Sample merge commits

3. **Check actual commit format**:
   ```bash
   cd repositories/PROJ_your-repo
   git log --oneline | head -20
   ```

   Look for PR numbers in commit messages. Do you see patterns like:
   - `Merged in branch (pull request #123)`
   - `feature: description (pull request #123)`
   - `PR #123: Title`
   - `pr#123`

### Step 3: View Results in Dashboard

```bash
streamlit run dashboard.py
```

Navigate to:
1. **Overview** → Check "Total Pull Requests" count
2. **Detailed PRs** → View list of detected PRs
3. **Authors Analytics** → Check "PRs Created" and "PRs Approved" columns

### Step 4: Export and Verify Data

In the dashboard:
- Go to "Detailed PRs" page
- Click "Export to CSV"
- Open the CSV and verify PR data looks correct

## Expected Results

### If Your Team Uses Merge Commits

**Example commit message**:
```
Merged in feature-xyz (pull request #123)

Add new feature

Reviewed-by: Alice <alice@company.com>
```

**Expected Detection**:
- ✅ PR #123 detected
- ✅ Author captured
- ✅ Branch names extracted
- ✅ Alice's review captured

### If Your Team Uses Squash-Merge

**Example commit message**:
```
feature-xyz: Add new feature (pull request #123)
```

**Expected Detection**:
- ✅ PR #123 detected (NEW - wasn't detected before)
- ✅ Author captured
- ⚠️ Commit count = 1 (squashed)
- ⚠️ Approvals only if documented in message

## Troubleshooting

### Still Showing 0 PRs?

**Possible reasons**:

1. **Commit messages don't contain PR numbers**

   Check with:
   ```bash
   cd repositories/PROJ_your-repo
   git log --oneline | grep -i "pull\|pr"
   ```

   If no results → Your commit messages don't reference PR numbers.

   **Solution**: Configure Bitbucket to include PR numbers in merge/squash commits:
   - Repository Settings → Default merge strategy
   - Enable "Include pull request ID in commit message"

2. **Using a different PR reference format**

   Share the output of the diagnostic tool:
   ```bash
   python diagnose_repo.py ./repositories/PROJ_your-repo > diagnosis.txt
   ```

   We can add a custom pattern for your format.

3. **PRs were never merged**

   GitPython can only detect PRs that have been merged (exist in Git history).
   Open/declined PRs are not in the Git commit history.

### Approvals Still Showing 0?

**This is expected** if your team doesn't document approvals in Git commit messages.

**Why**: Bitbucket web UI approvals are NOT stored in Git commits. They're only in Bitbucket's database.

**Solutions**:

1. **Start documenting approvals** (going forward):
   ```bash
   git commit -m "Feature X

   Reviewed-by: John Doe <john@company.com>
   Approved-by: Jane Smith <jane@company.com>"
   ```

2. **Use API integration** (alternative approach):
   - Would require Bitbucket REST API access
   - Can fetch web UI approvals
   - More complex setup
   - Let us know if you need this

3. **Accept limitation**:
   - GitPython approach focuses on commit history
   - For merged PRs and documented approvals
   - Simpler, works across all platforms
   - Good enough for many use cases

## What to Share If It Still Doesn't Work

If PRs are still showing 0, please share:

1. **Debug output** from the extraction:
   ```bash
   python cli.py repos.csv 2>&1 | tee output.log
   ```

2. **Diagnostic report**:
   ```bash
   python diagnose_repo.py ./repositories/PROJ_repo > diagnosis.txt
   ```

3. **Sample commit messages** (sanitized):
   ```bash
   cd repositories/PROJ_repo
   git log --merges -5 --pretty=format:"%s%n%b%n---" > sample_commits.txt
   ```

4. **Repository workflow info**:
   - Do you use merge commits or squash-merge?
   - Are PR numbers included in commit messages?
   - Example screenshot of a merged PR's commit

## Performance Notes

- The enhanced detection checks more commits (not just merge commits)
- This may add 10-20% to extraction time
- But significantly improves detection rate
- Trade-off is worth it for better data quality

## Documentation

Updated documentation:
- ✅ [README.md](README.md) - Main docs with improvement notes
- ✅ [PR_DETECTION_IMPROVEMENTS.md](PR_DETECTION_IMPROVEMENTS.md) - Detailed technical changes
- ✅ [GITPYTHON_ANALYSIS_GUIDE.md](GITPYTHON_ANALYSIS_GUIDE.md) - Still valid
- ✅ [diagnose_repo.py](diagnose_repo.py) - New diagnostic tool

## Questions?

Common questions:

**Q: Will this work with GitHub/GitLab?**
A: Yes! The improvements apply to all platforms. GitHub and GitLab patterns are also included.

**Q: Do I need to delete my old database?**
A: No, but you may want to re-extract to get newly detected PRs:
```bash
# Backup first
cp git_history.db git_history_backup.db
# Delete and re-extract
rm git_history.db
python cli.py repos.csv
```

**Q: Can I test without re-cloning?**
A: Yes, if you used `--no-cleanup`:
```bash
python diagnose_repo.py ./repositories/PROJ_repo
```

**Q: What if my team uses a custom format?**
A: Share examples, we can add custom patterns to the code.

## Summary

**Action Required**:
1. Re-run extraction: `python cli.py your_repos.csv`
2. Check debug output for PR detection counts
3. Verify in dashboard
4. Share results/issues if still showing 0

**Expected Outcome**: Significantly more PRs detected, especially for squash-merge workflows.

**Time Required**: 5-10 minutes for re-extraction + verification
