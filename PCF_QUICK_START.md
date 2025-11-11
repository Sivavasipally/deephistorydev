# PCF Quick Start Guide

Get the Git History Deep Analyzer running on PCF in 10 minutes!

## ⚡ Quick Deployment (5 Commands)

```bash
# 1. Login to PCF
cf login -a api.system.pcfone.io

# 2. Create configuration service
cf create-user-provided-service git-history-config -p '{
  "db_type": "mysql",
  "git_username": "your-username",
  "git_password": "your-password",
  "bitbucket_url": "https://bitbucket.yourcompany.com",
  "bitbucket_username": "bitbucket-user",
  "bitbucket_app_password": "bitbucket-password"
}'

# 3. Build frontend
cd frontend && npm install && npm run build && cd ..

# 4. Deploy backend
cf push -f manifest-backend.yml

# 5. Deploy frontend
cf push -f manifest-frontend.yml
```

**Done!** Access your app at:
- Frontend: https://git-history.apps.pcfone.io
- Backend: https://git-history-backend.apps.pcfone.io

---

## 🎯 Using the Automated Script

### Linux/Mac:

```bash
chmod +x deploy-pcf.sh
./deploy-pcf.sh
```

### Windows:

```cmd
deploy-pcf.bat
```

The script will guide you through:
1. ✅ Creating CUPS service
2. ✅ Setting up MySQL (optional)
3. ✅ Building frontend
4. ✅ Deploying both apps

---

## 🔧 Configuration Options

### Minimal Configuration (SQLite - Dev Only)

```bash
cf create-user-provided-service git-history-config -p '{
  "db_type": "sqlite"
}'
```

⚠️ **Warning**: SQLite data is ephemeral in PCF. Use MySQL for production!

### Production Configuration (MySQL)

```bash
# 1. Create MySQL service
cf create-service p-mysql db-small git-history-db

# 2. Create config service
cf create-user-provided-service git-history-config -p '{
  "db_type": "mysql",
  "git_username": "git-user",
  "git_password": "git-pass",
  "bitbucket_url": "https://bitbucket.company.com",
  "bitbucket_username": "bb-user",
  "bitbucket_app_password": "bb-pass"
}'

# 3. Deploy (MySQL will be auto-detected)
cf push -f manifest-backend.yml
cf push -f manifest-frontend.yml
```

---

## 📋 Pre-Deployment Checklist

- [ ] CF CLI installed (`cf --version`)
- [ ] Logged in to PCF (`cf login`)
- [ ] Node.js installed (`node --version`)
- [ ] Git credentials ready
- [ ] Bitbucket credentials ready (if using)

---

## 🚀 First Time Setup

### 1. Install CF CLI

**Mac (Homebrew):**
```bash
brew install cloudfoundry/tap/cf-cli
```

**Windows (Chocolatey):**
```cmd
choco install cloudfoundry-cli
```

**Linux:**
```bash
wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
echo "deb https://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
sudo apt-get update
sudo apt-get install cf-cli
```

### 2. Login to PCF

```bash
cf login -a api.system.pcfone.io
# Enter your username and password
# Select org and space
```

### 3. Verify Access

```bash
cf target
cf apps
cf marketplace
```

---

## 🔑 Creating CUPS Service

### Interactive Mode (Recommended for First Time)

```bash
cf create-user-provided-service git-history-config -p "db_type, git_username, git_password, bitbucket_url, bitbucket_username, bitbucket_app_password"
```

You'll be prompted for each value. You can skip optional ones by pressing Enter.

### From JSON File (Recommended for CI/CD)

Create `credentials.json`:
```json
{
  "db_type": "mysql",
  "git_username": "your-git-user",
  "git_password": "your-git-token",
  "bitbucket_url": "https://bitbucket.yourcompany.com",
  "bitbucket_username": "your-bb-user",
  "bitbucket_app_password": "your-bb-app-password"
}
```

Then:
```bash
cf create-user-provided-service git-history-config -p credentials.json
```

---

## 🗄️ Database Setup

### Option 1: MySQL (Production)

