# PCF Deployment Guide - Git History Deep Analyzer

Complete guide for deploying the Git History Deep Analyzer to Pivotal Cloud Foundry (PCF).

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [CUPS Configuration](#cups-configuration)
- [Manual Deployment Steps](#manual-deployment-steps)
- [Automated Deployment](#automated-deployment)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Troubleshooting](#troubleshooting)
- [Monitoring & Logs](#monitoring--logs)
- [Scaling](#scaling)
- [CI/CD Integration](#cicd-integration)

---

## 🔧 Prerequisites

### Required Tools

1. **Cloud Foundry CLI**
   ```bash
   # Download from: https://github.com/cloudfoundry/cli/releases
   # Verify installation
   cf --version
   ```

2. **Node.js 16+** (for frontend build)
   ```bash
   node --version
   npm --version
   ```

3. **Python 3.8+** (for local testing)
   ```bash
   python --version
   ```

### PCF Access

1. **Login to PCF**
   ```bash
   cf login -a api.system.pcfone.io
   # Enter username and password
   ```

2. **Target Organization and Space**
   ```bash
   cf target -o your-org -s your-space
   ```

3. **Verify Access**
   ```bash
   cf target
   cf apps
   ```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    PCF DEPLOYMENT                        │
└─────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│  git-history-frontend│         │ git-history-backend  │
│  (Staticfile buildpack)│         │ (Python buildpack)   │
│  256MB / 1 instance  │         │ 1GB / 1 instance     │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                │
           │ binds to                       │ binds to
           ↓                                ↓
┌────────────────────────────────────────────────────────┐
│              PCF Services (CUPS)                        │
├────────────────────────────────────────────────────────┤
│  git-history-config                                     │
│  - db_type                                             │
│  - git_username / git_password                         │
│  - bitbucket_url / bitbucket_username                  │
│  - bitbucket_app_password                              │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│              MySQL Service (Optional)                   │
│  git-history-db                                         │
│  - hostname, port, username, password                  │
└────────────────────────────────────────────────────────┘
```

---

## 🔐 CUPS Configuration

### What is CUPS?

CUPS (Cloud Foundry User-Provided Service) allows you to store configuration and credentials as a service that your applications can bind to.

### Create CUPS Service

#### Method 1: Interactive (Recommended)

```bash
cf create-user-provided-service git-history-config -p "db_type, git_username, git_password, bitbucket_url, bitbucket_username, bitbucket_app_password"
```

You'll be prompted to enter each value interactively.

#### Method 2: JSON Inline

```bash
cf create-user-provided-service git-history-config -p '{
  "db_type": "mysql",
  "git_username": "your-git-username",
  "git_password": "your-git-password",
  "bitbucket_url": "https://bitbucket.yourcompany.com",
  "bitbucket_username": "your-bitbucket-username",
  "bitbucket_app_password": "your-app-password"
}'
```

#### Method 3: JSON File

Create `credentials.json`:
```json
{
  "db_type": "mysql",
  "git_username": "your-git-username",
  "git_password": "your-git-password",
  "bitbucket_url": "https://bitbucket.yourcompany.com",
  "bitbucket_username": "your-bitbucket-username",
  "bitbucket_app_password": "your-app-password"
}
```

Then create service:
```bash
cf create-user-provided-service git-history-config -p credentials.json
```

### Update CUPS Service

If you need to update credentials:

```bash
cf update-user-provided-service git-history-config -p '{
  "db_type": "mysql",
  "git_password": "new-password"
}'
```

### View CUPS Configuration

```bash
cf service git-history-config
cf env git-history-backend
```

---

## 📦 Manual Deployment Steps

### Step 1: Build Frontend

```bash
cd frontend

# Create production environment file
echo "VITE_API_BASE_URL=https://git-history-backend.apps.pcfone.io" > .env.production

# Install dependencies
npm install

# Build for production
npm run build

# Verify dist folder exists
ls -la dist/

cd ..
```

### Step 2: Deploy Backend

```bash
# Make sure you're in the project root
cf push -f manifest-backend.yml

# Wait for deployment to complete
# Check status
cf apps

# View logs
cf logs git-history-backend --recent
```

### Step 3: Deploy Frontend

```bash
cf push -f manifest-frontend.yml

# Check status
cf apps

# View logs
cf logs git-history-frontend --recent
```

### Step 4: Verify Deployment

```bash
# Test backend
curl https://git-history-backend.apps.pcfone.io/api/overview/stats

# Open frontend in browser
open https://git-history.apps.pcfone.io
```

---

## 🤖 Automated Deployment

### Using Deployment Script

#### Linux/Mac:

```bash
# Make script executable
chmod +x deploy-pcf.sh

# Run deployment
./deploy-pcf.sh
```

#### Windows:

```cmd
deploy-pcf.bat
```

The script will:
1. ✅ Check CF CLI installation and login
2. ✅ Create/update CUPS service
3. ✅ Create/bind MySQL service (optional)
4. ✅ Build frontend
5. ✅ Deploy backend
6. ✅ Deploy frontend
7. ✅ Display URLs and helpful commands

---

## 🌍 Environment Variables

### Frontend Environment Variables

**Location**: `frontend/.env.production`

```env
# Backend API URL (required)
VITE_API_BASE_URL=https://git-history-backend.apps.pcfone.io
```

### Backend Environment Variables

Backend reads from:
1. **CUPS service** (`git-history-config`)
2. **Bound MySQL service** (auto-detected via VCAP_SERVICES)
3. **Environment variables** (fallback for local development)

**Priority**: CUPS > Bound Services > Env Vars > Defaults

### Configuration Keys

| Key | CUPS Key | Description | Default |
|-----|----------|-------------|---------|
| `DB_TYPE` | `db_type` | Database type (sqlite/mysql) | sqlite |
| `GIT_USERNAME` | `git_username` | Git clone username | - |
| `GIT_PASSWORD` | `git_password` | Git clone password/token | - |
| `BITBUCKET_URL` | `bitbucket_url` | Bitbucket server URL | - |
| `BITBUCKET_USERNAME` | `bitbucket_username` | Bitbucket API username | - |
| `BITBUCKET_APP_PASSWORD` | `bitbucket_app_password` | Bitbucket API password | - |

---

## 🗄️ Database Setup

### Option 1: MySQL Service (Recommended for Production)

#### Create MySQL Service

```bash
# Check available MySQL services
cf marketplace | grep mysql

# Create service
cf create-service p-mysql db-small git-history-db

# Or for ClearDB
cf create-service cleardb spark git-history-db

# Wait for service creation
cf services

# Bind to backend (already in manifest)
cf bind-service git-history-backend git-history-db

# Restage app
cf restage git-history-backend
```

#### Initialize Database

After deploying, you'll need to initialize the database tables:

```bash
# SSH into backend container
cf ssh git-history-backend

# Run Python shell
python

# Initialize database
from models import create_tables
from config import Config
config = Config()
db_config = config.get_db_config()
create_tables(db_config)
exit()

# Exit SSH
exit
```

### Option 2: SQLite (Development Only)

For development/testing, SQLite can be used but **data will be lost on restart**.

CUPS configuration:
```json
{
  "db_type": "sqlite"
}
```

**⚠️ Warning**: SQLite in PCF is ephemeral. Use MySQL for production!

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Symptoms**: App crashes on startup

**Solution**:
```bash
# Check logs
cf logs git-history-backend --recent

# Common issues:
# - Missing CUPS service
cf services

# - Database connection failed
cf env git-history-backend

# - Dependencies missing
cf ssh git-history-backend
pip list
```

#### 2. Frontend Shows API Errors

**Symptoms**: Network errors, CORS issues

**Solution**:
```bash
# Verify backend is running
cf apps

# Test backend health
curl https://git-history-backend.apps.pcfone.io/api/overview/stats

# Check frontend environment
cat frontend/.env.production

# Verify routes.conf is being used
cf ssh git-history-frontend
cat nginx/conf/includes/routes.conf
```

#### 3. CUPS Service Not Found

**Symptoms**: `Service git-history-config not found`

**Solution**:
```bash
# List all services
cf services

# Create CUPS service
cf create-user-provided-service git-history-config -p '{...}'

# Bind to app
cf bind-service git-history-backend git-history-config

# Restage
cf restage git-history-backend
```

#### 4. Database Connection Timeout

**Symptoms**: `Database connection timeout`

**Solution**:
```bash
# Check MySQL service status
cf service git-history-db

# Verify binding
cf env git-history-backend | grep VCAP_SERVICES

# Test connection from app
cf ssh git-history-backend
python
from config import Config
config = Config()
print(config.get_db_config())
```

#### 5. Out of Memory

**Symptoms**: App keeps crashing, `Out of memory` in logs

**Solution**:
```bash
# Increase memory in manifest
# Edit manifest-backend.yml: memory: 2G

# Redeploy
cf push -f manifest-backend.yml
```

---

## 📊 Monitoring & Logs

### View Logs

```bash
# Recent logs
cf logs git-history-backend --recent
cf logs git-history-frontend --recent

# Live tail
cf logs git-history-backend
cf logs git-history-frontend

# Filter logs
cf logs git-history-backend --recent | grep ERROR
```

### App Status

```bash
# Check app health
cf apps

# Detailed app info
cf app git-history-backend

# Resource usage
cf app git-history-backend --guid
cf curl /v3/processes/$(cf app git-history-backend --guid)/stats
```

### Events

```bash
# View app events
cf events git-history-backend

# View service events
cf service git-history-db
```

### SSH Access

```bash
# SSH into container
cf ssh git-history-backend

# Run commands
cf ssh git-history-backend -c "ls -la"
cf ssh git-history-backend -c "python --version"
```

---

## 📈 Scaling

### Vertical Scaling (More Resources)

```bash
# Increase memory
cf scale git-history-backend -m 2G

# Increase disk
cf scale git-history-backend -k 2G
```

### Horizontal Scaling (More Instances)

```bash
# Scale to 3 instances
cf scale git-history-backend -i 3

# Auto-scaling (if available)
cf create-service autoscaler standard git-history-autoscaler
cf bind-service git-history-backend git-history-autoscaler
```

### Update Manifest

Edit `manifest-backend.yml`:
```yaml
applications:
  - name: git-history-backend
    memory: 2G      # Increased from 1G
    instances: 3    # Increased from 1
    disk_quota: 2G  # Optional
```

Then redeploy:
```bash
cf push -f manifest-backend.yml
```

---

## 🔄 CI/CD Integration

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any

    environment {
        CF_API = 'https://api.system.pcfone.io'
        CF_ORG = 'your-org'
        CF_SPACE = 'production'
    }

    stages {
        stage('Build Frontend') {
            steps {
                dir('frontend') {
                    sh 'npm install'
                    sh 'npm run build'
                }
            }
        }

        stage('Deploy to PCF') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'pcf-credentials',
                    usernameVariable: 'CF_USERNAME',
                    passwordVariable: 'CF_PASSWORD'
                )]) {
                    sh '''
                        cf login -a $CF_API -u $CF_USERNAME -p $CF_PASSWORD -o $CF_ORG -s $CF_SPACE
                        cf push -f manifest-backend.yml
                        cf push -f manifest-frontend.yml
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    sleep 30
                    curl -f https://git-history-backend.apps.pcfone.io/api/overview/stats
                '''
            }
        }
    }

    post {
        always {
            sh 'cf logout'
        }
    }
}
```

### GitHub Actions Example

```yaml
name: Deploy to PCF

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '16'

    - name: Build Frontend
      run: |
        cd frontend
        npm install
        echo "VITE_API_BASE_URL=https://git-history-backend.apps.pcfone.io" > .env.production
        npm run build

    - name: Install CF CLI
      run: |
        wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
        echo "deb https://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
        sudo apt-get update
        sudo apt-get install cf-cli

    - name: Deploy to PCF
      env:
        CF_USERNAME: ${{ secrets.CF_USERNAME }}
        CF_PASSWORD: ${{ secrets.CF_PASSWORD }}
      run: |
        cf login -a https://api.system.pcfone.io -u $CF_USERNAME -p $CF_PASSWORD -o your-org -s production
        cf push -f manifest-backend.yml
        cf push -f manifest-frontend.yml

    - name: Health Check
      run: |
        sleep 30
        curl -f https://git-history-backend.apps.pcfone.io/api/overview/stats
```

---

## 🔒 Security Best Practices

### 1. Use CUPS for Secrets

✅ **DO**: Store credentials in CUPS
```bash
cf create-user-provided-service git-history-config -p credentials.json
```

❌ **DON'T**: Hardcode credentials in manifest or code

### 2. Limit Service Permissions

```bash
# Use separate service accounts with minimal permissions
# For Git: Read-only access
# For Bitbucket: API access only
```

### 3. Enable HTTPS Only

Frontend manifest already includes:
```yaml
env:
  FORCE_HTTPS: "true"
```

### 4. Rotate Credentials Regularly

```bash
# Update CUPS with new credentials
cf update-user-provided-service git-history-config -p new-credentials.json

# Restage apps
cf restage git-history-backend
```

### 5. Use Private Routes (if available)

```yaml
# In manifest
routes:
  - route: git-history-backend.apps.internal
```

---

## 📝 Useful Commands Reference

### App Management

```bash
# List apps
cf apps

# App details
cf app git-history-backend

# Restart app
cf restart git-history-backend

# Restage app (rebuild)
cf restage git-history-backend

# Delete app
cf delete git-history-backend
```

### Service Management

```bash
# List services
cf services

# Service details
cf service git-history-config

# Create service
cf create-user-provided-service <name> -p <credentials>

# Update service
cf update-user-provided-service <name> -p <new-credentials>

# Delete service
cf delete-service git-history-config
```

### Environment & Configuration

```bash
# View environment
cf env git-history-backend

# Set environment variable
cf set-env git-history-backend KEY value

# Unset environment variable
cf unset-env git-history-backend KEY
```

### Logs & Debugging

```bash
# Recent logs
cf logs git-history-backend --recent

# Tail logs
cf logs git-history-backend

# SSH access
cf ssh git-history-backend

# File access
cf ssh git-history-backend -c "cat /app/config.py"
```

---

## 🎯 Quick Deployment Checklist

- [ ] Install CF CLI
- [ ] Login to PCF (`cf login`)
- [ ] Create CUPS service (`git-history-config`)
- [ ] (Optional) Create MySQL service (`git-history-db`)
- [ ] Build frontend (`cd frontend && npm run build`)
- [ ] Deploy backend (`cf push -f manifest-backend.yml`)
- [ ] Deploy frontend (`cf push -f manifest-frontend.yml`)
- [ ] Initialize database (if using MySQL)
- [ ] Verify deployment (test URLs)
- [ ] Check logs for errors

---

## 📞 Support

For issues or questions:

1. **Check logs**: `cf logs git-history-backend --recent`
2. **Verify services**: `cf services`
3. **Test connectivity**: `cf ssh git-history-backend`
4. **Review configuration**: `cf env git-history-backend`

---

**Happy Deploying! 🚀**
