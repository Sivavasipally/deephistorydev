# PCF Deployment - Summary

## 📦 What Was Created

This deployment package enables the Git History Deep Analyzer to run on Pivotal Cloud Foundry (PCF) with full support for CUPS (Cloud Foundry User-Provided Services) and managed database services.

---

## 🗂️ Files Created

### 1. **Manifest Files**

#### `manifest-backend.yml`
- Backend application manifest
- Configures Python buildpack
- Sets memory: 1G, instances: 1
- Binds to `git-history-config` (CUPS) and `git-history-db` (MySQL)
- Health check on `/api/overview/stats`
- Route: `git-history-backend.apps.pcfone.io`

#### `manifest-frontend.yml`
- Frontend application manifest
- Configures staticfile buildpack
- Serves built React app from `frontend/dist`
- Sets memory: 256M, instances: 1
- Forces HTTPS
- Route: `git-history.apps.pcfone.io`

### 2. **Configuration Files**

#### `config.py` (Updated)
**Changes Made:**
- Added PCF CUPS support via `VCAP_SERVICES`
- Properties now read from CUPS, environment variables, or defaults
- Auto-detects MySQL service bindings
- Configuration precedence:
  1. Environment variables (local dev)
  2. CUPS service credentials (PCF)
  3. Bound MySQL service (PCF)
  4. Default values

**New Methods:**
- `_get_vcap_services()` - Parse PCF service bindings
- `_get_service_credentials(service_name)` - Get CUPS credentials
- `_get_config_value()` - Multi-source config resolution

#### `Staticfile`
- Configures staticfile buildpack for frontend
- Sets root to `frontend/dist`
- Includes nginx configuration from `includes/` directory

#### `includes/routes.conf`
- Nginx configuration for SPA routing
- Redirects all routes to `index.html` (React Router)
- Proxies `/api/*` requests to backend
- Enables proper frontend routing

#### `runtime.txt`
- Specifies Python 3.9.x for buildpack

#### `.cfignore`
- Excludes unnecessary files from deployment
- Reduces upload time and app size
- Excludes: venv, node_modules, source files, docs, etc.

#### `credentials.json.template`
- Template for CUPS credentials
- Shows required JSON structure
- Copy and rename to `credentials.json` for deployment

### 3. **Deployment Scripts**

#### `deploy-pcf.sh` (Linux/Mac)
Automated deployment script featuring:
- ✅ CF CLI installation check
- ✅ Login verification
- ✅ Interactive CUPS creation/update
- ✅ Optional MySQL service creation
- ✅ Frontend build process
- ✅ Backend deployment
- ✅ Frontend deployment
- ✅ Deployment summary with URLs

#### `deploy-pcf.bat` (Windows)
Windows version of deployment script with same features.

### 4. **Documentation**

#### `PCF_DEPLOYMENT_GUIDE.md`
**Comprehensive 2000+ line guide covering:**
- Prerequisites and setup
- Architecture overview
- CUPS configuration details
- Manual deployment steps
- Automated deployment
- Environment variables
- Database setup (SQLite/MySQL)
- Troubleshooting guide
- Monitoring and logs
- Scaling strategies
- CI/CD integration (Jenkins, GitHub Actions)
- Security best practices
- Command reference

#### `PCF_QUICK_START.md`
**Quick start guide for rapid deployment:**
- 5-command deployment
- Using automated scripts
- Configuration options
- Pre-deployment checklist
- First-time setup
- Common commands
- Troubleshooting quick fixes

---

## 🔑 Key Features

### 1. **CUPS Integration**

The application now reads configuration from PCF Cloud Foundry User-Provided Services:

```bash
cf create-user-provided-service git-history-config -p '{
  "db_type": "mysql",
  "git_username": "user",
  "git_password": "pass",
  "bitbucket_url": "https://bitbucket.company.com",
  "bitbucket_username": "bb-user",
  "bitbucket_app_password": "bb-pass"
}'
```

