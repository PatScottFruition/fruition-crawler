# Fruition SEO Crawler - Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd fruition-seo-crawler
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python test_install.py
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## 🎯 Sprint 1 Features Delivered

✅ **Streamlit-based UI** with Fruition branding
- Custom CSS with brand colors (#1B2951, #2065f8, #02b2fe, #fa5c50)
- Fruition logo integration
- Professional, clean interface

✅ **Core Crawling Functionality**
- Async crawling for performance
- Configurable max pages and depth
- Real-time progress tracking
- Respects robots.txt

✅ **SEO Data Extraction**
- Title tags and lengths
- Meta descriptions and lengths
- H1 and H2 headers
- Meta robots directives
- Canonical tags
- Word count
- Status codes
- Indexability status

✅ **Export Capabilities**
- CSV export with all specified columns
- Timestamp-based filenames
- Preview before download

✅ **Basic Issue Detection**
- Missing titles
- Missing meta descriptions
- Error pages (4xx/5xx)

## 📁 Project Structure

```
fruition-seo-crawler/
├── app.py                 # Main Streamlit application
├── modules/
│   ├── __init__.py
│   └── crawler.py        # Core crawling logic
├── assets/
│   └── logo_icon.svg     # Fruition logo
├── .streamlit/
│   └── config.toml       # Streamlit theme config
├── requirements.txt      # Python dependencies
├── README.md            # Full documentation
├── QUICKSTART.md        # This file
└── test_install.py      # Installation tester
```

## 🔄 Next Steps (Sprint 2)

The following features are planned for Sprint 2:
- URL include/exclude patterns
- Ignore noindex option
- Enhanced crawl controls
- Improved robots.txt handling

## 💡 Tips

1. **For larger sites**: Start with a smaller max pages limit to test
2. **Performance**: The crawler uses async requests for speed
3. **Export**: CSV includes all columns specified in requirements
4. **Branding**: All colors match Fruition brand guidelines

## 🐛 Troubleshooting

If you encounter issues:

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check Python version (3.8+ recommended)
3. For Windows users, you may need to install Visual C++ Build Tools for lxml

## 📧 Support

For questions or issues, please refer to the main README.md file.
