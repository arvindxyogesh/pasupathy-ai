# 🚀 AWS Deployment Guide - Pasupathy AI

Deploy your Pasupathy AI backend to **AWS Elastic Beanstalk** with 1GB RAM free tier.

---

## 📋 Prerequisites

- ✅ AWS account (create at [aws.amazon.com](https://aws.amazon.com))
- ✅ MongoDB Atlas connection string
- ✅ Google Gemini API key
- ✅ GitHub repository

---

## 🎁 AWS Free Tier

**New AWS accounts get:**
- **750 hours/month** of t3.micro instances (12 months)
- **1GB RAM** - Better than most free tiers
- **5GB storage**
- **Free data transfer** (15GB/month)

---

## 🗄️ Step 1: MongoDB Atlas (Already Done)

You should already have:
- MongoDB Atlas cluster running
- Connection string saved

If not, refer to [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#-step-1-set-up-mongodb-atlas-database)

---

## ☁️ Step 2: Set Up AWS Account

### 2.1 Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click **"Create an AWS Account"**
3. Enter email, password, AWS account name
4. Choose **"Personal"** account
5. **Add credit/debit card** (required, but won't charge for free tier)
6. Verify phone number
7. Choose **"Basic support - Free"** plan

### 2.2 Access AWS Console

1. Go to [console.aws.amazon.com](https://console.aws.amazon.com)
2. Sign in with your credentials
3. You'll see the AWS Console dashboard

---

## 🚀 Step 3: Deploy with Elastic Beanstalk

### 3.1 Install EB CLI (Command Line Interface)

**On macOS:**
```bash
# Install using pip
pip install awsebcli --upgrade --user

# Verify installation
eb --version
```

**On Windows:**
```bash
pip install awsebcli --upgrade --user
```

### 3.2 Configure AWS Credentials

1. In AWS Console, go to **"IAM"** (Identity and Access Management)
2. Click **"Users"** → **"Create user"**
3. Username: `eb-cli-user`
4. Select **"Attach policies directly"**
5. Add policies:
   - `AdministratorAccess-AWSElasticBeanstalk`
   - `AWSElasticBeanstalkWebTier`
6. Click **"Create user"**
7. Select the user → **"Security credentials"** → **"Create access key"**
8. Choose **"Command Line Interface (CLI)"**
9. **Copy Access Key ID and Secret Access Key**

Configure EB CLI:
```bash
cd /Users/arvindxyogesh/Documents/pasupathy-ai
eb init
```

When prompted:
- **Region**: Choose closest to you (e.g., `us-east-1`)
- **Application name**: `pasupathy-ai`
- **Platform**: `Python 3.11`
- **Use SSH**: `n` (No)
- Enter your **Access Key ID** and **Secret Access Key**

---

## ⚙️ Step 4: Create Environment and Deploy

### 4.1 Create Elastic Beanstalk Environment

```bash
eb create pasupathy-backend \
  --instance-type t3.micro \
  --platform "Python 3.11" \
  --timeout 20
```

This will:
- Create environment named `pasupathy-backend`
- Use t3.micro (1GB RAM, free tier)
- Use Python 3.11
- Wait up to 20 minutes for deployment

### 4.2 Set Environment Variables

```bash
eb setenv \
  MONGO_URI="your-mongodb-connection-string" \
  GOOGLE_API_KEY="your-google-api-key" \
  SECRET_KEY="your-secret-key" \
  FLASK_ENV="production"
```

**Replace with your actual values!**

### 4.3 Deploy

The initial `eb create` will deploy automatically. For future updates:

```bash
git add .
git commit -m "Update backend"
eb deploy
```

---

## ✅ Step 5: Test Your Backend

### 5.1 Get Your URL

```bash
eb open
```

This opens your backend URL in browser. It will look like:
```
http://pasupathy-backend.us-east-1.elasticbeanstalk.com
```

### 5.2 Test Health Endpoint

Visit:
```
http://pasupathy-backend.us-east-1.elasticbeanstalk.com/api/health
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

## 📊 Step 6: Monitor Your Application

### 6.1 View Logs

```bash
eb logs
```

Or in AWS Console:
1. Go to **Elastic Beanstalk** service
2. Click your environment
3. Click **"Logs"** → **"Request Logs"** → **"Last 100 Lines"**

### 6.2 Check Health

```bash
eb health
```

Or in AWS Console:
1. Your Elastic Beanstalk environment
2. Check **"Health"** section

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
REACT_APP_API_BASE_URL=http://pasupathy-backend.us-east-1.elasticbeanstalk.com/api
NODE_ENV=production
```

**Replace with YOUR Elastic Beanstalk URL!**

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
   curl -X POST http://pasupathy-backend.us-east-1.elasticbeanstalk.com/api/dataset/upload \
     -H "Content-Type: application/json" \
     -d @data/arvind_personal_llm_dataset_mongo.json
   ```

---

## 🎯 Benefits of AWS Setup

- ✅ **1GB RAM** - Enough for ML models
- ✅ **750 hours/month free** - Can run 24/7
- ✅ **12 months free** - Full year of hosting
- ✅ **Easy scaling** - Upgrade anytime
- ✅ **Professional infrastructure** - Production-ready

---

## 🔧 Useful EB CLI Commands

```bash
# Deploy updates
eb deploy

# View logs
eb logs

# Check health
eb health

# Open in browser
eb open

# SSH into instance (if enabled)
eb ssh

# Terminate environment (careful!)
eb terminate pasupathy-backend

# List environments
eb list
```

---

## 🐛 Troubleshooting

### Deployment fails:
```bash
eb logs
```
Check for Python errors or missing dependencies

### Memory issues:
Upgrade instance type:
```bash
eb scale 1 --instance-type t3.small
```
(t3.small has 2GB RAM, costs ~$0.02/hour after free tier)

### Environment variables not set:
```bash
eb printenv
```
Verify variables are set correctly

### Health check failing:
1. Check Flask app is running on port 8000
2. Verify `/api/health` endpoint works
3. Check security group allows HTTP traffic

---

## 💰 Cost After Free Tier

If you exceed free tier or after 12 months:

| Resource | Cost |
|----------|------|
| t3.micro (1GB) | ~$0.01/hour (~$7.50/month) |
| t3.small (2GB) | ~$0.02/hour (~$15/month) |
| Storage (5GB) | Free forever |
| Data transfer | First 15GB free/month |

**First year is FREE with new AWS account!**

---

## 🔐 Security Best Practices

1. **Use HTTPS** - Add SSL certificate via AWS Certificate Manager (free)
2. **Rotate credentials** - Update access keys regularly
3. **Set up billing alerts** - Get notified if costs exceed free tier
4. **Use IAM roles** - Don't hardcode AWS credentials

---

## 🎉 You're Live!

- **Backend**: `http://pasupathy-backend.us-east-1.elasticbeanstalk.com`
- **Frontend**: `https://pasupathy-ai-xxxxx.vercel.app`

### Next Steps:

1. **Add custom domain** (optional)
2. **Set up HTTPS** with AWS Certificate Manager
3. **Configure auto-scaling** for high traffic
4. **Set up CloudWatch monitoring**

Enjoy your AI assistant on AWS! 🚀
