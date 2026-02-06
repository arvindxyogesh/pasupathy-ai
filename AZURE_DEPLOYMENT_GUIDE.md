# 🚀 Azure Deployment Guide - Pasupathy AI

Deploy your Pasupathy AI backend to **Azure App Service** using your free credits.

---

## 📋 Prerequisites

- ✅ Azure account with free credits (you have this!)
- ✅ MongoDB Atlas connection string
- ✅ Google Gemini API key
- ✅ GitHub repository

---

## 🗄️ Step 1: MongoDB Atlas (Already Done)

You should already have:
- MongoDB Atlas cluster running
- Connection string saved

If not, refer to [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#-step-1-set-up-mongodb-atlas-database)

---

## ☁️ Step 2: Deploy Backend to Azure App Service

### 2.1 Create App Service

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for **"App Services"** in the top search bar
3. Click **"+ Create"** → **"Web App"**

### 2.2 Configure Web App

**Basics:**
- **Subscription**: Your subscription with credits
- **Resource Group**: Click "Create new" → Name: `pasupathy-rg`
- **Name**: `pasupathy-backend` (must be globally unique)
- **Publish**: `Code`
- **Runtime stack**: `Python 3.11`
- **Operating System**: `Linux`
- **Region**: Choose closest to you (e.g., `East US`)

**App Service Plan:**
- Click **"Create new"**
- **Name**: `pasupathy-plan`
- **Pricing plan**: Click "Explore pricing plans"
  - Select **"Basic B1"** (1.75GB RAM, 1 Core)
  - This will use your free credits (~$13/month value)
- Click **"Apply"**

### 2.3 Review and Create

1. Click **"Review + create"**
2. Review settings
3. Click **"Create"**
4. Wait 2-3 minutes for deployment

---

## 🔧 Step 3: Configure Deployment

### 3.1 Set Up Deployment Source

1. Once created, click **"Go to resource"**
2. In left sidebar, go to **"Deployment"** → **"Deployment Center"**
3. **Source**: Select **"GitHub"**
4. Click **"Authorize"** and sign in to GitHub
5. Select:
   - **Organization**: Your GitHub username
   - **Repository**: `pasupathy-ai`
   - **Branch**: `main`
6. Click **"Save"**

### 3.2 Configure Build Settings

1. In Deployment Center, scroll to **"Build"**
2. **App location**: `/backend`
3. **Output location**: Leave blank
4. Click **"Save"**

---

## ⚙️ Step 4: Configure Application Settings

### 4.1 Add Environment Variables

1. In left sidebar, go to **"Settings"** → **"Configuration"**
2. Under **"Application settings"**, click **"+ New application setting"**

Add these variables one by one:

| Name | Value |
|------|-------|
| `MONGO_URI` | Your MongoDB Atlas connection string |
| `GOOGLE_API_KEY` | Your Google Gemini API key |
| `SECRET_KEY` | Generate random string (e.g., `openssl rand -hex 32`) |
| `FLASK_ENV` | `production` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

3. Click **"Save"** at the top
4. Click **"Continue"** when prompted (app will restart)

### 4.2 Configure Startup Command

1. Still in **"Configuration"** → **"General settings"** tab
2. **Startup Command**: 
   ```
   bash backend/startup.sh
   ```
3. Click **"Save"**

---

## 🚀 Step 5: Deploy

### 5.1 Trigger Deployment

1. Go back to **"Deployment"** → **"Deployment Center"**
2. You should see a build starting automatically
3. Wait 5-10 minutes for first deployment

### 5.2 Monitor Deployment

1. Watch the **"Logs"** tab in Deployment Center
2. Or go to **"Monitoring"** → **"Log stream"** for live logs

### 5.3 Expected Output

You should see:
```
Starting Pasupathy AI Backend...
Installing dependencies...
✅ Configuration loaded successfully
✅ MongoDB connected successfully
🚀 Starting LLM model initialization...
✅ LangChain model initialized
* Running on http://0.0.0.0:8000
```

---

## ✅ Step 6: Test Your Backend

1. Go to **"Overview"** in left sidebar
2. Copy your **"Default domain"**: `https://pasupathy-backend.azurewebsites.net`
3. Test health endpoint:
   ```
   https://pasupathy-backend.azurewebsites.net/api/health
   ```

Expected response:
```json
{
  "status": "healthy",
  "db_status": "connected",
  "model_status": "ready"
}
```

---

## 🎨 Step 7: Deploy Frontend to Vercel

### 7.1 Create Vercel Account

1. Go to [Vercel](https://vercel.com)
2. Sign up with GitHub

### 7.2 Import Project

1. Click **"Add New..."** → **"Project"**
2. Import: `arvindxyogesh/pasupathy-ai`
3. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`

### 7.3 Environment Variables

Add:
```
REACT_APP_API_BASE_URL=https://pasupathy-backend.azurewebsites.net/api
NODE_ENV=production
```

**Replace `pasupathy-backend` with YOUR Azure app name!**

### 7.4 Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes
3. Your site: `https://pasupathy-ai-xxxxx.vercel.app`

---

## 📊 Step 8: Upload Dataset

Once both are deployed:

1. Visit your Vercel frontend URL
2. Use the dataset upload feature on landing page
3. Or use API:
   ```bash
   curl -X POST https://pasupathy-backend.azurewebsites.net/api/dataset/upload \
     -H "Content-Type: application/json" \
     -d @data/arvind_personal_llm_dataset_mongo.json
   ```

---

## 🎯 Benefits of This Setup

- ✅ **1.75GB RAM** - Plenty for ML models
- ✅ **Always on** - No sleep after inactivity
- ✅ **Fast performance** - Better CPU than free tiers
- ✅ **Free for 6 months** - Using your Azure credits
- ✅ **Easy scaling** - Can upgrade later if needed

---

## 🐛 Troubleshooting

### Backend won't start:
- Check **Log stream** for errors
- Verify environment variables are set
- Check MongoDB connection string format

### "Application Error":
- Check **Deployment Center** → **Logs**
- Verify `startup.sh` has correct path
- Check Python version matches (3.11)

### Memory issues:
- B1 tier has 1.75GB, should be enough
- If issues persist, upgrade to B2 (3.5GB)

---

## 💰 Cost Monitoring

Monitor your credit usage:
1. Go to **"Cost Management + Billing"**
2. Check **"Cost analysis"**
3. You have plenty of credits for 6 months

Expected usage: ~$13/month for B1 tier

---

## 🎉 You're Live!

- **Backend**: `https://pasupathy-backend.azurewebsites.net`
- **Frontend**: `https://pasupathy-ai-xxxxx.vercel.app`

Enjoy your AI assistant! 🚀
