# 🚀 Quick Start

## Step 1: Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies (in a new terminal)
cd frontend
npm install
```

## Step 2: Configure Environment

Make sure your `.env` file is configured with database credentials.

## Step 3: Start the Application

### Option A: One-Click Start (Recommended)

**Windows:**
```bash
start-dev.bat
```

**Linux/Mac:**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

### Option B: Manual Start (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Step 4: Access Dashboard

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

---

## ✅ Verification

After starting, verify everything works:

1. **Backend Health**: Visit http://localhost:8000/api/health
2. **API Docs**: Visit http://localhost:8000/api/docs
3. **Frontend**: Visit http://localhost:3000

---

## 📚 Documentation

- **Full Setup Guide**: [REACT_FASTAPI_SETUP.md](REACT_FASTAPI_SETUP.md)
- **Quick Reference**: [QUICK_START.md](QUICK_START.md)
- **Frontend Options**: [FRONTEND_OPTIONS.md](FRONTEND_OPTIONS.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## 🐛 Troubleshooting

### "ModuleNotFoundError" in backend
```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Kill the process using the port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

**Need help?** Check the full documentation or API docs!
