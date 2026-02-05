# Profile Image Setup

## How to Add Your Profile Picture

Your landing page now includes a profile section with your photo and introduction!

### Steps to Add Your Profile Image:

1. **Prepare your image:**
   - Use a square image (recommended: 400x400px or larger)
   - Supported formats: JPG, PNG, WebP
   - File size: Keep under 500KB for fast loading

2. **Add to the project:**
   - Place your profile image in: `frontend/public/profile.jpg`
   - Or name it `profile.png` and update the code accordingly

3. **Option A: Copy to public folder (Local Development)**
   ```bash
   cp /path/to/your/photo.jpg frontend/public/profile.jpg
   ```

4. **Option B: Copy to Docker container (Running in Docker)**
   ```bash
   docker cp /path/to/your/photo.jpg llm_frontend:/app/public/profile.jpg
   docker restart llm_frontend
   ```

### Current Setup:

The landing page currently shows:
- **Profile Image**: Either your `profile.jpg` or a generated avatar with your initials
- **Name**: "Arvind"
- **Tagline**: "Computer Vision Engineer | AI Enthusiast | Problem Solver"
- **Description**: A brief introduction about your expertise

### To Customize the Text:

Edit `frontend/src/components/Landing.js`:

```javascript
<h2 className="profile-name">Your Name</h2>
<p className="profile-tagline">Your Professional Title</p>
<p className="profile-description">
  Your introduction text here...
</p>
```

### Accessing the Landing Page:

Open http://localhost:3000 to see your profile!

---

**Note**: If no `profile.jpg` is found, the system automatically falls back to a stylish generated avatar with your initials.
