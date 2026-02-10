# GitHub Actions CI/CD Workflows

This directory contains the automated CI/CD pipelines for Pasupathy.

## 📋 Workflows

### 1. **CI Pipeline** (`ci.yml`)
Runs on every push and pull request to `main` and `develop` branches.

**Jobs:**
- **Backend Tests**: Python linting (flake8) + pytest + coverage
- **Frontend Tests**: Build + tests (Jest/React Testing Library)
- **Docker Build Test**: Validates Dockerfiles build successfully
- **Security Scan**: Trivy vulnerability scanning

### 2. **CD Pipeline** (`cd.yml`)
Runs on merge to `main` branch.

**Jobs:**
- **Deploy**: Deploys to AWS Elastic Beanstalk
- **Docker Publish**: Builds and pushes images to Docker Hub

### 3. **Docker Build & Test** (`docker-build.yml`)
Integration testing with Docker Compose on PRs.

**Jobs:**
- **Docker Compose Test**: Spins up all services (MongoDB, Backend, Frontend) and runs health checks

---

## 🔐 Required Secrets

Configure these in **GitHub Repository Settings → Secrets and variables → Actions**:

### AWS Deployment
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key

### Google Gemini
- `GOOGLE_API_KEY` - Your Gemini API key

### Docker Hub (Optional)
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub access token

---

## 🚀 Setup Instructions

1. **Go to your GitHub repository**
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with exact names above

### Getting AWS Credentials
```bash
# In AWS Console:
IAM → Users → Create user → "github-actions"
Add policies: AdministratorAccess-AWSElasticBeanstalk
Security credentials → Create access key → CLI
Copy Access Key ID and Secret Access Key
```

### Getting Gemini API Key
```bash
# Visit: https://makersuite.google.com/app/apikey
# Create API key
# Copy to GOOGLE_API_KEY secret
```

---

## 📊 Workflow Triggers

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| CI Pipeline | PR + Push to main/develop | Quality checks before merge |
| CD Pipeline | Merge to main | Automatic deployment |
| Docker Build | PRs | Integration testing |

---

## ✅ Status Badges

Add to your README.md:

```markdown
![CI Pipeline](https://github.com/YOUR_USERNAME/pasupathy-ai/actions/workflows/ci.yml/badge.svg)
![CD Pipeline](https://github.com/YOUR_USERNAME/pasupathy-ai/actions/workflows/cd.yml/badge.svg)
```

---

## 🔧 Manual Deployment

Trigger CD pipeline manually:
1. Go to **Actions** tab
2. Select **CD Pipeline**
3. Click **Run workflow**
4. Choose branch and click **Run**

---

## 📝 Notes

- **First Run**: CI may fail until secrets are configured
- **Docker Hub**: Optional - used for public image distribution
- **Health Checks**: Automated after each deployment
- **Caching**: Docker layer caching enabled for faster builds
