## Installation

### Prerequisites

- **Python** 3.8 or higher
- **Node.js** 16+ and npm
- **Git** installed on your system
- **Database** (SQLite included, MySQL/PostgreSQL optional)

### Backend Setup

```bash
# 1. Install Python dependencies
pip install -r cli/requirements.txt

# 2. Create environment configuration
cp .env.example .env

# 3. Edit .env with your settings
nano .env
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build for production (optional)
npm run build
```

---

## Quick Start

### Complete Workflow

```bash
┌─────────────────────────────────────────────────────────────┐
│                    QUICK START GUIDE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Extract Git History                                │
│  ───────────────────────────                                │
│  $ python -m cli extract repositories.csv                   │
│                                                              │
│  Step 2: Import Staff Details                               │
│  ──────────────────────────────────────                     │
│  $ python -m cli import-staff staff_data.xlsx               │
│                                                              │
│  Step 3: Start Backend Server                               │
│  ───────────────────────────                                │
│  $ python cli/start_backend.py                              │
│  → Running on http://0.0.0.0:8000                          │
│                                                              │
│  Step 4: Start Frontend (New Terminal)                      │
│  ───────────────────────────────────────                    │
│  $ cd frontend                                              │
│  $ npm run dev                                              │
│  → Running on http://localhost:5173                        │
│                                                              │
│  Step 5: Map Authors to Staff                               │
│  ──────────────────────────                                 │
│  → Open http://localhost:5173                              │
│  → Navigate to "Author-Staff Mapping"                       │
│  → Use "Auto-Match by Email"                                │
│  → Map remaining authors (bulk or individual)               │
│                                                              │
│  Step 6: Analyze Productivity                               │
│  ───────────────────────────────                            │
│  → Navigate to "Staff Productivity"                         │
│  → Select staff member                                      │
│  → Choose time granularity                                  │
│  → View charts and export data                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

