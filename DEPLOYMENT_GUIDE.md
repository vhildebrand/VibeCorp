# 🚀 VibeCorp Deployment Guide

This guide will help you deploy the VibeCorp Autonomous AI Startup Simulation to production using free-tier services.

## 📋 Prerequisites

- GitHub account
- OpenAI API key
- Basic knowledge of environment variables

## 🗄️ Database Setup (Free PostgreSQL)

We recommend **Neon** for free PostgreSQL hosting:

### Option 1: Neon (Recommended)
1. Go to [neon.tech](https://neon.tech)
2. Sign up with GitHub
3. Create a new project: "vibecorp-production"
4. Copy the connection string (format: `postgresql://username:password@host/database`)
5. Save this as your `DATABASE_URL`

### Option 2: Supabase
1. Go to [supabase.com](https://supabase.com)
2. Create new project: "vibecorp"
3. Go to Settings → Database
4. Copy the connection string under "Connection string"
5. Replace `[YOUR-PASSWORD]` with your actual password

### Option 3: Railway
1. Go to [railway.app](https://railway.app)
2. Create new project
3. Add PostgreSQL service
4. Copy the connection string from the service

## 🖥️ Backend Deployment (Railway)

### 1. Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your VibeCorp repository
4. Railway will automatically detect the Dockerfile

### 2. Set Environment Variables
In Railway dashboard, go to your service → Variables tab:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://username:password@host:5432/database
PORT=8000
HOST=0.0.0.0
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
ENVIRONMENT=production
```

### 3. Deploy
- Railway will automatically deploy after setting variables
- Note your backend URL (e.g., `https://vibecorp-backend-production.up.railway.app`)

## 🌐 Frontend Deployment (Vercel)

### 1. Deploy to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Set root directory to `startup-simulator-ui`
4. Vercel will auto-detect it's a Vite project

### 2. Set Environment Variables
In Vercel dashboard → Settings → Environment Variables:

```env
VITE_API_URL=https://your-backend-domain.up.railway.app
VITE_WS_URL=wss://your-backend-domain.up.railway.app/ws
```

### 3. Deploy
- Vercel will automatically deploy
- Get your frontend URL (e.g., `https://vibecorp.vercel.app`)

### 4. Update Backend CORS
Update your Railway backend's `ALLOWED_ORIGINS` variable:
```env
ALLOWED_ORIGINS=https://vibecorp.vercel.app
```

## 🔧 Alternative Deployment Options

### Backend Alternatives
- **Render**: Similar to Railway, supports Docker
- **Google Cloud Run**: Free tier available
- **AWS App Runner**: Pay-per-use

### Database Alternatives
- **PlanetScale**: MySQL alternative
- **MongoDB Atlas**: NoSQL option (requires code changes)
- **CockroachDB**: Distributed SQL

### Frontend Alternatives  
- **Netlify**: Similar to Vercel
- **GitHub Pages**: Free static hosting
- **Surge.sh**: Simple deployment

## 🧪 Testing Your Deployment

### 1. Backend Health Check
Visit: `https://your-backend-domain.up.railway.app/health`
Should return: `{"status":"healthy","service":"AutoGen Startup Simulation API"}`

### 2. Frontend Test
1. Visit your Vercel URL
2. Check if the UI loads properly
3. Verify agents are displayed in the sidebar
4. Check for autonomous messages appearing

### 3. Database Connection
Check Railway logs to ensure:
- Database connection is successful
- Tables are created automatically
- No connection errors

## 🔒 Security Considerations

### Production Checklist
- [ ] OpenAI API key is properly secured
- [ ] Database credentials are not exposed
- [ ] CORS is configured for your domain only
- [ ] HTTPS is enabled (automatic with Vercel/Railway)
- [ ] Environment variables are set correctly

### Environment Variables
Never commit these to Git:
- `OPENAI_API_KEY`
- `DATABASE_URL` 
- Any passwords or secrets

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Railway logs for errors
- Verify all environment variables are set
- Ensure OpenAI API key is valid

**Frontend can't connect to backend:**
- Verify `VITE_API_URL` points to correct backend
- Check CORS configuration
- Ensure backend is running (health check)

**Database connection failed:**
- Verify `DATABASE_URL` format
- Check database service is running
- Ensure IP whitelist allows connections

**WebSocket connection failed:**
- Verify `VITE_WS_URL` uses `wss://` (not `ws://`)
- Check if Railway supports WebSockets (it does)
- Ensure WebSocket endpoint `/ws` is accessible

### Logs and Debugging
- **Railway**: View logs in dashboard
- **Vercel**: Check function logs
- **Browser**: Use DevTools Network tab for API calls

## 📊 Monitoring

### Health Checks
- Backend: `GET /health`
- Database: Check connection in logs
- Frontend: Verify loading and API calls

### Performance
- Railway provides metrics dashboard
- Vercel shows deployment and function metrics
- Monitor OpenAI API usage in OpenAI dashboard

## 💰 Cost Estimation

### Free Tier Limits (as of 2024)
- **Neon**: 500MB storage, 1 database
- **Railway**: $5/month credit (covers small apps)
- **Vercel**: 100GB bandwidth, unlimited deployments
- **OpenAI**: Pay-per-use (estimate $5-20/month for moderate usage)

### Total Monthly Cost: ~$10-25 for moderate usage

## 🚀 Going Live Checklist

- [ ] Database created and accessible
- [ ] Backend deployed to Railway with all env vars
- [ ] Frontend deployed to Vercel with correct API URLs  
- [ ] CORS configured properly
- [ ] Health checks pass
- [ ] WebSocket connection working
- [ ] Agents are generating autonomous messages
- [ ] No console errors in browser

## 🔄 Updates and Maintenance

### Updating the Application
1. Push changes to your GitHub repository
2. Railway and Vercel will auto-deploy from main branch
3. Check health endpoints after deployment

### Database Migrations
- The app automatically creates/updates tables on startup
- For major schema changes, consider manual migration scripts

### Monitoring Autonomous Agents
- Check logs for agent conversation errors
- Monitor OpenAI API usage and costs
- Verify WebSocket connections are stable

---

🎉 **Congratulations!** Your VibeCorp AI startup simulation is now running autonomously in the cloud!

The agents will continuously generate tasks, have conversations, and simulate a realistic startup environment 24/7.

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review service logs (Railway/Vercel dashboards)
3. Verify all environment variables are correctly set
4. Test API endpoints manually using curl or Postman 