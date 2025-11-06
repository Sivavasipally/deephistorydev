# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites Check
```bash
# Check Python version (need 3.8+)
python --version

# Check Node.js (need 16+)
node --version

# Check npm
npm --version
```

If any are missing, install them first.

---

## Option 1: React + FastAPI (Modern)

### 1️⃣ Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2️⃣ Configure Environment

Create/edit `.env` file:
```env
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=git_history
```

### 3️⃣ Start Servers

**Windows:**
```bash
start-dev.bat
```

**Linux/Mac:**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

### 4️⃣ Access Dashboard

Open browser: **http://localhost:3000**

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

---

## Option 2: Streamlit (Simple)

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Configure Environment
Same as above (.env file)

### 3️⃣ Start Dashboard
```bash
streamlit run dashboard.py
```

### 4️⃣ Access Dashboard
Open browser: **http://localhost:8501**

---

## 📊 First Time Setup

### Import Data

**1. Extract Git History:**
```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run extraction
python cli.py extract repositories.csv
```

**2. Import Staff Details (optional):**
```bash
python cli.py import-staff staff_details.xlsx
```

---

## 🎯 Quick Commands

### Backend (FastAPI)
```bash
# Start
cd backend
python main.py

# With hot reload
uvicorn backend.main:app --reload

# Check health
curl http://localhost:8000/api/health
```

### Frontend (React)
```bash
# Development
cd frontend
npm run dev

# Production build
npm run build

# Preview production
npm run preview
```

### Streamlit
```bash
# Start
streamlit run dashboard.py

# Custom port
streamlit run dashboard.py --server.port 8502
```

---

## 📁 Project Structure Quick Reference

```
deephistorydev/
├── cli.py              # Extract & import data
├── dashboard.py        # Streamlit UI (option 1)
├── backend/
│   └── main.py        # FastAPI server (option 2)
├── frontend/
│   └── src/           # React app (option 2)
├── models.py          # Database schemas
└── .env              # Configuration
```

---

## 🔑 Key URLs

### React + FastAPI
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Streamlit
- **Dashboard**: http://localhost:8501

---

## 🐛 Common Issues

### "Port already in use"

**Backend (8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (3000):**
```bash
# Kill and restart
# Or change port in vite.config.js
```

### "Module not found"

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules
npm install
```

### "Database connection error"

1. Check MariaDB is running
2. Verify credentials in `.env`
3. Test connection:
   ```bash
   mysql -h localhost -u root -p
   ```

---

## 📖 Next Steps

1. **Explore Dashboard**: Navigate through all 9 pages
2. **Try SQL Executor**: Use AI to generate queries
3. **Create Mappings**: Map authors to staff
4. **Export Data**: Download CSVs for reports
5. **Read Docs**: Check full setup guides

---

## 📚 Documentation

- **Full Setup**: [REACT_FASTAPI_SETUP.md](REACT_FASTAPI_SETUP.md)
- **Options**: [FRONTEND_OPTIONS.md](FRONTEND_OPTIONS.md)
- **Implementation**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Original**: [README.md](README.md)

---

## 🎓 Help & Support

- **API Docs**: http://localhost:8000/api/docs
- **Console**: Press F12 in browser
- **Logs**: Check terminal output

---

**Pro Tip**: Start with Streamlit if you want simplicity, use React + FastAPI for production! 🚀
