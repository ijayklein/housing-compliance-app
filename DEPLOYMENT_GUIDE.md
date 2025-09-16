# 🚀 Deployment Guide - Housing Compliance Web App

## 🎯 **QUICK START: Best Options**

### **🔥 Option 1: Render (Recommended - Easiest)**

**Why Render?**
- ✅ **FREE** 750 hours/month (enough for most use)
- ✅ **Zero configuration** - just connect GitHub
- ✅ **Automatic HTTPS** and custom domains
- ✅ **Built-in CI/CD** from your repo

**Steps:**
1. **Push to GitHub** (see GitHub setup below)
2. **Go to [render.com](https://render.com)** and sign up
3. **Connect GitHub** repo: `cityrules`
4. **Auto-detected:** Python app with `render.yaml`
5. **Deploy!** - Gets URL like `https://housing-compliance-xyz.onrender.com`

**Time to deploy:** ~5 minutes

---

### **⚡ Option 2: Railway (Most Modern)**

**Why Railway?**
- ✅ **$5 credit/month** free (covers small apps)
- ✅ **One-click deploy** from GitHub
- ✅ **Beautiful dashboard** and monitoring
- ✅ **Instant custom domains**

**Steps:**
1. **Push to GitHub** (see GitHub setup below)
2. **Go to [railway.app](https://railway.app)** and sign up
3. **"Deploy from GitHub"** → Select your repo
4. **Auto-deploys** with `railway.json` config
5. **Get URL** like `https://housing-compliance-production.up.railway.app`

**Time to deploy:** ~3 minutes

---

### **☁️ Option 3: Google Cloud Run (Scalable)**

**Why Cloud Run?**
- ✅ **Generous free tier** (2M requests/month)
- ✅ **Pay only for usage** (can be $0/month)
- ✅ **Enterprise-grade** performance
- ✅ **Auto-scaling** to handle traffic spikes

**Steps:**
1. **Install Google Cloud CLI**
2. **Build container:** `docker build -t housing-compliance .`
3. **Deploy:** `gcloud run deploy --source .`
4. **Get URL** like `https://housing-compliance-xyz-uc.a.run.app`

**Time to deploy:** ~10 minutes

---

## 📋 **STEP-BY-STEP: GitHub + Render Deployment**

### **Step 1: Prepare for GitHub**

```bash
# Navigate to your project
cd /Users/jayklein/Documents/rulestracking/cityrules

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Housing Compliance Web Application"
```

### **Step 2: Create GitHub Repository**

1. **Go to [github.com](https://github.com)** and sign in
2. **Click "New repository"**
3. **Repository name:** `housing-compliance-app`
4. **Description:** "Web application for Palo Alto housing compliance with planning and validation modes"
5. **Set to Public** (or Private if you prefer)
6. **Don't initialize** with README (we have files already)
7. **Click "Create repository"**

### **Step 3: Push to GitHub**

```bash
# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/housing-compliance-app.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### **Step 4: Deploy on Render**

1. **Go to [render.com](https://render.com)** and sign up with GitHub
2. **Click "New +"** → **"Web Service"**
3. **Connect your repository:** `housing-compliance-app`
4. **Render auto-detects:**
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
5. **Click "Deploy Web Service"**
6. **Wait ~5 minutes** for build and deploy
7. **Get your URL:** `https://housing-compliance-app.onrender.com`

**🎉 Your app is now live on the internet!**

---

## 🔧 **CONFIGURATION FILES INCLUDED**

I've created all necessary deployment files for you:

- ✅ `render.yaml` - Render platform configuration
- ✅ `Procfile` - Heroku deployment file  
- ✅ `Dockerfile` - Docker/Cloud Run container
- ✅ `railway.json` - Railway platform configuration
- ✅ `.gitignore` - Git ignore file (excludes venv, cache, etc.)

---

## 💰 **COST COMPARISON**

| Platform | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| **Render** | 750 hours/month | $7/month | Beginners, simple apps |
| **Railway** | $5 credit/month | Usage-based | Modern UI, developers |
| **Heroku** | Limited hours | $7/month | Established platform |
| **Cloud Run** | 2M requests/month | Pay-per-use | High traffic, scalability |
| **GitHub Pages** | Unlimited (static) | Free | Frontend-only hosting |

---

## 🌐 **CUSTOM DOMAIN SETUP**

### **After Deployment:**

1. **Buy domain** (e.g., `housingcompliance.com`)
2. **Add CNAME record:**
   - **Name:** `www` or `@`
   - **Value:** Your platform URL
3. **Configure in platform:**
   - **Render:** Dashboard → Settings → Custom Domain
   - **Railway:** Dashboard → Settings → Domains
   - **Cloud Run:** Cloud Console → Domain Mappings

**Example URLs after custom domain:**
- `https://housingcompliance.com`
- `https://app.housingcompliance.com`

---

## 🔐 **SECURITY CONSIDERATIONS**

### **Environment Variables**
```bash
# Set in platform dashboard:
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-secret-key-here
```

### **HTTPS**
- ✅ **Automatic** on all recommended platforms
- ✅ **Free SSL certificates** included
- ✅ **Force HTTPS** redirect enabled

### **Rate Limiting** (Optional)
```python
# Add to app.py if needed:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
```

---

## 📊 **MONITORING & MAINTENANCE**

### **Built-in Monitoring**
- **Render:** Logs, metrics, uptime monitoring
- **Railway:** Real-time logs, resource usage
- **Cloud Run:** Cloud Monitoring, alerting

### **Health Checks**
- ✅ **Included** in Dockerfile
- ✅ **Automatic** restart on failure
- ✅ **Status page** available

### **Updates**
```bash
# To update deployed app:
git add .
git commit -m "Update: description of changes"
git push origin main

# Platform auto-deploys from GitHub
```

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues:**

**1. Build Fails**
```bash
# Check requirements.txt has all dependencies
pip freeze > requirements.txt
```

**2. App Won't Start**
```bash
# Ensure app.py uses environment PORT
port = int(os.environ.get('PORT', 5001))
app.run(host='0.0.0.0', port=port)
```

**3. Static Files Not Loading**
```python
# Ensure correct static file paths in templates
{{ url_for('static', filename='css/style.css') }}
```

**4. Rules Not Found**
- ✅ **Included:** `rules_extraction_v3_*` directory in repo
- ✅ **Path correct:** Validator points to right directory

---

## 🎯 **RECOMMENDED DEPLOYMENT**

### **For Quick Demo:**
1. **GitHub** + **Render** (5 minutes, free)
2. Share URL: `https://housing-compliance-app.onrender.com`

### **For Production Use:**
1. **GitHub** + **Railway** or **Cloud Run**
2. **Custom domain:** `https://yourdomain.com`
3. **Monitoring** and **backups** enabled

### **For Enterprise:**
1. **Google Cloud Run** or **AWS Lambda**
2. **Load balancer** and **CDN**
3. **Database** for persistent storage
4. **Authentication** and **user management**

---

## ✅ **READY TO DEPLOY**

**Your app includes:**
- ✅ All deployment configuration files
- ✅ Production-ready Flask settings  
- ✅ Proper error handling
- ✅ Static file serving
- ✅ Health check endpoints
- ✅ Environment variable support

**🚀 Pick your platform and deploy in minutes!**

**Recommended first deployment:** GitHub + Render (easiest, free, 5 minutes)
