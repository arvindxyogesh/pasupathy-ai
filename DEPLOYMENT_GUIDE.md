# 🚀 Deployment Guide - Pasupathy AI

This guide walks you through deploying Pasupathy AI on **free hosting platforms**:
- **Frontend**: Vercel (Free Forever)
- **Backend**: Render (Free tier with sleep)
- **Database**: MongoDB Atlas (Free Forever)

---

## 📋 Prerequisites

1. **GitHub account** - Your code is already on GitHub ✅
2. **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Accounts on:
   - [Vercel](https://vercel.com) (Sign up with GitHub)
   - [Render](https://render.com) (Sign up with GitHub)
   - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) (Free signup)

---

## 🗄️ Step 1: Set Up MongoDB Atlas (Database)

### 1.1 Create MongoDB Atlas Account
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Sign up (free)
3. Create a **Free Shared Cluster** (M0 - 512MB)
4. Choose closest region to you

### 1.2 Configure Database Access
1. In Atlas Dashboard → **Database Access**
2. Click **"Add New Database User"**
3. Authentication Method: **Password**
4. Username: `pasupathy_admin`
5. Password: Click "Autogenerate Secure Password" (copy it!)
6. Database User Privileges: **Read and write to any database**
7. Click **"Add User"**

### 1.3 Configure Network Access
1. Go to **Network Access** in sidebar
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
4. Confirm

### 1.4 Get Connection String
1. Go to **Database** → Click **"Connect"**
2. Choose **"Connect your application"**
3. Copy the connection string:
   ```
   mongodb+srv://pasupathy_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<password>` with the password you copied earlier
5. Add database name: `pasupathy_ai`
   ```
   mongodb+srv://pasupathy_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/pasupathy_ai?retryWrites=true&w=majority
   ```
6. **Save this connection string** - you'll need it for Render!

### 1.5 Import Your Dataset (Optional - can do after deployment)
1. In Atlas → **Database** → Click **"Browse Collections"**
2. Click **"Add My Own Data"**
3. Database name: `pasupathy_ai`
4. Collection name: `dataset`
5. You can manually import or use the `/api/dataset/upload` endpoint after deployment

---

## 🖥️ Step 2: Deploy Backend on Render

### 2.1 Create Render Account
1. Go to [Render](https://render.com)
2. Sign up with GitHub

### 2.2 Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `arvindxyogesh/pasupathy-ai`
3. Configure:
   - **Name**: `pasupathy-backend`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: **Docker**
   - **Instance Type**: **Free**

### 2.3 Set Environment Variables
Click **"Advanced"** → Add environment variables:

| Key | Value |
|-----|-------|
| `MONGO_URI` | Your MongoDB Atlas connection string from Step 1.4 |
| `GOOGLE_API_KEY` | Your Google Gemini API key |
| `SECRET_KEY` | Click "Generate" or use any random string |
| `FLASK_ENV` | `production` |
| `PORT` | `5000` |

### 2.4 Deploy
1. Click **"Create Web Service"**
2. Wait 5-10 minutes for first deployment
3. Once deployed, copy your backend URL:
   ```
   https://pasupathy-backend.onrender.com
   ```
4. **Save this URL** - you'll need it for frontend!

### 2.5 Test Backend
1. Visit: `https://pasupathy-backend.onrender.com/api/health`
2. Should see:
   ```json
   {
     "status": "healthy",
     "db_status": "connected",
     "model_status": "ready"
   }
   ```

---

## 🎨 Step 3: Deploy Frontend on Vercel

### 3.1 Create Vercel Account
1. Go to [Vercel](https://vercel.com)
2. Sign up with GitHub

### 3.2 Import Project
1. Click **"Add New..."** → **"Project"**
2. Import from GitHub: `arvindxyogesh/pasupathy-ai`
3. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### 3.3 Set Environment Variables
Under **"Environment Variables"**, add:

| Name | Value |
|------|-------|
| `REACT_APP_API_BASE_URL` | `https://pasupathy-backend.onrender.com/api` |
| `NODE_ENV` | `production` |

**Replace with YOUR Render backend URL from Step 2.4!**

### 3.4 Deploy
1. Click **"Deploy"**
2. Wait 2-3 minutes
3. Your site will be live at: `https://pasupathy-ai-xxxxx.vercel.app`

### 3.5 Custom Domain (Optional)
1. In Vercel project → **Settings** → **Domains**
2. Add your custom domain (if you have one)

---

## ✅ Step 4: Verify Deployment

### Test Your Live Website:
1. Visit your Vercel URL: `https://your-site.vercel.app`
2. Check system status on landing page
3. Click "Enter Chat" button
4. Send a test message: "Who are you?"
5. Wait for response (first request may take 30s as Render wakes up)

---

## 🎯 Important Notes

### Render Free Tier Limitations:
- **Sleeps after 15 minutes** of inactivity
- First request after sleep takes ~30 seconds to wake up
- 750 hours/month free (more than enough for personal use)

### To Keep Backend Awake (Optional):
Use a service like [UptimeRobot](https://uptimerobot.com) to ping your backend every 14 minutes:
- URL to ping: `https://pasupathy-backend.onrender.com/api/health`
- Interval: Every 14 minutes

---

## 🔄 Updating Your Deployment

### When you make code changes:

**Backend:**
1. Push to GitHub: `git push origin main`
2. Render auto-deploys (5-10 min)

**Frontend:**
1. Push to GitHub: `git push origin main`
2. Vercel auto-deploys (2-3 min)

---

## 📊 Upload Your Dataset

After deployment, visit:
```
https://your-site.vercel.app
```

On the landing page, there should be a way to upload your dataset, or use the API directly:

```bash
curl -X POST https://pasupathy-backend.onrender.com/api/dataset/upload \
  -H "Content-Type: application/json" \
  -d @data/arvind_personal_llm_dataset_mongo.json
```

---

## 🐛 Troubleshooting

### Backend health check fails:
- Check Render logs for errors
- Verify MONGO_URI and GOOGLE_API_KEY are set correctly
- Ensure MongoDB Atlas IP whitelist includes 0.0.0.0/0

### Frontend can't connect to backend:
- Verify `REACT_APP_API_BASE_URL` in Vercel env vars
- Check for CORS errors in browser console
- Redeploy frontend after fixing env vars

### "Model not initialized" error:
- Check if dataset is uploaded to MongoDB
- Verify GOOGLE_API_KEY is valid
- Check Render logs for initialization errors

---

## 💰 Cost Breakdown

| Service | Cost | Limitations |
|---------|------|-------------|
| **Vercel** | ✅ FREE FOREVER | Unlimited bandwidth for personal projects |
| **Render** | ✅ FREE FOREVER | Sleeps after 15 min, 750 hrs/month |
| **MongoDB Atlas** | ✅ FREE FOREVER | 512MB storage (plenty for your data) |
| **Total** | **$0/month** | Perfect for portfolio/personal projects |

---

## 🎉 You're Live!

Share your AI assistant:
- **Frontend**: `https://your-site.vercel.app`
- **Backend API**: `https://pasupathy-backend.onrender.com/api`

Need help? Check:
- Render Dashboard for backend logs
- Vercel Dashboard for frontend logs
- MongoDB Atlas for database monitoring

---

## 📝 Next Steps

1. ✅ Deploy to production
2. 🎨 Add custom domain (optional)
3. 📊 Monitor usage in dashboards
4. 🔄 Set up dataset auto-import
5. 🌐 Share with friends!

Good luck with your deployment! 🚀
