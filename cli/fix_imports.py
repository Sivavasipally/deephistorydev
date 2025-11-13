"""Fix imports in backend router files."""

import os
from pathlib import Path

router_files = [
    'backend/routers/overview.py',
    'backend/routers/authors.py',
    'backend/routers/commits.py',
    'backend/routers/pull_requests.py',
    'backend/routers/staff.py',
    'backend/routers/mappings.py',
    'backend/routers/tables.py',
    'backend/routers/sql_executor.py'
]

path_setup_code = """import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

"""

for router_file in router_files:
    filepath = Path(router_file)
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if path setup already added
        if 'sys.path.insert' not in content:
            # Find the first import line and add before it
            lines = content.split('\n')
            new_lines = []
            import_added = False

            for line in lines:
                if not import_added and line.strip().startswith('from') or line.strip().startswith('import'):
                    # Add path setup before first import
                    new_lines.append(path_setup_code)
                    import_added = True
                new_lines.append(line)

            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))

            print(f"[OK] Fixed imports in {router_file}")
        else:
            print(f"[SKIP] Skipped {router_file} (already has path setup)")
    else:
        print(f"[ERROR] File not found: {router_file}")

print("\n[DONE] All router files processed!")
