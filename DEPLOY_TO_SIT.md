# Deploy to SIT Environment - Step-by-Step Guide

Complete guide for deploying Git History Deep Analyzer to SIT (System Integration Testing) environment in PCF.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **CF CLI installed** (version 7+)
  ```bash
  cf --version
  ```

- [ ] **PCF access credentials** for SIT environment
  - Username
  - Password
  - Organization name
  - Space name (usually 'sit' or 'development')

- [ ] **Node.js 16+** installed
  ```bash
  node --version
  npm --version
  ```

- [ ] **Git credentials** for repository cloning
  - Git username
  - Git password/token

- [ ] **Bitbucket credentials** (if using Bitbucket)
  - Bitbucket server URL
  - Bitbucket username
  - Bitbucket app password

- [ ] **MySQL service plan** information (check with PCF admin)
  - Service name (e.g., `p-mysql`, `cleardb`)
  - Available plans (e.g., `db-small`, `spark`)

---

## 🚀 Deployment Steps

### **Step 1: Login to PCF SIT Environment**

```bash
# Login to PCF
cf login -a api.system.pcfone.io

# Enter your credentials when prompted:
# - Email/Username
# - Password

# Target SIT organization and space
cf target -o your-organization-name -s sit
```

**Verify you're in the correct environment:**
```bash
cf target
```

Expected output:
```
API endpoint:   https://api.system.pcfone.io
API version:    3.x.x
user:           your-email@company.com
org:            your-org
space:          sit
```

---

### **Step 2: Create Configuration Service (CUPS)**

#### **Option A: Interactive Mode (Recommended for first time)**

```bash
cf create-user-provided-service git-history-config-sit -p "db_type, git_username, git_password, bitbucket_url, bitbucket_username, bitbucket_app_password"
```

**You'll be prompted to enter each value:**

| Prompt | Example Value | Description |
|--------|---------------|-------------|
| `db_type` | `mysql` | Database type (mysql or sqlite) |
| `git_username` | `your-git-user` | Git username for cloning |
| `git_password` | `ghp_xxxxxxxxxxxx` | Git password or personal access token |
| `bitbucket_url` | `https://bitbucket.company.com` | Your Bitbucket server URL |
| `bitbucket_username` | `your-bb-user` | Bitbucket username |
| `bitbucket_app_password` | `app-password-123` | Bitbucket app password |

**Press Enter to skip optional fields.**

#### **Option B: Using Credentials File (Recommended for automation)**

1. **Copy the template:**
   ```bash
   cp credentials.json.template credentials-sit.json
   ```

2. **Edit the file with your SIT credentials:**
   ```json
   {
     "db_type": "mysql",
     "git_username": "your-git-username",
     "git_password": "your-git-token",
     "bitbucket_url": "https://bitbucket.yourcompany.com",
     "bitbucket_username": "your-bitbucket-username",
     "bitbucket_app_password": "your-bitbucket-app-password"
   }
   ```

3. **Create the CUPS service:**
   ```bash
   cf create-user-provided-service git-history-config-sit -p credentials-sit.json
   ```

**Verify service was created:**
```bash
cf services
```

You should see `git-history-config-sit` in the list.

---

### **Step 3: Create MySQL Database Service**

#### **Check available MySQL services:**
```bash
cf marketplace | grep mysql
```

Or:
```bash
cf marketplace -s p-mysql
```

This will show available plans like:
- `db-small` (512MB RAM, 5GB storage)
- `db-medium` (1GB RAM, 10GB storage)

#### **Create MySQL service for SIT:**
```bash
# Using p-mysql
cf create-service p-mysql db-small git-history-db-sit

# OR using cleardb (if p-mysql not available)
cf create-service cleardb spark git-history-db-sit
```

**Wait for service creation:**
```bash
# Check status
cf services

# Wait until status shows "create succeeded"
# This can take 5-10 minutes
```

**Expected output:**
```
name                      service   plan      bound apps   last operation
git-history-db-sit        p-mysql   db-small               create succeeded
git-history-config-sit    user-provided
```

---

### **Step 4: Update Manifest Files for SIT**

#### **Create SIT-specific manifests:**

**4.1. Create `manifest-backend-sit.yml`:**
```bash
cp manifest-backend.yml manifest-backend-sit.yml
```

