# 🚀 AIRMS Complete System Setup Guide

This guide explains how to run the complete AIRMS system with all three applications running simultaneously.

## 🌐 **Complete Port Configuration**

| Application | Port | URL | Technology | Purpose |
|-------------|------|-----|------------|---------|
| **Backend API** | 8000 | http://localhost:8000 | Python/FastAPI | Core API, authentication, risk detection |
| **Frontend App** | 3000 | http://localhost:3000 | Next.js/React | Main application, dashboard, user interface |
| **Landing Page** | 3001 | http://localhost:3001 | React/Vite | Marketing page with login buttons |

## 🎯 **Quick Start (Recommended)**

### **Option 1: One-Click Startup Scripts**

#### **For Windows Users:**
1. **Double-click** `start-all-apps-simple.bat` in the root folder (Recommended)
2. **Or run PowerShell script**: `.\start-all-apps-simple.ps1`
3. **Alternative scripts**: `start-all-apps.bat` or `.\start-all-apps.ps1`

This will automatically:
- ✅ Check Python, Node.js, and npm installation
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Start all three applications in separate terminal windows
- ✅ Open each app on the correct port

#### **For Mac/Linux Users:**
```bash
# Make script executable
chmod +x start-all-apps.ps1

# Run the script
./start-all-apps.ps1
```

### **Option 2: Manual Setup**

#### **1. Start Backend (Python/FastAPI) - Port 8000**
```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
python run.py
```

#### **2. Start Frontend (Next.js) - Port 3000**
```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

#### **3. Start Landing Page (React/Vite) - Port 3001**
```bash
cd landing

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

## 🔗 **Complete System Flow**

```
User Journey:
1. User visits landing page (localhost:3001)
2. Clicks login/signup button
3. New tab opens to frontend (localhost:3000)
4. Frontend authenticates with backend API (localhost:8000)
5. User accesses dashboard and features
6. Landing page remains open for reference
```

## 🎨 **Application Features**

### **Backend (Port 8000)**
- **FastAPI REST API** with automatic documentation
- **JWT Authentication** system
- **Risk Detection Engine** (PII, bias, adversarial, hallucination)
- **Database Integration** (PostgreSQL, MySQL, Supabase)
- **API Documentation**: http://localhost:8000/docs

### **Frontend (Port 3000)**
- **Next.js Application** with TypeScript
- **User Authentication** and dashboard
- **Risk Analysis** interface
- **Settings** and configuration
- **Responsive Design** for all devices

### **Landing Page (Port 3001)**
- **Marketing Website** with 3D animations
- **Multiple Login Entry Points** throughout the page
- **Feature Showcase** and testimonials
- **Responsive Design** with modern UI
- **Floating Action Button** for quick access

## 🛠️ **Prerequisites**

### **Required Software:**
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Git** (for cloning the repository)

### **System Requirements:**
- **RAM**: 4GB+ recommended
- **Storage**: 2GB+ free space
- **OS**: Windows 10+, macOS 10.15+, or Linux

## 🔧 **Configuration Files**

### **Backend Configuration**
- **Port**: Set in `backend/app/core/config.py`
- **Database**: Configure in environment variables
- **API Keys**: Set in `.env` file

### **Frontend Configuration**
- **Port**: Set in `frontend/next.config.ts`
- **API Endpoint**: Configure to point to backend (localhost:8000)

### **Landing Page Configuration**
- **Port**: Set in `landing/vite.config.ts` (currently 3001)
- **Frontend URL**: All buttons redirect to localhost:3000

## 🚨 **Troubleshooting**

### **Port Already in Use**
```bash
# Check what's running on each port
# Windows:
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :3001

# Mac/Linux:
lsof -i :8000
lsof -i :3000
lsof -i :3001
```

### **Python Issues**
```bash
# Clear pip cache
pip cache purge

# Reinstall virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### **Node.js Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### **Common Error Solutions**

#### **"Module not found" errors:**
- Ensure virtual environment is activated for Python
- Ensure `node_modules` exists for Node.js apps

#### **"Port already in use" errors:**
- Kill the process using the port
- Or change ports in configuration files

#### **"Permission denied" errors:**
- Run as administrator (Windows)
- Use `sudo` (Mac/Linux)

## 📋 **Development Workflow**

### **Daily Development:**
1. **Start all applications** using the startup script
2. **Develop backend features** at localhost:8000
3. **Develop frontend features** at localhost:3000
4. **Update landing page** at localhost:3001
5. **Test complete user flow** between all applications

### **Testing Checklist:**
- [ ] Backend API responds on port 8000
- [ ] Frontend loads on port 3000
- [ ] Landing page loads on port 3001
- [ ] Login buttons redirect correctly
- [ ] API calls work between frontend and backend
- [ ] All responsive designs work properly

## 🚀 **Deployment Notes**

### **Production Deployment:**
- **Backend**: Deploy to cloud platforms (AWS, Azure, GCP)
- **Frontend**: Deploy to Vercel, Netlify, or similar
- **Landing Page**: Deploy to static hosting services
- **Update URLs**: Change localhost references to production domains

### **Environment Variables:**
- Set production database URLs
- Configure API keys and secrets
- Update CORS settings for production domains

## 📞 **Support & Resources**

### **Documentation:**
- **Backend**: Check `backend/COMPLETE_WORKFLOW_README.md`
- **Frontend**: Check `frontend/README.md`
- **Landing Page**: Check `landing/README.md`

### **API Testing:**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### **Getting Help:**
1. Check browser console for frontend errors
2. Check terminal output for backend errors
3. Verify all applications are running on correct ports
4. Ensure all dependencies are installed
5. Check the troubleshooting section above

## 🎉 **Success Indicators**

When everything is working correctly:
- ✅ Backend shows "Uvicorn running on http://0.0.0.0:8000"
- ✅ Frontend shows "Ready - started server on 0.0.0.0:3000"
- ✅ Landing page shows "Local: http://localhost:3001/"
- ✅ All three URLs open in browser without errors
- ✅ Login buttons redirect to frontend application
- ✅ API documentation loads at localhost:8000/docs

---

**Happy coding! 🚀** Your complete AIRMS system should now be running on all three ports!
