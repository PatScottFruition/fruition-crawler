# Fruition SEO Crawler

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32.0-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional technical SEO crawler built with Streamlit and Python, featuring comprehensive SEO analysis, content metrics, and issue detection with the Fruition brand design.

## 🚀 Live Demo

Try the live demo: [Fruition SEO Crawler](https://your-app-name.streamlit.app) *(Deploy to get this link)*

## 📸 Screenshots

![Executive Summary](https://via.placeholder.com/800x400?text=Executive+Summary+Screenshot)
*Executive Summary with SEO Health Score*

![All Pages View](https://via.placeholder.com/800x400?text=All+Pages+View+Screenshot)
*Comprehensive page analysis with filtering*

## Features

### Sprint 1 - Foundation ✅
- Web-based UI with Fruition branding
- Basic crawling functionality
- Extract essential SEO elements:
  - Title tags and lengths
  - Meta descriptions and lengths
  - H1 and H2 headers
  - Meta robots directives
  - Canonical tags
  - Word count
  - Status codes
- Real-time crawl progress
- CSV export with all required columns
- Basic issue detection

### Enhanced Crawler Features (Implemented) ✅
- **Browser-like Headers**: Full set of headers to appear like a real browser
- **Session Management**: Maintains cookies and session state
- **Smart Delays**: Random delays (0.5-2s) or respects robots.txt crawl-delay
- **Robots.txt Parser**: Actually parses and respects disallow rules
- **Retry Logic**: Up to 3 retries with exponential backoff
- **Better Error Handling**: Detailed error messages for debugging
- **SSL/TLS Handling**: Gracefully handles certificate issues
- **Referrer Tracking**: Includes referrer headers for natural browsing

### Sprint 2 - Advanced Crawling Features ✅
- **URL Filtering**: Include/exclude patterns with wildcards and regex support
- **Ignore Noindex Option**: Crawl noindex pages anyway (marked as non-indexable)
- **Advanced Crawl Controls**: Configurable timeouts, delays, and options
- **Enhanced Robots.txt**: Better parsing and optional override
- **Crawl Statistics**: Detailed stats showing what was crawled and skipped
- **Pattern Examples**: Built-in help for URL filtering patterns

### Sprint 3 - SEO Analysis & Content Metrics ✅
- **Flesch Reading Ease Scoring**: Actual readability calculations with textstat library
- **Enhanced Content Analysis**: Word count, paragraph count, sentence analysis
- **Complete Link Analysis**: Internal vs external link tracking and counting
- **Structured Data Detection**: JSON-LD and microdata parsing with schema type extraction
- **Enhanced Header Analysis**: All H1-H6 tags with hierarchy validation
- **Image SEO Analysis**: Alt text coverage, missing alt detection
- **Content Quality Tab**: Dedicated interface for content analysis metrics
- **Schema Visualization**: Bar charts showing structured data distribution

### Sprint 4 - Technical Checks & Issue Detection ✅
- **Advanced Issue Detection**: Missing/duplicate titles, meta descriptions, H1 tags
- **Technical SEO Checks**: Server errors, heading hierarchy, canonical issues
- **Content Quality Issues**: Thin content, readability problems, image alt text
- **Severity Scoring System**: Critical, High, Medium, Low priority classification
- **Issue Dashboard**: Visual metrics and category breakdown with filtering
- **Automated Recommendations**: Specific fix instructions for each issue type
- **Duplicate Detection**: Cross-page analysis for duplicate titles and descriptions
- **Enhanced Issues Tab**: Professional issue management interface with detailed analysis

### Sprint 5 - Reporting & Polish ✅
- **Executive Summary Generator**: SEO health score with intelligent insights and priority actions
- **Visual Charts and Graphs**: Interactive Plotly charts for issue distribution and content quality
- **Enhanced UI/UX**: Advanced search, filtering, and data visualization capabilities
- **Professional Dashboard**: Executive-level reporting with key metrics and recommendations
- **SEO Health Scoring**: Intelligent scoring system based on issue severity and impact
- **Interactive Visualizations**: Pie charts, histograms, and bar charts for data analysis
- **Enhanced Search & Filtering**: Real-time search and multi-criteria filtering across all data
- **Polished User Experience**: Professional styling, responsive design, and intuitive navigation

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Local Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/PatScottFruition/fruition-crawler.git
cd fruition-crawler
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### 🚀 Deploy to Streamlit Cloud

1. Fork this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository
5. Set the main file path to `app.py`
6. Click "Deploy"

Your app will be live at `https://your-app-name.streamlit.app`

## 📖 Usage

### Basic Crawling
1. **Enter the website URL** in the sidebar
2. **Configure crawl settings:**
   - **Max Pages**: Maximum number of pages to crawl (default: 50)
   - **Max Depth**: How deep to crawl from the start URL (default: 3)
   - **Include XML Sitemap URLs**: Discover additional URLs from sitemaps
3. **Click "Start Crawl"** to begin
4. **View results** in the comprehensive tabs:
   - **📋 Executive Summary**: SEO health score and key insights
   - **📊 All Pages**: Complete list with advanced filtering
   - **📝 Content Analysis**: Readability, links, and structured data
   - **⚠️ Issues**: Detailed SEO problems with fix recommendations
   - **📈 Stats**: Crawl statistics and settings
   - **💾 Export**: Download complete CSV report

### Advanced Features
- **URL Filtering**: Use include/exclude patterns with wildcards and regex
- **Advanced Options**: Configure timeouts, delays, robots.txt handling
- **Real-time Progress**: Monitor crawl progress with current URL display
- **Clear Crawl**: Reset results and start fresh with the clear button

### Export Options
Download comprehensive CSV reports with all SEO metrics for further analysis in Excel, Google Sheets, or other tools.

## CSV Export Format

The exported CSV includes all requested columns:
- Address
- Content Type
- Status Code
- Indexability
- Title tag & Length
- Meta Description & Length
- H1-1 & Length
- H2-1, H2-2 & Lengths
- Meta Robots 1
- Canonical Link Element 1
- Word Count
- Flesch Reading Ease Score (Sprint 3)
- Readability (Sprint 3)
- Crawl Depth
- Inlinks & Unique Inlinks (Enhanced in Sprint 3)

## Upcoming Features

### Sprint 2: Advanced Crawling
- URL include/exclude patterns
- Ignore noindex option
- Enhanced crawl controls

### Sprint 3: SEO Analysis
- Flesch Reading Ease scoring
- Readability assessment
- Complete link analysis
- Structured data validation

### Sprint 4: Issue Detection
- Comprehensive issue identification
- Severity scoring
- Prioritized recommendations

### Sprint 5: Reporting & Polish
- Executive summary
- Visual charts and graphs
- Enhanced UI/UX
- Performance optimizations

## 🏗️ Technical Stack

- **Frontend**: Streamlit
- **Crawling**: aiohttp (async)
- **HTML Parsing**: BeautifulSoup4
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **Readability Analysis**: textstat
- **URL Validation**: validators
- **Styling**: Custom CSS with Fruition brand colors

## 🎨 Brand Colors

- **Primary Dark**: #1B2951
- **Primary Blue**: #2065f8
- **Secondary Blue**: #02b2fe
- **Accent Red**: #fa5c50

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Include comments for complex logic

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 About Fruition

This crawler was developed by [Fruition](https://fruition.net), a digital marketing agency specializing in SEO and web development.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/PatScottFruition/fruition-crawler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PatScottFruition/fruition-crawler/discussions)
- **Website**: [fruition.net](https://fruition.net)

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [aiohttp](https://aiohttp.readthedocs.io/) for async crawling
- SEO analysis inspired by industry best practices
- UI design following Fruition brand guidelines

---

**Made with ❤️ by the Fruition team**
