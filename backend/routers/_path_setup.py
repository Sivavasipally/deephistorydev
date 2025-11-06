"""Path setup helper for routers to import parent directory modules."""

import sys
from pathlib import Path

# Add parent directory (deephistorydev) to Python path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))
