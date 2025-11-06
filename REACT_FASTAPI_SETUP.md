# React + FastAPI Setup Guide

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   GIT HISTORY ANALYZER v2.0                      │
│                    React + FastAPI Stack                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐          ┌──────────────┐          ┌────────┐ │
│  │   Frontend   │  HTTP    │   Backend    │  SQL     │  DB    │ │
│  │   React.js   │◄────────►│   FastAPI    │◄────────►│MariaDB │ │
│  │  Ant Design  │   API    │   Python     │  Queries │        │ │
│  └──────────────┘          └──────────────┘          └────────┘ │
│       │                           │                              │
│       │                           │                              │
│  ┌────▼────┐               ┌──────▼──────┐                      │
│  │ Vite    │               │ Uvicorn     │                      │
│  │ Port    │               │ Port        │                      │
│  │ 3000    │               │ 8000        │                      │
│  └─────────┘               └─────────────┘                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Project Structure

```
deephistorydev/
├── backend/                    # FastAPI Backend
│   ├── main.py                # Main FastAPI app
│   ├── routers/               # API route handlers
│   │   ├── overview.py        # Overview stats
│   │   ├── authors.py         # Author analytics
│   │   ├── commits.py         # Commits data
│   │   ├── pull_requests.py   # PR data
│   │   ├── staff.py           # Staff details
│   │   ├── mappings.py        # Author-staff mapping
│   │   ├── tables.py          # Table viewer
│   │   └── sql_executor.py    # SQL execution + AI
│   └── __init__.py
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── pages/             # Page components
│   │   │   ├── Overview.jsx
│   │   │   ├── AuthorsAnalytics.jsx
│   │   │   ├── CommitsView.jsx
│   │   │   ├── PullRequestsView.jsx
│   │   │   ├── TopCommits.jsx
│   │   │   ├── TopApprovers.jsx
│   │   │   ├── AuthorMapping.jsx
│   │   │   ├── TableViewer.jsx
│   │   │   └── SQLExecutor.jsx
│   │   ├── services/
│   │   │   └── api.js         # API client
│   │   ├── App.jsx            # Main app with routing
│   │   ├── main.jsx           # Entry point
│   │   └── index.css          # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── models.py                   # Database models (shared)
├── config.py                   # Configuration
├── cli.py                      # CLI tool
└── .env                        # Environment variables
```

## 🚀 Installation

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** and **npm**
- **MariaDB/MySQL** database

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional backend dependencies
pip install fastapi uvicorn[standard] python-multipart
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Return to root
cd ..
```

### 3. Database Setup

```bash
# Ensure MariaDB is running
# Create database (if not exists)

# Run migrations (database initialization happens automatically)
```

### 4. Environment Configuration

Create/update `.env` file:

```env
# Database Configuration
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=git_history

# Git Credentials
GIT_USERNAME=your_git_username
GIT_PASSWORD=your_git_password_or_token

# Bitbucket API Configuration
BITBUCKET_URL=https://bitbucket.sgp.dbs.com:8443
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_APP_PASSWORD=your_bitbucket_app_password

# Clone Directory
CLONE_DIR=./repositories
```

## ▶️ Running the Application

### Development Mode

You need **two terminal windows**:

#### Terminal 1: Backend Server

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Start FastAPI server
cd backend
python main.py

# Or use uvicorn directly:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: **http://localhost:8000**
- API Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

#### Terminal 2: Frontend Dev Server

```bash
# Navigate to frontend
cd frontend

# Start Vite dev server
npm run dev
```

Frontend will run on: **http://localhost:3000**

### Production Mode

#### Build Frontend

```bash
cd frontend
npm run build
```

This creates an optimized build in `frontend/dist/`

#### Serve with FastAPI

You can serve the built frontend from FastAPI by adding static file mounting:

```python
# In backend/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```

Then run only the backend:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Access at: **http://localhost:8000**

## 🎨 Features

### Frontend Features

- ✅ **Modern UI with Ant Design**
  - Professional enterprise-grade component library
  - Responsive design for mobile/tablet/desktop
  - Dark mode toggle (in header)

- ✅ **Advanced Navigation**
  - Collapsible sidebar with icons
  - Breadcrumb navigation
  - React Router for SPA routing
  - Sticky header with branding

- ✅ **Interactive Dashboards**
  - Overview page with 6 stat cards
  - Authors Analytics with date range filtering
  - Commits & PR views with filters
  - Top contributors charts

- ✅ **AI-Powered SQL Generator**
  - Natural language to SQL conversion
  - Integrated with Dify AI API
  - One-click query execution
  - Download results as CSV

- ✅ **Data Visualization**
  - Bar charts (Ant Design Charts)
  - Interactive tables with sorting/filtering
  - Pagination and search
  - Export capabilities

### Backend Features

- ✅ **RESTful API with FastAPI**
  - Auto-generated OpenAPI docs
  - Type validation with Pydantic
  - Async/await support
  - CORS enabled for frontend

- ✅ **Modular Router Structure**
  - `/api/overview` - Dashboard stats
  - `/api/authors` - Author analytics
  - `/api/commits` - Commit data
  - `/api/pull-requests` - PR data
  - `/api/staff` - Staff details
  - `/api/mappings` - Author-staff mapping
  - `/api/tables` - Table viewer
  - `/api/sql` - SQL execution + AI generation

- ✅ **Database Integration**
  - SQLAlchemy ORM
  - Connection pooling
  - Efficient querying

- ✅ **AI Integration**
  - Dify AI API for SQL generation
  - SSL verification disabled for corporate certs
  - Error handling and timeouts

## 📊 API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

