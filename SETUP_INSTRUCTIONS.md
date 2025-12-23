# LUMEN Setup Instructions

## ❌ Error: npm is not recognized

You're seeing this error because Node.js is not installed on your system.

---

## ✅ Solution: Install Node.js

### Step 1: Download Node.js
Visit: **https://nodejs.org/**

**Recommended:** Download **Node.js v20.x LTS** (Long Term Support)

### Step 2: Install Node.js
1. Run the downloaded installer
2. Accept the license agreement
3. Keep default settings (includes npm)
4. ✅ Check "Automatically install necessary tools" if prompted
5. Click "Install"

### Step 3: Verify Installation
Open a **NEW** PowerShell terminal and run:
```powershell
node --version   # Should show v20.x.x or similar
npm --version    # Should show 10.x.x or similar
```

### Step 4: Run Frontend
```powershell
# From project root
.\start_frontend.bat

# OR manually:
cd frontend
npm install
npm run dev
```

---

## 📦 Complete Setup Checklist

### Backend Requirements
- ✅ Python 3.10+ installed
- ✅ pip installed
- ✅ Run: `pip install -r requirements.txt`
- ⏳ Gemini API key (add to `.env`)
- ⏳ GPU drivers (for local AI models)

### Frontend Requirements  
- ⏳ **Node.js v20.x+ installed** ← You are here
- ⏳ npm installed (comes with Node.js)
- ⏳ Run: `cd frontend && npm install`

### AI Models (Optional for MVP)
- ⏳ XTTS v2 checkpoints
- ⏳ SadTalker checkpoints
- ⏳ Reference assets (avatar.jpg, reference_voice.wav)

---

## 🚀 Quick Start (After Node.js Installation)

### Terminal 1: Backend
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Start backend server
python backend/run.py
```

### Terminal 2: Frontend
```powershell
# Install Node.js dependencies
cd frontend
npm install

# Start frontend dev server
npm run dev
```

### Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🔧 Troubleshooting

### Issue: "npm not recognized" after Node.js installation
**Solution:**
1. Close all PowerShell/CMD windows
2. Open a NEW terminal
3. Try again (PATH updated after restart)

### Issue: Node.js version too old
**Solution:**
```powershell
# Check current version
node --version

# If < v18, download latest LTS from nodejs.org
```

### Issue: npm install fails with permission errors
**Solution:**
```powershell
# Run PowerShell as Administrator
# OR clear npm cache
npm cache clean --force
```

### Issue: Port 3000 already in use
**Solution:**
```powershell
# Use different port
npm run dev -- -p 3001

# OR kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

## 📚 Additional Resources

- [Node.js Official Docs](https://nodejs.org/docs)
- [npm Documentation](https://docs.npmjs.com/)
- [Next.js Getting Started](https://nextjs.org/docs/getting-started)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 🎯 Next Steps After Setup

1. ✅ Install Node.js
2. ✅ Run `.\start_frontend.bat`
3. ✅ Verify both servers running
4. ⏳ Add Gemini API key to `.env`
5. ⏳ Test chat interface at http://localhost:3000
6. ⏳ Download AI model checkpoints
7. ⏳ Add reference media files
8. ⏳ Uncomment TODO sections in AI code

---

**Current Status:** Frontend requires Node.js installation to proceed.

**Estimated Time:** 5-10 minutes for Node.js installation + 2-3 minutes for npm install
