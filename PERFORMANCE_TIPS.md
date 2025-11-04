# Performance Tips and Best Practices

## Repository Size Considerations

### Small Repositories (< 100 MB, < 1000 commits)
**Examples**: Demo repos, small projects, personal projects
- **Clone Time**: Seconds to minutes
- **Processing**: Very fast
- **Recommended**: Perfect for testing and small-scale analysis

### Medium Repositories (100 MB - 1 GB, 1000 - 50K commits)
**Examples**: Most application projects, libraries
- **Clone Time**: 2-10 minutes
- **Processing**: Fast to moderate
- **Recommended**: Standard use case

### Large Repositories (1 GB - 10 GB, 50K - 500K commits)
**Examples**: Large applications, frameworks
- **Clone Time**: 10-60 minutes
- **Processing**: Moderate to slow
- **Recommendations**:
  - Process in batches
  - Use `--no-cleanup` to keep repos if re-running
  - Ensure adequate disk space (2-3x repo size)
  - Run during off-hours

### Very Large Repositories (> 10 GB, > 500K commits)
**Examples**: Linux kernel, Chromium, large monorepos
- **Clone Time**: Hours
- **Processing**: Very slow
- **Recommendations**:
  - ⚠️ **NOT RECOMMENDED** for this tool
  - Consider using shallow clones
  - May timeout or fail
  - Use repository-specific APIs instead
  - Requires significant disk space (100+ GB)

## Performance Optimization Tips

### 1. Batch Processing
Process repositories in small batches:
```bash
# Instead of one large CSV with 100 repos
# Split into multiple smaller CSVs
python cli.py batch1.csv  # 10 repos
python cli.py batch2.csv  # 10 repos
# etc.
```

### 2. Cleanup Strategy

**For testing/debugging**:
```bash
python cli.py repos.csv --no-cleanup
```
Keeps cloned repos for inspection.

**For production**:
```bash
python cli.py repos.csv
```
Automatically cleans up after processing.

### 3. Database Choice

**SQLite** (Default):
- ✅ Great for: < 1M commits
- ✅ Zero configuration
- ✅ Fast for single-user
- ❌ Not ideal for concurrent access

**MariaDB**:
- ✅ Great for: > 1M commits
- ✅ Better for concurrent users
- ✅ Better for large datasets
- ❌ Requires server setup

### 4. Disk Space Management

Monitor disk space before processing:

**Windows**:
```bash
dir repositories /s
```

**Linux/Mac**:
```bash
du -sh repositories
```

Rule of thumb: Need 3x the total repository size:
- 1x for cloned repo
- 1x for Git operations
- 1x for safety margin

### 5. Network Considerations

**Slow network**:
- Clone speed is bottleneck
- Consider local network mirrors
- Process repositories during off-peak hours

**Fast network**:
- Processing is bottleneck
- Can process larger repos
- Parallel processing possible (future feature)

## Troubleshooting Performance Issues

### Issue: Clone takes too long

**Solutions**:
1. Check repository size on GitHub/GitLab first
2. Skip very large repositories (> 10 GB)
3. Use faster internet connection
4. Clone during off-peak hours

### Issue: Processing is slow

**Solutions**:
1. Use SSD instead of HDD
2. Close other applications
3. Process fewer repositories at once
4. Switch to MariaDB for large datasets

### Issue: Running out of disk space

**Solutions**:
1. Let tool cleanup automatically (don't use `--no-cleanup`)
2. Process in smaller batches
3. Clean up old database files
4. Use external/network drive

### Issue: Database queries are slow

**Solutions**:
1. Switch from SQLite to MariaDB
2. Add database indexes (for custom queries)
3. Archive old data
4. Reduce result set size in dashboard filters

## Recommended Repository Sizes for Testing

For testing the application, use these small repositories:

```csv
Project Key,Slug Name,Clone URL (HTTP)
EXAMPLE1,hello-world,https://github.com/octocat/Hello-World.git
EXAMPLE2,spoon-knife,https://github.com/octocat/Spoon-Knife.git
EXAMPLE3,git-consortium,https://github.com/octocat/git-consortium.git
```

These are:
- ✅ Small (< 1 MB each)
- ✅ Fast to clone (< 10 seconds)
- ✅ Quick to process
- ✅ Perfect for testing

## Production Use Guidelines

### Step 1: Test with small repos
```bash
python cli.py sample_repositories.csv
```

### Step 2: Verify data in dashboard
```bash
streamlit run dashboard.py
```

### Step 3: Process your actual repositories
Create your CSV with your repos and run:
```bash
python cli.py my_repositories.csv
```

### Step 4: Monitor progress
- Watch console output
- Check disk space regularly
- Monitor memory usage
- Be patient with large repos

## Expected Processing Times

Based on typical hardware (SSD, 16GB RAM, 100 Mbps internet):

| Repo Size | Clone Time | Process Time | Total Time |
|-----------|------------|--------------|------------|
| Small (< 100 MB) | 10-60 sec | 5-30 sec | < 2 min |
| Medium (< 1 GB) | 2-10 min | 1-5 min | 3-15 min |
| Large (< 10 GB) | 10-60 min | 5-30 min | 15-90 min |
| Very Large (> 10 GB) | Hours | Hours | Many hours |

**Note**: Times are per repository. Multiply by number of repositories in your CSV.

## Best Practices Summary

1. ✅ **Start small** - Test with sample repositories first
2. ✅ **Check size** - Verify repository sizes before processing
3. ✅ **Monitor resources** - Watch disk space and memory
4. ✅ **Batch processing** - Process in manageable batches
5. ✅ **Use cleanup** - Let tool cleanup automatically
6. ✅ **Choose right DB** - SQLite for < 1M commits, MariaDB for more
7. ❌ **Avoid huge repos** - Skip repositories > 10 GB
8. ❌ **Don't parallel** - Process one CSV at a time

## Getting Help

If you encounter performance issues:
1. Check this guide first
2. Review README.md troubleshooting section
3. Consider repository size limits
4. File an issue with details (repo size, error message, system specs)
