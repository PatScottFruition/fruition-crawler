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

### Common Deployment Issues:

#### 1. **lxml Build Errors on Streamlit Cloud**
**Error**: `Error: Please make sure the libxml2 and libxslt development packages are installed`

**Solution**: ✅ **Fixed!** We've updated the requirements.txt to use:
- `lxml>=4.9.0,<5.0.0` (more compatible version)
- `html.parser` as primary BeautifulSoup parser (built into Python)

#### 2. **Dependency Version Conflicts**
**Error**: Package version conflicts during deployment

**Solution**: ✅ **Fixed!** We use flexible version ranges:
```
streamlit>=1.32.0
aiohttp>=3.9.0
beautifulsoup4>=4.12.0
```

#### 3. **Memory Issues on Free Tier**
**Symptoms**: App crashes or becomes unresponsive

**Solutions**:
- Reduce max pages to 25-30 for large sites
- Use URL filtering to focus on specific sections
- Increase timeout settings in Advanced Options

#### 4. **Slow Performance**
**Solutions**:
- Increase delay between requests (Advanced Options)
- Reduce max depth for broad sites
- Use include patterns to target specific areas

### Runtime Issues:

#### 1. **SSL Certificate Errors**
**Solution**: The crawler automatically handles most SSL issues with relaxed certificate validation

#### 2. **Timeout Errors**
**Solution**: Increase request timeout in Advanced Options (default: 30s)

#### 3. **Rate Limiting**
**Solution**: Increase delay range in Advanced Options or respect robots.txt crawl-delay

### Support:
- **GitHub Issues**: [Report bugs here](https://github.com/PatScottFruition/fruition-crawler/issues)
- **Documentation**: See README.md for full usage guide
- **Deployment Logs**: Check Streamlit Cloud logs for specific error details

### Quick Fixes:
1. **Redeploy**: Sometimes a simple redeploy fixes temporary issues
2. **Clear Cache**: Use "Clear Crawl" button to reset session state
3. **Restart App**: Use "Reboot app" in Streamlit Cloud dashboard
