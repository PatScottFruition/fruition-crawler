# Deployment Guide

## 🚀 Deploy to Streamlit Cloud (Recommended)

Streamlit Cloud offers free hosting for public repositories. Here's how to deploy:

### Step 1: Prepare Repository
✅ **Already Done!** Your repository is ready for deployment.

### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app"
   - Select your repository: `PatScottFruition/fruition-crawler`
   - Set main file path: `app.py`
   - Choose a custom URL (optional): `fruition-seo-crawler`

3. **Deploy**
   - Click "Deploy!"
   - Wait 2-3 minutes for deployment

4. **Your App Will Be Live At:**
   - `https://fruition-seo-crawler.streamlit.app` (or your custom URL)

### Step 3: Update README
Once deployed, update the live demo link in README.md:
```markdown
## 🚀 Live Demo
Try the live demo: [Fruition SEO Crawler](https://your-actual-url.streamlit.app)
```

## 🐳 Docker Deployment (Optional)

If you prefer Docker deployment:

1. **Create Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. **Build and Run:**
```bash
docker build -t fruition-crawler .
docker run -p 8501:8501 fruition-crawler
```

## 🔧 Environment Variables

No environment variables are required for basic functionality. The app works out of the box!

## 📊 Performance Notes

- **Recommended**: 1GB RAM minimum for Streamlit Cloud
- **Concurrent Users**: Handles multiple users well
- **Crawl Limits**: Default 50 pages per crawl (configurable)

## 🛠️ Troubleshooting

### Common Issues:
1. **Slow Loading**: Increase timeout settings in Advanced Options
2. **Memory Issues**: Reduce max pages for large sites
3. **SSL Errors**: The crawler handles most SSL issues automatically

### Support:
- GitHub Issues: [Report bugs here](https://github.com/PatScottFruition/fruition-crawler/issues)
- Documentation: See README.md for full usage guide