**Edit `manifest-backend-sit.yml`:**
```yaml
---
applications:
  - name: git-history-backend-sit
    memory: 1G
    instances: 1
    buildpacks:
      - python_buildpack
    command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    health-check-type: http
    health-check-http-endpoint: /api/overview/stats
    timeout: 180
    env:
      PYTHONUNBUFFERED: "true"
      PYTHONPATH: "."
      ENV: "sit"
    services:
      - git-history-config-sit
      - git-history-db-sit
    routes:
      - route: git-history-backend-sit.apps.pcfone.io
```

**4.2. Create `manifest-frontend-sit.yml`:**
```bash
cp manifest-frontend.yml manifest-frontend-sit.yml
```

**Edit `manifest-frontend-sit.yml`:**
```yaml
---
applications:
  - name: git-history-frontend-sit
    memory: 256M
    instances: 1
    buildpacks:
      - staticfile_buildpack
    path: frontend/dist
    env:
      FORCE_HTTPS: "true"
    routes:
      - route: git-history-sit.apps.pcfone.io
```

---

### **Step 5: Update Frontend Configuration for SIT**

**Navigate to frontend directory:**
```bash
cd frontend
```

**Create SIT production environment file:**
```bash
echo "VITE_API_BASE_URL=https://git-history-backend-sit.apps.pcfone.io" > .env.production
```

**Verify the file:**
```bash
cat .env.production
```

Expected output:
```
VITE_API_BASE_URL=https://git-history-backend-sit.apps.pcfone.io
```

---

### **Step 6: Build Frontend**

**Still in `frontend` directory:**

```bash
# Install dependencies (if not already installed)
npm install

# Build for production
npm run build
```

**Wait for build to complete (takes ~20-30 seconds).**

**Verify build succeeded:**
```bash
ls -la dist/
```

You should see:
```
dist/
├── assets/
├── index.html
└── ...
```

**Return to project root:**
```bash
cd ..
```

---

### **Step 7: Update Nginx Configuration for SIT**

**Edit `includes/routes.conf`:**
```bash
nano includes/routes.conf
```

**Update to:**
```nginx
# SPA routing - redirect all routes to index.html
location / {
    try_files $uri $uri/ /index.html;
}

# API proxy to backend (SIT)
location /api/ {
    proxy_pass https://git-history-backend-sit.apps.pcfone.io/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Save and close (Ctrl+X, Y, Enter).**

---

### **Step 8: Deploy Backend to SIT**

```bash
cf push -f manifest-backend-sit.yml
```

**This will:**
1. Upload application code
2. Stage application with Python buildpack
3. Bind to services (CUPS and MySQL)
4. Start the application

**Wait for deployment (takes 2-3 minutes).**

**Verify deployment:**
```bash
cf apps
```

Expected output:
```
name                          state     instances   memory   disk   urls
git-history-backend-sit       started   1/1         1G       1G     git-history-backend-sit.apps.pcfone.io
```

**Check logs:**
```bash
cf logs git-history-backend-sit --recent
```

Look for:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete.
```

---

### **Step 9: Initialize Database**

**SSH into backend container:**
```bash
cf ssh git-history-backend-sit
```

**Inside the container, run Python:**
```bash
python
```

**In Python shell, initialize database:**
```python
from models import create_tables
from config import Config

config = Config()
db_config = config.get_db_config()

print("Database config:", db_config)
print("\nCreating tables...")

create_tables(db_config)

print("✅ Database initialized successfully!")
exit()
```

**Exit SSH:**
```bash
exit
```

---

### **Step 10: Deploy Frontend to SIT**

```bash
cf push -f manifest-frontend-sit.yml
```

**Wait for deployment (takes 1-2 minutes).**

**Verify deployment:**
```bash
cf apps
```

Expected output:
```
name                          state     instances   memory   disk   urls
git-history-backend-sit       started   1/1         1G       1G     git-history-backend-sit.apps.pcfone.io
git-history-frontend-sit      started   1/1         256M     1G     git-history-sit.apps.pcfone.io
```

---

### **Step 11: Verify Deployment**

#### **11.1. Test Backend Health:**
```bash
curl https://git-history-backend-sit.apps.pcfone.io/api/overview/stats
```

