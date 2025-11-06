# 🚀 How to Start the Application

## ✅ Correct Way to Start Backend

The backend **must be run from the root directory**, not from the `backend/` directory.

### ❌ WRONG (will cause import errors):
```bash
cd backend
python main.py  # ❌ Don't do this!
```

### ✅ CORRECT:

**Option 1: Use the startup script (Easiest)**
```bash
# From the root directory (deephistorydev/)
python start_backend.py
```

**Option 2: Use uvicorn directly**
```bash
# From the root directory (deephistorydev/)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Use the batch file (Windows)**
```bash
# From the root directory (deephistorydev/)
start-dev.bat
```

---

## 📁 Important: Working Directory

**Always run commands from the project root directory:**
```
D:\GenAi\deephistorydev\  ← Run from here
├── backend/
├── frontend/
├── start_backend.py     ← Use this to start backend
├── start-dev.bat        ← Or use this
└── venv/
```

**NOT from:**
```
D:\GenAi\deephistorydev\backend\  ← Don't run from here
```

---

## 🎯 Complete Startup Process

### Step 1: Open Terminal in Root Directory

**Windows Command Prompt:**
```bash
cd D:\GenAi\deephistorydev
```

**Or open VS Code and use integrated terminal** (automatically opens in root)

### Step 2: Activate Virtual Environment

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Start Backend

```bash
# Use the startup script
python start_backend.py
```

You should see:
```
============================================================
  Git History Analysis API - Backend Server
============================================================

Starting FastAPI server...
  - URL: http://localhost:8000
  - API Docs: http://localhost:8000/api/docs
  - ReDoc: http://localhost:8000/api/redoc

Press Ctrl+C to stop the server
============================================================

INFO:     Started reloader process...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Start Frontend (New Terminal)

```bash
# Open a new terminal
cd D:\GenAi\deephistorydev\frontend
npm run dev
```

You should see:
```
  VITE v5.0.7  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## 🎬 Quick Start (One Command)

**Windows:**
```bash
# From root directory
start-dev.bat
```

**Linux/Mac:**
```bash
# From root directory
chmod +x start-dev.sh
./start-dev.sh
```

This automatically:
1. ✅ Starts backend from correct directory
2. ✅ Starts frontend
3. ✅ Opens both in separate windows

---

## 🌐 Access URLs

Once both servers are running:

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/api/docs |
| **Health Check** | http://localhost:8000/api/health |

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'config'"

**Cause**: You're running from the wrong directory

**Solution**:
```bash
# Make sure you're in the root directory
pwd  # Should show: /path/to/deephistorydev

# Start backend correctly
python start_backend.py
```

### Error: "WARNING: You must pass the application as an import string"

**Cause**: Trying to run `python backend/main.py` directly

**Solution**: Use `python start_backend.py` from root directory instead

### Backend starts but API doesn't work

**Check**:
1. Visit http://localhost:8000/api/health
2. Check terminal for errors
3. Verify database is running

---

## 📝 Summary

**Golden Rule**: Always work from the project root directory!

```bash
# ✅ CORRECT
cd D:\GenAi\deephistorydev
python start_backend.py

# ❌ WRONG
cd D:\GenAi\deephistorydev\backend
python main.py
```

---

## 🎓 Why This Matters

The backend needs to import modules from the parent directory:
- `config.py`
- `models.py`
- `git_analyzer.py`

When you run from `backend/`, Python can't find these files.

When you run from the root with `python start_backend.py`, the path is set up correctly and everything works! ✨

---

**Happy coding!** 🚀
