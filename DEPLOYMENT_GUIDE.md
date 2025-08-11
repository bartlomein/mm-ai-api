# Deployment Guide - Market Brief AI

## Quick Start Deployment to Render

### Prerequisites
- GitHub account with this code pushed to a repository
- Render.com account (free tier works)
- API keys ready (Fish Audio, Gemini, Finlight)

### Step 1: Push to GitHub
```bash
# If not already initialized
git init
git add .
git commit -m "Ready for Render deployment with 5-minute briefings"
git remote add origin https://github.com/YOUR_USERNAME/mm-ai-be.git
git push -u origin main
```

### Step 2: Deploy on Render

1. **Sign in to Render.com**
   - Go to https://render.com
   - Sign in with GitHub

2. **Create New Blueprint**
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing this code
   - Render will auto-detect the `render.yaml` file

3. **Configure Environment Variables**
   - Render will prompt for environment variables
   - Add these values:
     ```
     FISH_API_KEY=your_fish_api_key_here
     GEMINI_API_KEY=your_gemini_api_key_here
     FINLIGHT_API_KEY=your_finlight_api_key_here
     OPENAI_API_KEY=your_openai_key_here (optional)
     ```
   - FISH_MODEL_ID is already set in render.yaml

4. **Deploy**
   - Click "Apply" to start deployment
   - Wait ~5-10 minutes for initial build

### Step 3: Verify Deployment

1. **Check API Health**
   ```bash
   curl https://market-brief-api.onrender.com/api/health
   ```

2. **Test Briefing Generation**
   ```bash
   curl -X POST https://market-brief-api.onrender.com/api/test/generate
   ```

3. **View API Documentation**
   - Visit: https://market-brief-api.onrender.com/docs

### Step 4: Monitor Cron Jobs

1. **View Cron Job Logs**
   - Go to Render Dashboard
   - Click on "morning-briefing" or "evening-briefing"
   - View Logs tab

2. **Manual Trigger (for testing)**
   - In Render Dashboard
   - Select the cron job
   - Click "Trigger Run"

## Deployment Options Comparison

### Render.com (RECOMMENDED) ✅
**Pros:**
- Free tier includes cron jobs
- Auto-deploy from GitHub
- Blueprint support (render.yaml)
- Built-in health checks
- Easy environment variables

**Cons:**
- Spins down after 15 min inactivity (free tier)
- Cold starts can be slow

### Alternative: Railway.app
**Pros:**
- Better performance
- No cold starts
- Great developer experience

**Cons:**
- Cron jobs require paid plan
- More expensive overall

### Alternative: Heroku
**Pros:**
- Mature platform
- Lots of add-ons

**Cons:**
- No free tier
- Expensive for cron jobs

## Production Checklist

### Before Going Live
- [ ] Test Fish Audio voice consistency
- [ ] Verify 5-minute briefing length
- [ ] Check pronunciation formatting
- [ ] Test deduplication logic
- [ ] Verify cron schedule (UTC times!)

### Security
- [ ] Never commit .env file
- [ ] Use Render's environment variables
- [ ] Keep API keys secret
- [ ] Enable HTTPS only (automatic on Render)

### Monitoring
- [ ] Set up error alerts
- [ ] Monitor API response times
- [ ] Check daily briefing generation
- [ ] Track Fish Audio usage/costs

## Troubleshooting

### Issue: API not responding
**Solution:** Check Render logs, might be spinning up from cold start

### Issue: Briefing not generating at scheduled time
**Solution:** Verify timezone - Render uses UTC (6 AM EST = 11 AM UTC)

### Issue: Fish Audio timeout
**Solution:** Normal for 800+ word texts, takes 3-4 minutes

### Issue: Voice changes between generations
**Solution:** Ensure FISH_MODEL_ID is set correctly in environment

## Next Steps After Deployment

1. **Set up monitoring**
   - Use Render's built-in metrics
   - Set up Uptime Robot for health checks

2. **Add custom domain**
   - In Render settings, add custom domain
   - Update DNS records

3. **Scale if needed**
   - Upgrade Render plan for better performance
   - Add more worker instances

4. **Future features**
   - User authentication (Supabase)
   - Email delivery of briefings
   - Mobile app
   - Personalized tickers

## Support

- Render Documentation: https://render.com/docs
- Fish Audio Docs: https://docs.fish.audio
- Project Issues: Create issue in GitHub repo

---

**Remember:** The free tier works great for testing and personal use. Upgrade when you need better performance or more features.