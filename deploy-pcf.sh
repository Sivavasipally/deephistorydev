#!/bin/bash
# PCF Deployment Script for Git History Deep Analyzer

set -e

echo "🚀 Git History Deep Analyzer - PCF Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if cf CLI is installed
if ! command -v cf &> /dev/null; then
    echo -e "${RED}❌ Cloud Foundry CLI not found. Please install it first.${NC}"
    echo "   Download from: https://github.com/cloudfoundry/cli/releases"
    exit 1
fi

# Check if logged in to PCF
if ! cf target &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Cloud Foundry.${NC}"
    echo "   Please run: cf login"
    exit 1
fi

echo -e "${GREEN}✓ Logged in to PCF${NC}"
cf target

# Step 1: Create CUPS for configuration
echo ""
echo "📦 Step 1: Creating CUPS for configuration..."
echo "----------------------------------------------"

read -p "Do you want to create/update CUPS service 'git-history-config'? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Enter configuration values (press Enter to skip):"

    read -p "DB Type (sqlite/mysql): " DB_TYPE
    read -p "Git Username: " GIT_USERNAME
    read -sp "Git Password: " GIT_PASSWORD
    echo
    read -p "Bitbucket URL: " BITBUCKET_URL
    read -p "Bitbucket Username: " BITBUCKET_USERNAME
    read -sp "Bitbucket App Password: " BITBUCKET_APP_PASSWORD
    echo

    # Build credentials JSON
    CREDENTIALS="{"
    [[ -n "$DB_TYPE" ]] && CREDENTIALS+="\"db_type\":\"$DB_TYPE\","
    [[ -n "$GIT_USERNAME" ]] && CREDENTIALS+="\"git_username\":\"$GIT_USERNAME\","
    [[ -n "$GIT_PASSWORD" ]] && CREDENTIALS+="\"git_password\":\"$GIT_PASSWORD\","
    [[ -n "$BITBUCKET_URL" ]] && CREDENTIALS+="\"bitbucket_url\":\"$BITBUCKET_URL\","
    [[ -n "$BITBUCKET_USERNAME" ]] && CREDENTIALS+="\"bitbucket_username\":\"$BITBUCKET_USERNAME\","
    [[ -n "$BITBUCKET_APP_PASSWORD" ]] && CREDENTIALS+="\"bitbucket_app_password\":\"$BITBUCKET_APP_PASSWORD\""
    CREDENTIALS+="}"

    # Remove trailing comma if exists
    CREDENTIALS=$(echo $CREDENTIALS | sed 's/,}/}/')

    # Check if service exists
    if cf service git-history-config &> /dev/null; then
        echo "Updating existing CUPS service..."
        cf update-user-provided-service git-history-config -p "$CREDENTIALS"
    else
        echo "Creating new CUPS service..."
        cf create-user-provided-service git-history-config -p "$CREDENTIALS"
    fi

    echo -e "${GREEN}✓ CUPS service configured${NC}"
fi

# Step 2: Create or bind MySQL service (optional)
echo ""
echo "🗄️  Step 2: Database service setup..."
echo "--------------------------------------"

read -p "Do you want to create/bind MySQL service? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "MySQL service name (default: git-history-db): " DB_SERVICE_NAME
    DB_SERVICE_NAME=${DB_SERVICE_NAME:-git-history-db}

    if ! cf service $DB_SERVICE_NAME &> /dev/null; then
        echo "Available MySQL service plans:"
        cf marketplace -s p-mysql || cf marketplace -s cleardb

        read -p "Enter service plan (e.g., db-small): " SERVICE_PLAN

        echo "Creating MySQL service..."
        cf create-service p-mysql $SERVICE_PLAN $DB_SERVICE_NAME || \
        cf create-service cleardb $SERVICE_PLAN $DB_SERVICE_NAME

        echo "Waiting for service to be created..."
        sleep 30
    fi

    echo -e "${GREEN}✓ Database service ready${NC}"
fi

# Step 3: Build frontend
echo ""
echo "🏗️  Step 3: Building frontend..."
echo "--------------------------------"

cd frontend

# Update API base URL for production
echo "VITE_API_BASE_URL=https://git-history-backend.apps.pcfone.io" > .env.production

# Install dependencies and build
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Building frontend for production..."
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Frontend build failed - dist directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend built successfully${NC}"
cd ..

# Step 4: Deploy backend
echo ""
echo "🚀 Step 4: Deploying backend..."
echo "-------------------------------"

read -p "Deploy backend now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing backend application..."
    cf push -f manifest-backend.yml

    echo -e "${GREEN}✓ Backend deployed${NC}"

    # Get backend URL
    BACKEND_URL=$(cf app git-history-backend | grep routes | awk '{print $2}')
    echo "Backend URL: https://$BACKEND_URL"
fi

# Step 5: Deploy frontend
echo ""
echo "🚀 Step 5: Deploying frontend..."
echo "--------------------------------"

read -p "Deploy frontend now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing frontend application..."
    cf push -f manifest-frontend.yml

    echo -e "${GREEN}✓ Frontend deployed${NC}"

    # Get frontend URL
    FRONTEND_URL=$(cf app git-history-frontend | grep routes | awk '{print $2}')
    echo "Frontend URL: https://$FRONTEND_URL"
fi

# Step 6: Summary
echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "Application URLs:"
echo "  Frontend: https://git-history.apps.pcfone.io"
echo "  Backend:  https://git-history-backend.apps.pcfone.io"
echo "  API Docs: https://git-history-backend.apps.pcfone.io/docs"
echo ""
echo "Useful commands:"
echo "  cf logs git-history-backend --recent    # View backend logs"
echo "  cf logs git-history-frontend --recent   # View frontend logs"
echo "  cf apps                                 # List all apps"
echo "  cf services                             # List all services"
echo "  cf env git-history-backend              # View backend environment"
echo ""
echo "To update configuration:"
echo "  cf update-user-provided-service git-history-config -p '{\"key\":\"value\"}'"
echo ""
echo -e "${GREEN}Happy analyzing! 🎉${NC}"
