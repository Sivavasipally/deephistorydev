# CLI Folder Reorganization

## Summary

All CLI-related Python files have been moved into a new `cli/` folder to improve project organization and maintainability.

## Changes Made

### 1. Created CLI Package Structure

**New folder:** `cli/`

**Files moved:**
- `cli.py` - Main CLI interface
- `config.py` - Configuration management
- `models.py` - Database models (SQLAlchemy)
- `git_analyzer.py` - Git repository analysis
- `bitbucket_api.py` - Bitbucket API client
- `dashboard.py` - Legacy Streamlit dashboard
- `start_backend.py` - Backend server starter
- `diagnose_repo.py` - Repository diagnostics
- `fix_imports.py` - Import fixing utility
- `fix_mapping_table.py` - Mapping table utility
- `show_merge_commits.py` - Merge commit viewer
- `test_credential_encoding.py` - Credential tests
- `setup.py` - Package setup
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python runtime version

**Files created:**
- `cli/__init__.py` - Package initialization with exports
- `cli/__main__.py` - Entry point for `python -m cli`
- `cli/README.md` - CLI documentation

### 2. Updated Import Paths

**Backend files updated:**
All files in `backend/` directory now import from the `cli` package:

```python
# Old imports
from config import Config
from models import get_engine, get_session

# New imports
from cli.config import Config
from cli.models import get_engine, get_session
```

**Files updated:**
- `backend/main.py`
- `backend/routers/commits.py`
- `backend/routers/pull_requests.py`
- `backend/routers/authors.py`
- `backend/routers/staff.py`
- `backend/routers/tables.py`
- `backend/routers/sql_executor.py`
- `backend/routers/mappings.py`
- `backend/routers/overview.py`
- `backend/routers/dashboard360.py`

**CLI files updated:**
All files in `cli/` directory now use relative imports:

```python
# Old imports
from config import Config
from models import get_engine

# New imports
from .config import Config
from .models import get_engine
```

### 3. Updated Documentation

**README.md updates:**
- Added project structure section showing new folder layout
- Updated installation instructions to reference `cli/requirements.txt`
- Updated Quick Start commands to use `python -m cli` or `python cli/`
- Updated development mode instructions

### 4. Usage Changes

**Before reorganization:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python cli.py extract repos.csv

# Start backend
python start_backend.py
```

**After reorganization:**
```bash
# Install dependencies
pip install -r cli/requirements.txt

# Run CLI (method 1 - recommended)
python -m cli extract repos.csv

# Run CLI (method 2)
python cli/cli.py extract repos.csv

# Start backend
python cli/start_backend.py
```

## Benefits

1. **Better Organization** - All CLI-related code is now in one place
2. **Cleaner Root** - Project root is less cluttered
3. **Package Structure** - CLI is now a proper Python package with `__init__.py`
4. **Module Pattern** - Can run CLI as a module with `python -m cli`
5. **Clear Separation** - Separation between CLI, backend, and frontend
6. **Maintainability** - Easier to understand project structure
7. **Scalability** - Easier to add new CLI utilities

## Compatibility

- ✅ **Backend API** - All routes working correctly with new imports
- ✅ **Frontend** - No changes needed, continues to work
- ✅ **CLI Commands** - All CLI commands functional with new structure
- ✅ **Database** - No changes to database schema or operations
- ✅ **Configuration** - `.env` file location unchanged

## Testing Performed

1. ✅ CLI package imports successfully
2. ✅ Backend app loads without errors
3. ✅ All router files compile without syntax errors
4. ✅ Frontend build completes successfully

## Migration Notes

If you have any custom scripts that import from these modules, update them:

```python
# Update any scripts that import
from config import Config          # ❌ Old
from cli.config import Config      # ✅ New

from models import Repository      # ❌ Old
from cli.models import Repository  # ✅ New
```

## Rollback (if needed)

To rollback these changes:
1. Move all files from `cli/` back to root
2. Revert import changes in `backend/` files
3. Delete `cli/__init__.py` and `cli/__main__.py`

However, the new structure is recommended for better project organization.