```
GET  /api/overview/stats              # Overview statistics
GET  /api/authors/statistics          # Author stats (with date filters)
GET  /api/authors/top-contributors    # Top contributors by metric
GET  /api/commits/                    # List commits (with filters)
GET  /api/commits/top-by-lines        # Top commits by lines
GET  /api/pull-requests/              # List PRs (with filters)
GET  /api/pull-requests/top-approvers # Top PR approvers
GET  /api/staff/                      # Staff list (with search)
GET  /api/mappings/                   # Get all mappings
POST /api/mappings/                   # Create mapping
DELETE /api/mappings/{author_name}    # Delete mapping
GET  /api/mappings/unmapped-authors   # Unmapped authors
GET  /api/tables/info                 # Table row counts
GET  /api/tables/{table_name}/data    # Table data
POST /api/sql/execute                 # Execute SQL query
POST /api/sql/generate-query          # AI-generate SQL from prompt
```

## 🎯 Usage Workflows

### Workflow 1: Analyze Contributors

1. Navigate to **Authors Analytics**
2. Select date range (optional)
3. View summary stats and charts
4. Sort by different metrics
5. Download CSV report

### Workflow 2: Generate Custom Reports

1. Go to **SQL Executor**
2. Enter natural language query:
   - "Get commits from last month"
   - "Show top 5 authors by lines changed"
3. Click **Generate SQL**
4. Review generated query
5. Click **Use This Query**
6. Click **Execute Query**
7. Download results as CSV

### Workflow 3: Map Authors to Staff

1. Navigate to **Author-Staff Mapping**
2. Select unmapped author
3. Search for matching staff member
4. Add notes (optional)
5. Save mapping

### Workflow 4: Browse Database

1. Go to **Table Viewer**
2. Select table from dropdown
3. Set row limit
4. Load and view data
5. Export as CSV

## 🔧 Customization

### Adding a New Page

1. **Create page component**:
```jsx
// frontend/src/pages/MyNewPage.jsx
import React from 'react'
import { Card, Typography } from 'antd'

const MyNewPage = () => {
  return (
    <div>
      <Typography.Title level={2}>My New Page</Typography.Title>
      <Card>Content here</Card>
    </div>
  )
}

export default MyNewPage
```

2. **Add route in App.jsx**:
```jsx
import MyNewPage from './pages/MyNewPage'

// In menuItems array:
{
  key: '/my-page',
  icon: <StarOutlined />,
  label: <Link to="/my-page">My Page</Link>,
  breadcrumb: 'My Page'
}

// In Routes:
<Route path="/my-page" element={<MyNewPage />} />
```

3. **Add API endpoint** (if needed):
```python
# backend/routers/my_router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-data")
async def get_my_data():
    return {"data": "example"}
```

4. **Include router in main.py**:
```python
from .routers import my_router

app.include_router(my_router.router, prefix="/api/my", tags=["My Feature"])
```

### Styling and Theming

Ant Design theme is configured in `frontend/src/main.jsx`:

```jsx
<ConfigProvider
  theme={{
    algorithm: theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',  // Primary color
      borderRadius: 6,           // Border radius
      fontSize: 14,              // Base font size
    },
  }}
>
```

Dark mode is handled by toggling the `dark-theme` class on the layout.

## 🐛 Troubleshooting

### Backend Issues

**Port 8000 already in use**:
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

**Database connection errors**:
- Verify MariaDB is running
- Check credentials in `.env`
- Test connection: `mysql -h localhost -u root -p`

**Module import errors**:
- Ensure virtual environment is activated
- Re-install: `pip install -r requirements.txt`

### Frontend Issues

**Port 3000 already in use**:
```bash
# Change port in vite.config.js:
server: {
  port: 3001,  // Use different port
}
```

**API connection errors**:
- Ensure backend is running on port 8000
- Check proxy configuration in `vite.config.js`
- Verify CORS settings in `backend/main.py`

**Build errors**:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📚 Tech Stack

### Frontend
- **React 18** - UI library
- **Ant Design 5** - Component library
- **Vite** - Build tool
- **React Router 6** - Routing
- **Axios** - HTTP client
- **Ant Design Charts** - Data visualization
- **Day.js** - Date handling

### Backend
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **Pandas** - Data processing
- **Requests** - HTTP client (for AI API)

### Database
- **MariaDB/MySQL** - Relational database

### AI Integration
- **Dify AI API** - Natural language to SQL generation

## 📝 Development Tips

1. **Hot Reload**: Both frontend (Vite) and backend (Uvicorn with `--reload`) support hot reloading

2. **API Testing**: Use Swagger UI at `/api/docs` to test endpoints

3. **Console Logging**:
   - Frontend: Check browser console (`F12`)
   - Backend: Check terminal output

4. **Error Handling**: Errors are caught and displayed as Ant Design messages

5. **State Management**: Currently using React's useState. For complex state, consider adding Zustand or Redux

## 🚢 Deployment

### Docker Deployment (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://user:pass@db:3306/git_history
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  db:
    image: mariadb:10.6
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: git_history
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```

### Manual Deployment

1. Build frontend: `npm run build`
2. Deploy FastAPI with gunicorn + uvicorn workers
3. Use nginx as reverse proxy
4. Configure SSL certificates
5. Set up systemd services for auto-start

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Ant Design**: https://ant.design/
- **Vite**: https://vitejs.dev/
- **React Router**: https://reactrouter.com/

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review FastAPI docs at `/api/docs`
- Inspect browser console for frontend errors
- Check backend terminal for API errors

---

**Version**: 2.0.0
**Last Updated**: 2025-01-06
**Stack**: React + FastAPI + MariaDB
