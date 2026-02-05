# 📋 Quick Deployment Checklist

Use this checklist to track your deployment progress:

## Pre-Deployment
- [ ] Google Gemini API Key obtained
- [ ] GitHub repository is up to date (`git push`)
- [ ] Local environment tested and working

## MongoDB Atlas Setup
- [ ] Account created
- [ ] Free M0 cluster created
- [ ] Database user created with password saved
- [ ] Network access configured (0.0.0.0/0)
- [ ] Connection string copied and password replaced
- [ ] Database name set to `pasupathy_ai`

## Render Backend Deployment
- [ ] Render account created
- [ ] New Web Service created
- [ ] Repository connected (`arvindxyogesh/pasupathy-ai`)
- [ ] Root directory set to `backend`
- [ ] Runtime set to Docker
- [ ] Environment variables configured:
  - [ ] `MONGO_URI`
  - [ ] `GOOGLE_API_KEY`
  - [ ] `SECRET_KEY`
  - [ ] `FLASK_ENV=production`
  - [ ] `PORT=5000`
- [ ] Service deployed successfully
- [ ] Backend URL copied: `https://pasupathy-backend.onrender.com`
- [ ] Health check tested: `/api/health`

## Vercel Frontend Deployment
- [ ] Vercel account created
- [ ] Project imported from GitHub
- [ ] Root directory set to `frontend`
- [ ] Framework preset: Create React App
- [ ] Environment variables configured:
  - [ ] `REACT_APP_API_BASE_URL` (your Render backend URL + /api)
  - [ ] `NODE_ENV=production`
- [ ] Project deployed successfully
- [ ] Frontend URL copied: `https://your-site.vercel.app`

## Post-Deployment Verification
- [ ] Landing page loads correctly
- [ ] System status shows "Ready"
- [ ] Can enter chat interface
- [ ] Test message sent and response received
- [ ] Dataset uploaded (if not done during setup)

## Optional Enhancements
- [ ] Custom domain added (if you have one)
- [ ] UptimeRobot monitoring configured (to prevent backend sleep)
- [ ] Analytics added (Vercel Analytics)

---

## 🔗 Important URLs to Save:

**MongoDB Atlas:**
- Connection String: `_________________________________`

**Render Backend:**
- Dashboard: https://dashboard.render.com
- Backend URL: `_________________________________`
- Health Check: `_________________________________/api/health`

**Vercel Frontend:**
- Dashboard: https://vercel.com/dashboard
- Frontend URL: `_________________________________`

---

## 🎉 Deployment Complete!

Your Pasupathy AI is now live and accessible worldwide! 🌍

Share your website:
- Portfolio: Add to resume/LinkedIn
- GitHub: Update README with live demo link
- Social Media: Show off your AI assistant!
