# 🔧 Troubleshooting Guide

## Error: "The requested module does not provide an export named 'overviewAPI'"

### Symptoms
- Frontend shows: `Uncaught SyntaxError: The requested module '/src/services/api.js' does not provide an export named 'overviewAPI'`
- WebSocket connection errors to port 3001

### Cause
This is typically a **Vite dev server caching issue** or the dev server isn't running properly.

### Solutions (Try in order)

#### Solution 1: Restart Vite Dev Server (Quickest)
```bash
# In the frontend terminal, press Ctrl+C to stop, then:
npm run dev
```

#### Solution 2: Clear Vite Cache
```bash
cd frontend

# Stop the dev server (Ctrl+C), then:
rm -rf node_modules/.vite
npm run dev

# Windows:
rmdir /s /q node_modules\.vite
npm run dev
```

#### Solution 3: Full Clean Reinstall
```bash
cd frontend

# Stop the dev server (Ctrl+C), then:
rm -rf node_modules package-lock.json node_modules/.vite
npm install
npm run dev

# Windows:
rmdir /s /q node_modules
del package-lock.json
npm install
npm run dev
```

#### Solution 4: Hard Refresh in Browser
- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Or open DevTools (F12) → Right-click refresh button → "Empty Cache and Hard Reload"

---

## WebSocket Connection Errors

### Symptoms
- `WebSocket connection to 'ws://localhost:3001/' failed`
- `GET http://localhost:3001/ net::ERR_CONNECTION_REFUSED`

### Cause
Vite HMR (Hot Module Replacement) can't connect, usually because:
1. Dev server crashed or stopped
2. Port conflict
3. Firewall blocking connection

### Solutions

#### Check if Frontend is Running
```bash
# Should show process on port 3000
netstat -ano | findstr :3000

# If nothing, start frontend:
cd frontend
npm run dev
```

#### Check for Port Conflicts
```bash
# Check if port 3000 or 5173 is in use
netstat -ano | findstr :3000
netstat -ano | findstr :5173

# Kill process if needed (Windows):
taskkill /PID <PID_NUMBER> /F
```

---

## Backend Not Responding

### Symptoms
- Frontend loads but API calls fail
- `/api/overview/stats` returns 404 or timeout

### Solutions

#### Check Backend is Running
```bash
# Visit in browser:
http://localhost:8000/api/docs

# Or check with curl:
curl http://localhost:8000/api/health
```

#### Restart Backend
```bash
# From root directory:
python start_backend.py

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Check Backend Logs
Look for errors in the terminal where backend is running:
- Import errors → Run from root directory
- Database errors → Check database connection
- Port in use → Stop other process on port 8000

---

## Complete Fresh Start

If nothing else works, do a complete restart:

### Step 1: Stop Everything
```bash
# Press Ctrl+C in both terminals (backend and frontend)
```

### Step 2: Clean Frontend
```bash
cd frontend
rm -rf node_modules/.vite
```

### Step 3: Start Backend
```bash
# From root directory:
python start_backend.py

# Wait for: "INFO: Application startup complete"
```

### Step 4: Start Frontend
```bash
# In new terminal:
cd frontend
npm run dev

# Wait for: "VITE ready in XXX ms"
```

### Step 5: Open Browser
```bash
# Visit:
http://localhost:3000

# Hard refresh with Ctrl+Shift+R
```

---

## Quick Check Commands

### Verify All Services
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend running
curl http://localhost:3000

# Check processes
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

---

## Common Import Errors

### "Cannot find module X"
**Frontend**: Clear node_modules/.vite cache
**Backend**: Run from root directory, not backend/

### "Module has no export named X"
**Frontend**: Restart Vite dev server
**Backend**: Check if router is registered in main.py

---

## Still Having Issues?

1. Check both terminal windows for error messages
2. Verify you're in the correct directory
3. Ensure Python venv is activated for backend
4. Try the "Complete Fresh Start" section above
5. Check if antivirus/firewall is blocking ports 3000 or 8000

---

**Most Common Fix**: Just restart the Vite dev server! 🔄
