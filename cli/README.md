# CLI Package

This folder contains all the CLI-related modules for the Git History Deep Analyzer.

## Contents

- **cli.py** - Main command-line interface
- **config.py** - Configuration management
- **models.py** - Database models (SQLAlchemy)
- **git_analyzer.py** - Git repository analysis logic
- **bitbucket_api.py** - Bitbucket API integration
- **dashboard.py** - Legacy Streamlit dashboard
- **start_backend.py** - FastAPI backend server starter
- **diagnose_repo.py** - Repository diagnostic utility
- **fix_imports.py** - Import fixing utility
- **fix_mapping_table.py** - Author mapping table utility
- **show_merge_commits.py** - Merge commit viewer
- **test_credential_encoding.py** - Credential encoding tests
- **setup.py** - Package setup script

## Usage

### Running the CLI

```bash
# From project root
python -m cli extract repos.csv

# Or directly
python cli/cli.py extract repos.csv
```

### Starting the Backend

```bash
# From project root
python cli/start_backend.py
```

### Legacy Streamlit Dashboard

```bash
# From project root
streamlit run cli/dashboard.py
```

## Import Changes

All imports from these modules should now use the `cli` package prefix:

```python
# Old (incorrect)
from config import Config
from models import get_engine, get_session

# New (correct)
from cli.config import Config
from cli.models import get_engine, get_session
```

## Dependencies

See [requirements.txt](requirements.txt) for all Python dependencies.