Expected response (JSON):
```json
{
  "total_commits": 0,
  "total_authors": 0,
  "total_repositories": 0,
  "total_pull_requests": 0
}
```

#### **11.2. Test Backend API Docs:**

Open in browser:
```
https://git-history-backend-sit.apps.pcfone.io/docs
```

You should see Swagger UI with all API endpoints.

#### **11.3. Test Frontend:**

Open in browser:
```
https://git-history-sit.apps.pcfone.io
```

You should see the Git History Analyzer dashboard.

#### **11.4. Check Application Logs:**
```bash
# Backend logs
cf logs git-history-backend-sit --recent

# Frontend logs
cf logs git-history-frontend-sit --recent
```

---

### **Step 12: Verify Service Bindings**

```bash
# Check backend environment
cf env git-history-backend-sit
```

**Verify:**
1. ✅ `VCAP_SERVICES` contains `git-history-config-sit`
2. ✅ `VCAP_SERVICES` contains `git-history-db-sit` (MySQL)
3. ✅ All credentials are present

---

## 🧪 Post-Deployment Testing

### **Test 1: Database Connection**

```bash
cf ssh git-history-backend-sit
python
```

```python
from config import Config
from models import get_engine, get_session

config = Config()
db_config = config.get_db_config()
print("DB Config:", db_config)

engine = get_engine(db_config)
session = get_session(engine)

# Test query
from models import Repository
repos = session.query(Repository).count()
print(f"Repositories count: {repos}")

session.close()
exit()
```

```bash
exit
```

### **Test 2: API Endpoints**

```bash
# Test overview
curl https://git-history-backend-sit.apps.pcfone.io/api/overview/stats

# Test staff endpoint
curl https://git-history-backend-sit.apps.pcfone.io/api/staff?limit=10

# Test authors
curl https://git-history-backend-sit.apps.pcfone.io/api/authors/statistics?limit=10
```

### **Test 3: Frontend Functionality**

Open `https://git-history-sit.apps.pcfone.io` and test:
1. ✅ Overview page loads
2. ✅ Authors Analytics page loads
3. ✅ 360° Dashboards page loads
4. ✅ No console errors in browser (F12)
5. ✅ API calls succeed (check Network tab in F12)

---

## 🔧 Troubleshooting Common Issues

### **Issue 1: Backend Won't Start**

**Symptoms:** App shows as `crashed` or `starting`

**Solution:**
```bash
# Check logs
cf logs git-history-backend-sit --recent

# Common causes:
# - Missing CUPS service
cf services | grep git-history-config-sit

# - Database not accessible
cf service git-history-db-sit

# - Port binding issue
cf env git-history-backend-sit | grep PORT
```

### **Issue 2: Frontend Shows API Errors**

**Symptoms:** Network errors in browser console

**Solution:**
```bash
# Verify backend is running
cf app git-history-backend-sit

# Test backend directly
curl https://git-history-backend-sit.apps.pcfone.io/api/overview/stats

# Check frontend environment
cat frontend/.env.production

# Should be:
# VITE_API_BASE_URL=https://git-history-backend-sit.apps.pcfone.io
```

### **Issue 3: Database Connection Failed**

**Symptoms:** `Connection refused` or `Timeout` errors

**Solution:**
```bash
# Check MySQL service status
cf service git-history-db-sit

# Should show: create succeeded

# Verify binding
cf env git-history-backend-sit | grep VCAP_SERVICES

# Restart app
cf restart git-history-backend-sit
```

### **Issue 4: CUPS Service Not Found**

**Symptoms:** `Service instance git-history-config-sit not found`

**Solution:**
```bash
# List all services
cf services

# Create if missing
cf create-user-provided-service git-history-config-sit -p credentials-sit.json

# Bind to app
cf bind-service git-history-backend-sit git-history-config-sit

# Restage
cf restage git-history-backend-sit
```

### **Issue 5: Out of Memory**

**Symptoms:** App keeps crashing with OOM errors

**Solution:**
```bash
# Increase memory in manifest
# Edit manifest-backend-sit.yml: memory: 2G

# Redeploy
cf push -f manifest-backend-sit.yml
```

---