```bash
# Check available MySQL plans
cf marketplace -s p-mysql

# Create MySQL service
cf create-service p-mysql db-small git-history-db

# Wait for creation (check status)
cf services

# Service will auto-bind via manifest
```

### Option 2: SQLite (Development)

No additional setup needed. Just set `db_type: "sqlite"` in CUPS.

⚠️ **Data will be lost on app restart!**

---

## 🏗️ Build & Deploy

### 1. Build Frontend

```bash
cd frontend

# Create production config
echo "VITE_API_BASE_URL=https://git-history-backend.apps.pcfone.io" > .env.production

# Install and build
npm install
npm run build

# Verify
ls -la dist/

cd ..
```

### 2. Deploy Backend

```bash
cf push -f manifest-backend.yml

# Monitor deployment
cf logs git-history-backend

# Check status
cf app git-history-backend
```

### 3. Deploy Frontend

```bash
cf push -f manifest-frontend.yml

# Check status
cf app git-history-frontend
```

---

## ✅ Verify Deployment

### Check App Status

```bash
cf apps
```

Should show both apps as `running`.

### Test Backend API

```bash
curl https://git-history-backend.apps.pcfone.io/api/overview/stats
```

Should return JSON with stats.

### Test Frontend

Open in browser:
```
https://git-history.apps.pcfone.io
```

### Check Logs

```bash
# Backend logs
cf logs git-history-backend --recent

# Frontend logs
cf logs git-history-frontend --recent
```

---

## 🔄 Update Configuration

### Update CUPS Service

```bash
cf update-user-provided-service git-history-config -p '{
  "db_type": "mysql",
  "git_password": "new-password"
}'

# Restage app to pick up changes
cf restage git-history-backend
```

### Update Environment Variables

```bash
# Set env var
cf set-env git-history-backend CUSTOM_VAR value

# Restage
cf restage git-history-backend
```

---

## 🔍 Troubleshooting

### App Won't Start

```bash
# Check logs
cf logs git-history-backend --recent

# Common fixes:
# 1. Verify CUPS service exists
cf services

# 2. Check bindings
cf env git-history-backend

# 3. Verify dependencies
cf ssh git-history-backend
pip list
```

### Database Connection Failed

```bash
# For MySQL: Check service status
cf service git-history-db

# View connection details
cf env git-history-backend | grep VCAP_SERVICES

# Test from app
cf ssh git-history-backend
python
from config import Config
config = Config()
print(config.get_db_config())
```

### Frontend Shows 404 on Routes

This is already handled by `includes/routes.conf` which configures nginx for SPA routing.

If issues persist:
```bash
cf ssh git-history-frontend
cat nginx/conf/includes/routes.conf
```

---

## 📊 Common Commands

```bash
# View apps
cf apps

# View services
cf services

# View logs
cf logs git-history-backend --recent

# Restart app
cf restart git-history-backend

# Scale app
cf scale git-history-backend -i 2 -m 2G

# SSH into app
cf ssh git-history-backend

# Delete app
cf delete git-history-backend

# Update service
cf update-user-provided-service git-history-config -p new-creds.json
```

---

## 🎯 Next Steps

After successful deployment:

1. **Initialize Database** (if using MySQL)
   ```bash
   cf ssh git-history-backend
   python
   from models import create_tables
   from config import Config
   config = Config()
   create_tables(config.get_db_config())
   ```

2. **Extract Git Data**
   - You'll need to do this from a local machine or CI/CD
   - Use `cli.py extract` to populate the database

3. **Import Staff Data**
   ```bash
   python cli.py import-staff staff_data.xlsx
   ```

4. **Access the Application**
   - Frontend: https://git-history.apps.pcfone.io
   - Backend API: https://git-history-backend.apps.pcfone.io
   - API Docs: https://git-history-backend.apps.pcfone.io/docs

---

## 📚 Additional Resources

- [Full PCF Deployment Guide](PCF_DEPLOYMENT_GUIDE.md)
- [Application README](README.md)
- [Cloud Foundry Docs](https://docs.cloudfoundry.org/)

---

**Happy Deploying! 🚀**