**Supported Configuration Keys:**
- `db_type` - Database type (sqlite/mysql)
- `git_username` - Git clone username
- `git_password` - Git clone password/token
- `bitbucket_url` - Bitbucket server URL
- `bitbucket_username` - Bitbucket API username
- `bitbucket_app_password` - Bitbucket API app password

### 2. **MySQL Service Auto-Detection**

When a MySQL service is bound to the backend app, configuration is automatically detected from `VCAP_SERVICES`:

```bash
cf create-service p-mysql db-small git-history-db
cf bind-service git-history-backend git-history-db
```

No additional configuration needed - connection details are auto-discovered!

### 3. **Multi-Environment Support**

The same codebase works in:
- **Local Development**: Uses `.env` file
- **PCF with CUPS**: Uses CUPS service
- **PCF with MySQL**: Uses bound service + CUPS

Configuration precedence ensures smooth transition between environments.

### 4. **Frontend API Proxy**

Frontend nginx configuration (`includes/routes.conf`) automatically proxies API requests:
- Frontend: `https://git-history.apps.pcfone.io`
- API calls to `/api/*` → Proxied to backend
- No CORS issues
- Seamless integration

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PCF CLOUD FOUNDRY                       │
└─────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  git-history-frontend│  (Route: git-history.apps.pcfone.io)
│  Staticfile Buildpack│  - Serves React app
│  256MB / 1 instance  │  - Nginx SPA routing
└──────────┬───────────┘  - API proxy to backend
           │
           │ /api/* proxied to backend
           ↓
┌──────────────────────┐
│  git-history-backend │  (Route: git-history-backend.apps.pcfone.io)
│  Python Buildpack    │  - FastAPI REST API
│  1GB / 1 instance    │  - 20+ endpoints
└──────────┬───────────┘  - SQLAlchemy ORM
           │
           │ binds to
           ↓
┌────────────────────────────────────────────────────────┐
│           git-history-config (CUPS)                     │
│  - db_type, git credentials, bitbucket config          │
└────────────────────────────────────────────────────────┘
           │
           │ (optional) binds to
           ↓
┌────────────────────────────────────────────────────────┐
│           git-history-db (MySQL Service)                │
│  - Persistent database                                 │
│  - Auto-detected via VCAP_SERVICES                     │
└────────────────────────────────────────────────────────┘
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [x] CF CLI installed
- [x] Logged in to PCF
- [x] Node.js 16+ installed
- [x] Python 3.8+ installed (for local testing)
- [x] Git credentials available
- [x] Bitbucket credentials available

### Files Ready
- [x] `manifest-backend.yml`
- [x] `manifest-frontend.yml`
- [x] `Staticfile`
- [x] `includes/routes.conf`
- [x] `config.py` (updated)
- [x] `runtime.txt`
- [x] `.cfignore`
- [x] `deploy-pcf.sh` / `deploy-pcf.bat`

### Deployment Steps
1. [x] Create CUPS service (`git-history-config`)
2. [ ] (Optional) Create MySQL service (`git-history-db`)
3. [ ] Build frontend (`npm run build`)
4. [ ] Deploy backend (`cf push -f manifest-backend.yml`)
5. [ ] Deploy frontend (`cf push -f manifest-frontend.yml`)
6. [ ] Initialize database (if using MySQL)
7. [ ] Verify deployment

---

## 🎯 Quick Deployment Commands

### Option 1: Automated Script

**Linux/Mac:**
```bash
chmod +x deploy-pcf.sh
./deploy-pcf.sh
```

**Windows:**
```cmd
deploy-pcf.bat
```

### Option 2: Manual Commands

```bash
# 1. Login
cf login -a api.system.pcfone.io

# 2. Create CUPS (from template)
cp credentials.json.template credentials.json
# Edit credentials.json with your values
cf create-user-provided-service git-history-config -p credentials.json

# 3. (Optional) Create MySQL
cf create-service p-mysql db-small git-history-db

# 4. Build frontend
cd frontend
npm install
echo "VITE_API_BASE_URL=https://git-history-backend.apps.pcfone.io" > .env.production
npm run build
cd ..

# 5. Deploy
cf push -f manifest-backend.yml
cf push -f manifest-frontend.yml

# 6. Verify
cf apps
curl https://git-history-backend.apps.pcfone.io/api/overview/stats
```

---

## 🔧 Configuration Examples

### Development (SQLite)

```json
{
  "db_type": "sqlite"
}
```

⚠️ **Warning**: SQLite data is ephemeral in PCF!

### Production (MySQL)

```json
{
  "db_type": "mysql",
  "git_username": "git-user",
  "git_password": "ghp_token123",
  "bitbucket_url": "https://bitbucket.company.com",
  "bitbucket_username": "bb-user",
  "bitbucket_app_password": "app-password-123"
}
```

With bound MySQL service:
```bash
cf create-service p-mysql db-small git-history-db
# MySQL credentials auto-detected from VCAP_SERVICES
```

---

## 📊 Post-Deployment

### Initialize Database

For MySQL:
```bash
cf ssh git-history-backend
python
>>> from models import create_tables
>>> from config import Config
>>> config = Config()
>>> create_tables(config.get_db_config())
>>> exit()
exit
```

### Access Application

- **Frontend**: https://git-history.apps.pcfone.io
- **Backend API**: https://git-history-backend.apps.pcfone.io
- **API Docs**: https://git-history-backend.apps.pcfone.io/docs

### Monitor Logs

```bash
# Tail logs
cf logs git-history-backend

# Recent logs
cf logs git-history-backend --recent
```

### Scale Application

```bash
# Horizontal scaling
cf scale git-history-backend -i 3

# Vertical scaling
cf scale git-history-backend -m 2G
```

---

## 🔍 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| App won't start | Check logs: `cf logs git-history-backend --recent` |
| CUPS not found | Create service: `cf create-user-provided-service` |
| Database connection failed | Verify MySQL service: `cf service git-history-db` |
| Frontend 404 errors | Check `includes/routes.conf` is included |
| API calls fail | Verify backend URL in `.env.production` |

### Debug Commands

```bash
# Check app status
cf apps

# View environment
cf env git-history-backend

# SSH into app
cf ssh git-history-backend

# Test database connection
cf ssh git-history-backend
python
from config import Config
config = Config()
print(config.get_db_config())
```

---

## 📚 Documentation Reference

| Document | Purpose |
|----------|---------|
| `PCF_QUICK_START.md` | 10-minute quick deployment |
| `PCF_DEPLOYMENT_GUIDE.md` | Comprehensive deployment guide |
| `README.md` | Application documentation |
| `manifest-backend.yml` | Backend app manifest |
| `manifest-frontend.yml` | Frontend app manifest |

---

## 🎉 Success Criteria

✅ Both apps show `running` status
✅ Backend health check passes: `curl https://git-history-backend.apps.pcfone.io/api/overview/stats`
✅ Frontend loads: `https://git-history.apps.pcfone.io`
✅ API calls work from frontend
✅ Logs show no errors: `cf logs git-history-backend --recent`

---

## 🚀 Next Steps

After successful deployment:

1. **Initialize Database** (if using MySQL)
2. **Extract Git Data** (from local machine or CI/CD)
   ```bash
   python cli.py extract repositories.csv
   ```
3. **Import Staff Data**
   ```bash
   python cli.py import-staff staff_data.xlsx
   ```
4. **Access & Use Application**
   - Map authors to staff
   - View dashboards
   - Export reports

---

## 📞 Support

For issues or questions, refer to:
- **PCF_DEPLOYMENT_GUIDE.md** - Comprehensive troubleshooting
- **PCF_QUICK_START.md** - Quick fixes
- **CF Logs**: `cf logs git-history-backend --recent`

---

**Deployment Package Version**: 1.0
**Last Updated**: 2025-01-11
**Compatible with**: PCF 2.x and above

---

**Happy Deploying to PCF! 🎉🚀**