## 📊 Monitoring & Health Checks

### **View App Status**
```bash
cf apps
```

### **View Logs (Live Tail)**
```bash
# Backend
cf logs git-history-backend-sit

# Frontend
cf logs git-history-frontend-sit
```

### **View Recent Logs**
```bash
cf logs git-history-backend-sit --recent
```

### **Check App Events**
```bash
cf events git-history-backend-sit
```

### **SSH into App**
```bash
cf ssh git-history-backend-sit
```

### **View Resource Usage**
```bash
cf app git-history-backend-sit
```

---

## 🔄 Update/Redeploy Application

### **Update Backend Code**
```bash
# Pull latest code
git pull

# Redeploy
cf push -f manifest-backend-sit.yml
```

### **Update Frontend**
```bash
cd frontend
npm run build
cd ..
cf push -f manifest-frontend-sit.yml
```

### **Update Configuration**
```bash
# Update CUPS
cf update-user-provided-service git-history-config-sit -p '{
  "git_password": "new-password"
}'

# Restage app
cf restage git-history-backend-sit
```

---

## 📝 Environment Summary

After successful deployment, you'll have:

| Component | Name | URL | Memory | Instances |
|-----------|------|-----|--------|-----------|
| Frontend | `git-history-frontend-sit` | https://git-history-sit.apps.pcfone.io | 256M | 1 |
| Backend | `git-history-backend-sit` | https://git-history-backend-sit.apps.pcfone.io | 1G | 1 |
| Config Service | `git-history-config-sit` | CUPS | - | - |
| Database | `git-history-db-sit` | MySQL | - | - |

**Access Points:**
- **Application UI**: https://git-history-sit.apps.pcfone.io
- **API Documentation**: https://git-history-backend-sit.apps.pcfone.io/docs
- **API Base URL**: https://git-history-backend-sit.apps.pcfone.io/api

---

## 🎯 Quick Command Reference

```bash
# Login
cf login -a api.system.pcfone.io
cf target -o your-org -s sit

# Services
cf services
cf service git-history-db-sit
cf env git-history-backend-sit

# Apps
cf apps
cf app git-history-backend-sit
cf logs git-history-backend-sit --recent

# Deploy
cf push -f manifest-backend-sit.yml
cf push -f manifest-frontend-sit.yml

# Restart/Restage
cf restart git-history-backend-sit
cf restage git-history-backend-sit

# Scale
cf scale git-history-backend-sit -i 2 -m 2G

# SSH
cf ssh git-history-backend-sit

# Delete
cf delete git-history-backend-sit
cf delete-service git-history-db-sit
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] CF CLI installed and configured
- [ ] Logged in to PCF SIT environment
- [ ] Credentials prepared (Git, Bitbucket)
- [ ] Node.js installed for frontend build

### Deployment
- [ ] Created CUPS service (`git-history-config-sit`)
- [ ] Created MySQL service (`git-history-db-sit`)
- [ ] Created SIT manifests
- [ ] Updated frontend environment file
- [ ] Built frontend (`npm run build`)
- [ ] Updated nginx routes.conf
- [ ] Deployed backend
- [ ] Initialized database
- [ ] Deployed frontend

### Verification
- [ ] Both apps showing `started` status
- [ ] Backend health check passing
- [ ] Frontend loads in browser
- [ ] API calls working
- [ ] No errors in logs

### Post-Deployment
- [ ] Tested database connection
- [ ] Verified API endpoints
- [ ] Tested frontend functionality
- [ ] Documented SIT URLs

---

## 🎉 Success!

Your Git History Deep Analyzer is now deployed to SIT environment!

**Next Steps:**
1. Share SIT URLs with team for testing
2. Extract Git data and populate database
3. Import staff data
4. Perform integration testing
5. Prepare for UAT/Production deployment

---

**Deployment Date**: _________________
**Deployed By**: _________________
**SIT Environment**: https://git-history-sit.apps.pcfone.io
**Status**: _________________

---

**Need Help?**
- Check [PCF_DEPLOYMENT_GUIDE.md](PCF_DEPLOYMENT_GUIDE.md) for detailed troubleshooting
- View logs: `cf logs git-history-backend-sit --recent`
- Contact PCF admin for service access issues
