@echo off
REM PCF Deployment Script for Git History Deep Analyzer (Windows)

echo.
echo ================================================
echo  Git History Deep Analyzer - PCF Deployment
echo ================================================
echo.

REM Check if cf CLI is installed
where cf >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Cloud Foundry CLI not found.
    echo Please install it from: https://github.com/cloudfoundry/cli/releases
    exit /b 1
)

REM Check if logged in to PCF
cf target >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Not logged in to Cloud Foundry.
    echo Please run: cf login
    exit /b 1
)

echo [OK] Logged in to PCF
cf target

REM Step 1: Create CUPS for configuration
echo.
echo ================================================
echo Step 1: Creating CUPS for configuration
echo ================================================
echo.

set /p CREATE_CUPS="Create/update CUPS service 'git-history-config'? (y/n): "
if /i "%CREATE_CUPS%"=="y" (
    echo Enter configuration values (press Enter to skip):
    echo.

    set /p DB_TYPE="DB Type (sqlite/mysql): "
    set /p GIT_USERNAME="Git Username: "
    set /p GIT_PASSWORD="Git Password: "
    set /p BITBUCKET_URL="Bitbucket URL: "
    set /p BITBUCKET_USERNAME="Bitbucket Username: "
    set /p BITBUCKET_APP_PASSWORD="Bitbucket App Password: "

    REM Build credentials JSON
    set CREDENTIALS={}
    if defined DB_TYPE set CREDENTIALS={"db_type":"%DB_TYPE%"}
    if defined GIT_USERNAME set CREDENTIALS={"git_username":"%GIT_USERNAME%","git_password":"%GIT_PASSWORD%"}
    if defined BITBUCKET_URL set CREDENTIALS={"bitbucket_url":"%BITBUCKET_URL%","bitbucket_username":"%BITBUCKET_USERNAME%","bitbucket_app_password":"%BITBUCKET_APP_PASSWORD%"}

    REM Check if service exists
    cf service git-history-config >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Updating existing CUPS service...
        cf update-user-provided-service git-history-config -p "%CREDENTIALS%"
    ) else (
        echo Creating new CUPS service...
        cf create-user-provided-service git-history-config -p "%CREDENTIALS%"
    )

    echo [OK] CUPS service configured
)

REM Step 2: Build frontend
echo.
echo ================================================
echo Step 2: Building frontend
echo ================================================
echo.

cd frontend

REM Update API base URL for production
echo VITE_API_BASE_URL=https://git-history-backend.apps.pcfone.io > .env.production

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo Building frontend for production...
call npm run build

if not exist "dist" (
    echo [ERROR] Frontend build failed - dist directory not found
    exit /b 1
)

echo [OK] Frontend built successfully
cd ..

REM Step 3: Deploy backend
echo.
echo ================================================
echo Step 3: Deploying backend
echo ================================================
echo.

set /p DEPLOY_BACKEND="Deploy backend now? (y/n): "
if /i "%DEPLOY_BACKEND%"=="y" (
    echo Pushing backend application...
    cf push -f manifest-backend.yml
    echo [OK] Backend deployed
)

REM Step 4: Deploy frontend
echo.
echo ================================================
echo Step 4: Deploying frontend
echo ================================================
echo.

set /p DEPLOY_FRONTEND="Deploy frontend now? (y/n): "
if /i "%DEPLOY_FRONTEND%"=="y" (
    echo Pushing frontend application...
    cf push -f manifest-frontend.yml
    echo [OK] Frontend deployed
)

REM Summary
echo.
echo ================================================
echo  Deployment Complete!
echo ================================================
echo.
echo Application URLs:
echo   Frontend: https://git-history.apps.pcfone.io
echo   Backend:  https://git-history-backend.apps.pcfone.io
echo   API Docs: https://git-history-backend.apps.pcfone.io/docs
echo.
echo Useful commands:
echo   cf logs git-history-backend --recent    - View backend logs
echo   cf logs git-history-frontend --recent   - View frontend logs
echo   cf apps                                 - List all apps
echo   cf services                             - List all services
echo.
echo Happy analyzing!
echo.

pause
