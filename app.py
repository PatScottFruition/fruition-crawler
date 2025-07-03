import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
import validators
from modules.crawler import SEOCrawler
import base64
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Fruition Site Crawler",
    page_icon="assets/fruition-logo-sm.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Fruition branding
def load_css():
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-dark: #1B2951;
        --primary-blue: #2065f8;
        --secondary-blue: #02b2fe;
        --accent-red: #fa5c50;
        --bg-light: #F8F9FA;
    }
    
    /* Header styling */
    .main-header {
        display: flex;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 2px solid var(--primary-blue);
        margin-bottom: 2rem;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-dark);
        margin: 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(32, 101, 248, 0.3);
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    div[data-testid="metric-container"] label {
        color: var(--primary-dark);
        font-weight: 600;
    }
    
    div[data-testid="metric-container"] div[data-testid="metric-value"] {
        color: var(--primary-blue);
        font-weight: 700;
    }
    
    /* Executive Summary Cards */
    .summary-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid var(--primary-blue);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .health-score {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin: 1rem 0;
    }
    
    .score-excellent { color: #28a745; }
    .score-good { color: #17a2b8; }
    .score-fair { color: #ffc107; }
    .score-poor { color: #dc3545; }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--bg-light);
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: var(--secondary-blue);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    
    .stError {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    .dataframe thead th {
        background-color: var(--primary-dark);
        color: white;
        font-weight: 600;
        text-align: left;
        padding: 0.75rem;
    }
    
    .dataframe tbody tr:hover {
        background-color: #f0f7ff;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-color: #e0e0e0;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-blue);
        box-shadow: 0 0 0 2px rgba(32, 101, 248, 0.1);
    }
    
    /* Enhanced search and filter styling */
    .search-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def load_logo():
    """Load and display the Fruition logo"""
    logo_path = Path("assets/fruition-logo-sm.svg")
    if logo_path.exists():
        with open(logo_path, "r") as f:
            svg_content = f.read()
        # Create a smaller version for the header
        svg_small = svg_content.replace('width="200"', 'width="40"').replace('height="320"', 'height="64"')
        return svg_small
    return None

def init_session_state():
    """Initialize session state variables"""
    if 'crawl_results' not in st.session_state:
        st.session_state.crawl_results = None
    if 'crawl_in_progress' not in st.session_state:
        st.session_state.crawl_in_progress = False
    if 'crawl_progress' not in st.session_state:
        st.session_state.crawl_progress = 0
    if 'current_url' not in st.session_state:
        st.session_state.current_url = ""

def display_header():
    """Display the app header with logo"""
    col1, col2 = st.columns([1, 12])
    
    with col1:
        logo_path = Path("assets/fruition-logo-sm.svg")
        if logo_path.exists():
            try:
                # Use Streamlit's native image handling - much more reliable
                st.image(str(logo_path), width=60)
            except Exception as e:
                # Fallback if image fails to load
                st.markdown("🔍", unsafe_allow_html=True)
        else:
            # Fallback if file doesn't exist
            st.markdown("🔍", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <h1 style="color: #1B2951; font-weight: 700; margin-top: 15px; margin-bottom: 0;">Site Crawler</h1>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 2px solid #2065f8; margin-top: 1rem; margin-bottom: 2rem;'>", unsafe_allow_html=True)

def validate_url(url):
    """Validate the input URL"""
    if not url:
        return False, "Please enter a URL"
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    if not validators.url(url):
        return False, "Please enter a valid URL"
    
    return True, url

def generate_executive_summary(results_df, issues, issue_summary):
    """Generate executive summary with SEO health score"""
    total_pages = len(results_df)
    
    # Calculate SEO Health Score
    score = 100
    
    # Deduct points for issues
    score -= issue_summary['critical'] * 15
    score -= issue_summary['high'] * 8
    score -= issue_summary['medium'] * 3
    score -= issue_summary['low'] * 1
    
    # Ensure score doesn't go below 0
    score = max(0, score)
    
    # Determine health level
    if score >= 90:
        health_level = "Excellent"
        health_class = "score-excellent"
        health_icon = "🟢"
    elif score >= 75:
        health_level = "Good"
        health_class = "score-good"
        health_icon = "🔵"
    elif score >= 50:
        health_level = "Fair"
        health_class = "score-fair"
        health_icon = "🟡"
    else:
        health_level = "Poor"
        health_class = "score-poor"
        health_icon = "🔴"
    
    # Key insights
    insights = []
    
    if issue_summary['critical'] > 0:
        insights.append(f"🚨 {issue_summary['critical']} critical issues require immediate attention")
    
    if issue_summary['high'] > 0:
        insights.append(f"⚠️ {issue_summary['high']} high-priority issues found")
    
    indexable_pages = len(results_df[results_df['Indexability'] == 'Indexable']) if 'Indexability' in results_df.columns else 0
    indexable_percentage = (indexable_pages / total_pages * 100) if total_pages > 0 else 0
    
    if indexable_percentage < 80:
        insights.append(f"📄 Only {indexable_percentage:.1f}% of pages are indexable")
    
    if 'Flesch Reading Ease Score' in results_df.columns:
        avg_readability = results_df['Flesch Reading Ease Score'].mean()
        if avg_readability < 50:
            insights.append(f"📖 Content readability could be improved (avg score: {avg_readability:.1f})")
    
    # Priority actions
    priority_actions = []
    
    if issue_summary['critical'] > 0:
        priority_actions.append("Fix critical server errors and missing title tags")
    
    if issue_summary['high'] > 0:
        priority_actions.append("Address missing H1 tags and meta descriptions")
    
    if len([i for i in issues if i['Type'] == 'Duplicate Title Tag']) > 0:
        priority_actions.append("Create unique titles for duplicate pages")
    
    if not priority_actions:
        priority_actions.append("Continue monitoring and optimizing content quality")
    
    return {
        'score': score,
        'health_level': health_level,
        'health_class': health_class,
        'health_icon': health_icon,
        'insights': insights,
        'priority_actions': priority_actions,
        'total_pages': total_pages,
        'indexable_pages': indexable_pages,
        'indexable_percentage': indexable_percentage
    }

async def run_crawl(url, max_pages, max_depth, include_patterns, exclude_patterns, 
                   ignore_noindex, request_timeout, delay_range, respect_robots, 
                   follow_redirects, use_sitemap, init_progress_bar, init_status_text, 
                   crawl_container):
    """Run the crawler asynchronously with two-phase progress"""
    # Parse patterns
    include_list = [p.strip() for p in include_patterns.split('\n') if p.strip()] if include_patterns else []
    exclude_list = [p.strip() for p in exclude_patterns.split('\n') if p.strip()] if exclude_patterns else []
    
    crawler = SEOCrawler(
        start_url=url,
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=include_list,
        exclude_patterns=exclude_list,
        ignore_noindex=ignore_noindex,
        request_timeout=request_timeout,
        delay_range=delay_range,
        respect_robots=respect_robots,
        follow_redirects=follow_redirects,
        use_sitemap=use_sitemap
    )
    
    def init_progress_callback(progress, status):
        init_progress_bar.progress(progress / 100)
        init_status_text.text(status)
        
        # When initialization is complete, transition to crawl phase
        if progress >= 100:
            # Clear initialization UI and show crawl progress
            init_progress_bar.empty()
            init_status_text.empty()
            
            # Show crawl progress section
            with crawl_container.container():
                st.markdown("### 📄 Crawling Pages")
                crawl_progress_bar = st.progress(0)
                crawl_status_text = st.empty()
                
                # Store references for crawl progress updates
                st.session_state.crawl_progress_bar = crawl_progress_bar
                st.session_state.crawl_status_text = crawl_status_text
    
    def progress_callback(current, total, current_url):
        progress = current / total
        st.session_state.crawl_progress = progress
        st.session_state.current_url = current_url
        
        # Update crawl progress if components exist
        if hasattr(st.session_state, 'crawl_progress_bar') and hasattr(st.session_state, 'crawl_status_text'):
            st.session_state.crawl_progress_bar.progress(progress)
            st.session_state.crawl_status_text.text(f"📄 Crawling page {current}/{total}: {current_url}")
    
    results = await crawler.crawl(progress_callback, init_progress_callback)
    return results, crawler

def main():
    # Initialize
    init_session_state()
    load_css()
    display_header()
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### 🔧 Crawl Configuration")
        
        url_input = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the URL you want to crawl"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            max_pages = st.number_input(
                "Max Pages",
                min_value=1,
                max_value=500,
                value=50,
                help="Maximum number of pages to crawl"
            )
        
        with col2:
            max_depth = st.number_input(
                "Max Depth",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum crawl depth from the start URL"
            )
        
        st.markdown("---")
        
        # Sprint 2: URL Filtering
        st.markdown("### 🎯 URL Filtering")
        
        include_patterns = st.text_area(
            "Include Patterns",
            placeholder="/blog/*\n/products/*\n^https://example.com/important/.*",
            help="URLs to include (one per line). Supports wildcards (*) and regex patterns.",
            height=80
        )
        
        exclude_patterns = st.text_area(
            "Exclude Patterns", 
            placeholder="/admin/*\n*?utm_*\n/wp-admin/*",
            help="URLs to exclude (one per line). Supports wildcards (*) and regex patterns.",
            height=80
        )
        
        st.markdown("---")
        
        # Sprint 2: Advanced Options
        with st.expander("⚙️ Advanced Options"):
            ignore_noindex = st.checkbox(
                "Crawl noindex pages",
                value=False,
                help="Crawl pages with noindex meta tag (they'll still be marked as non-indexable)"
            )
            
            # New sitemap option
            use_sitemap = st.checkbox(
                "Include XML Sitemap URLs",
                value=True,
                help="Discover additional URLs from XML sitemaps to ensure comprehensive coverage"
            )
            
            request_timeout = st.slider(
                "Request Timeout (seconds)",
                min_value=10,
                max_value=120,
                value=30,
                help="How long to wait for each page to load"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                delay_min = st.number_input(
                    "Min Delay (seconds)",
                    min_value=0.1,
                    max_value=5.0,
                    value=0.5,
                    step=0.1,
                    help="Minimum delay between requests"
                )
            with col2:
                delay_max = st.number_input(
                    "Max Delay (seconds)",
                    min_value=0.1,
                    max_value=5.0,
                    value=2.0,
                    step=0.1,
                    help="Maximum delay between requests"
                )
            
            respect_robots = st.checkbox(
                "Respect robots.txt",
                value=True,
                help="Follow robots.txt disallow rules"
            )
            
            follow_redirects = st.checkbox(
                "Follow redirects",
                value=True,
                help="Follow HTTP redirects"
            )
        
        st.markdown("---")
        
        # Crawl button
        crawl_button = st.button(
            "🚀 Start Crawl",
            type="primary",
            disabled=st.session_state.crawl_in_progress,
            use_container_width=True
        )
        
        # Clear crawl button
        if st.session_state.crawl_results:
            if st.button(
                "🗑️ Clear Crawl",
                type="secondary",
                use_container_width=True,
                help="Clear previous crawl results"
            ):
                # Clear all session state
                st.session_state.crawl_results = None
                st.session_state.crawler_stats = None
                st.session_state.crawl_progress = 0
                st.session_state.current_url = ""
                st.success("✅ Crawl results cleared!")
                st.rerun()
    
    # Main content area
    if crawl_button and not st.session_state.crawl_in_progress:
        # Validate URL
        is_valid, processed_url = validate_url(url_input)
        
        if not is_valid:
            st.error(processed_url)
        else:
            st.session_state.crawl_in_progress = True
            st.session_state.crawl_results = None
            
            # Validate delay range
            if delay_min > delay_max:
                st.error("Min delay cannot be greater than max delay")
                st.session_state.crawl_in_progress = False
                return
            
            # Create initialization progress components
            st.markdown("### 🔧 Initializing Crawler")
            init_progress_bar = st.progress(0)
            init_status_text = st.empty()
            
            # Create container for crawl progress (will be populated later)
            crawl_container = st.empty()
            
            try:
                # Run async crawl
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results, crawler = loop.run_until_complete(
                    run_crawl(
                        processed_url, max_pages, max_depth, 
                        include_patterns, exclude_patterns,
                        ignore_noindex, request_timeout, 
                        (delay_min, delay_max), respect_robots, 
                        follow_redirects, use_sitemap,
                        init_progress_bar, init_status_text, crawl_container
                    )
                )
                
                st.session_state.crawl_results = results
                st.session_state.crawler_stats = crawler.get_crawl_stats()
                st.session_state.crawl_in_progress = False
                
                # Clear crawl progress components
                if hasattr(st.session_state, 'crawl_progress_bar'):
                    del st.session_state.crawl_progress_bar
                if hasattr(st.session_state, 'crawl_status_text'):
                    del st.session_state.crawl_status_text
                
                # Enhanced success message with sitemap info
                stats = crawler.get_crawl_stats()
                sitemap_info = ""
                if hasattr(crawler, 'urls_from_sitemap') and crawler.urls_from_sitemap > 0:
                    sitemap_info = f" ({crawler.urls_from_crawling} discovered, {crawler.urls_from_sitemap} from sitemap)"
                
                st.success(f"✅ Crawl completed! Found {stats['total_pages']} pages{sitemap_info}. Skipped {stats['skipped_urls']} URLs.")
                
            except Exception as e:
                st.session_state.crawl_in_progress = False
                st.error(f"❌ Crawl failed: {str(e)}")
    
    # Display results
    if st.session_state.crawl_results:
        st.markdown("---")
        
        # Summary metrics
        results_df = pd.DataFrame(st.session_state.crawl_results)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pages", len(results_df))
        with col2:
            if 'Indexability' in results_df.columns:
                indexable = len(results_df[results_df['Indexability'] == 'Indexable'])
            else:
                indexable = 0
            st.metric("Indexable Pages", indexable)
        with col3:
            if 'Status Code' in results_df.columns:
                errors = len(results_df[results_df['Status Code'].astype(str).str.startswith(('4', '5'))])
            else:
                errors = 0
            st.metric("Errors (4xx/5xx)", errors, delta_color="inverse")
        with col4:
            if 'Load_Time' in results_df.columns:
                avg_load = results_df['Load_Time'].mean()
                if pd.notna(avg_load):
                    st.metric("Avg Load Time", f"{avg_load:.2f}s")
            else:
                st.metric("Avg Load Time", "N/A")
        
        # Get issues for executive summary
        from modules.crawler import SEOCrawler
        temp_crawler = SEOCrawler("temp")
        issues = temp_crawler.detect_issues(st.session_state.crawl_results)
        issue_summary = temp_crawler.get_issue_summary(issues)
        
        # Tabs for different views - Sprint 5: Added Executive Summary
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📋 Executive Summary", "📊 All Pages", "📝 Content Analysis", 
            "⚠️ Issues", "📈 Stats", "💾 Export"
        ])
        
        with tab1:
            st.markdown("### Executive Summary")
            
            # Generate executive summary
            summary = generate_executive_summary(results_df, issues, issue_summary)
            
            # SEO Health Score
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div class="summary-card">
                    <h3 style="text-align: center; margin-bottom: 1rem;">SEO Health Score</h3>
                    <div class="health-score {summary['health_class']}">
                        {summary['health_icon']} {summary['score']}/100
                    </div>
                    <h4 style="text-align: center; color: #6c757d;">{summary['health_level']}</h4>
                </div>
                """, unsafe_allow_html=True)
            
            # Key Metrics Overview
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Pages Crawled", summary['total_pages'])
            with col2:
                st.metric("Indexable Pages", f"{summary['indexable_percentage']:.1f}%")
            with col3:
                st.metric("Total Issues", issue_summary['total_issues'])
            with col4:
                st.metric("Critical Issues", issue_summary['critical'], delta_color="inverse")
            
            st.markdown("---")
            
            # Key Insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔍 Key Insights")
                if summary['insights']:
                    for insight in summary['insights']:
                        st.markdown(f"• {insight}")
                else:
                    st.success("✅ No major issues detected!")
            
            with col2:
                st.markdown("#### 🎯 Priority Actions")
                for i, action in enumerate(summary['priority_actions'], 1):
                    st.markdown(f"{i}. {action}")
            
            st.markdown("---")
            
            # Visual Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Issue Distribution")
                if issue_summary['total_issues'] > 0:
                    issue_data = {
                        'Severity': ['Critical', 'High', 'Medium', 'Low'],
                        'Count': [issue_summary['critical'], issue_summary['high'], 
                                issue_summary['medium'], issue_summary['low']],
                        'Color': ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
                    }
                    fig = px.pie(
                        values=issue_data['Count'], 
                        names=issue_data['Severity'],
                        color_discrete_sequence=issue_data['Color'],
                        title="Issues by Severity"
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No issues found!")
            
            with col2:
                st.markdown("#### Content Quality Overview")
                if 'Flesch Reading Ease Score' in results_df.columns:
                    readability_scores = results_df['Flesch Reading Ease Score'].dropna()
                    if len(readability_scores) > 0:
                        fig = px.histogram(
                            x=readability_scores,
                            nbins=10,
                            title="Readability Score Distribution",
                            labels={'x': 'Flesch Reading Ease Score', 'y': 'Number of Pages'}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No readability data available")
                else:
                    st.info("No readability data available")
        
        with tab2:
            st.markdown("### All Crawled Pages")
            
            # Enhanced search and filtering
            st.markdown('<div class="search-container">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input("🔍 Search URLs", placeholder="Enter search term...")
            
            with col2:
                status_filter = st.selectbox(
                    "Filter by Status",
                    options=["All"] + sorted(results_df['Status Code'].unique().astype(str).tolist())
                )
            
            with col3:
                indexability_filter = st.selectbox(
                    "Filter by Indexability",
                    options=["All"] + sorted(results_df['Indexability'].unique().tolist()) if 'Indexability' in results_df.columns else ["All"]
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Apply filters
            filtered_df = results_df.copy()
            
            if search_term:
                filtered_df = filtered_df[filtered_df['Address'].str.contains(search_term, case=False, na=False)]
            
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['Status Code'].astype(str) == status_filter]
            
            if indexability_filter != "All":
                filtered_df = filtered_df[filtered_df['Indexability'] == indexability_filter]
            
            st.markdown(f"**Showing {len(filtered_df)} of {len(results_df)} pages**")
            
            # Configure columns to display
            display_columns = [
                'Address', 'Status Code', 'Indexability', 'Title tag', 'Title tag Length',
                'Meta Description Length', 'H1-1', 'Word Count', 'Flesch Reading Ease Score',
                'Readability', 'Internal_Links', 'External_Links', 'Total_Images'
            ]
            
            # Filter columns that exist in the dataframe
            available_columns = [col for col in display_columns if col in filtered_df.columns]
            
            # Display the dataframe
            st.dataframe(
                filtered_df[available_columns],
                use_container_width=True,
                height=600
            )
        
        with tab3:
            st.markdown("### Content Analysis")
            
            # Content Quality Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'Flesch Reading Ease Score' in results_df.columns:
                    avg_readability = results_df['Flesch Reading Ease Score'].mean()
                    st.metric("Avg Readability Score", f"{avg_readability:.1f}" if pd.notna(avg_readability) else "N/A")
                else:
                    st.metric("Avg Readability Score", "N/A")
            
            with col2:
                if 'Total_Images' in results_df.columns:
                    total_images = results_df['Total_Images'].sum()
                    st.metric("Total Images", total_images)
                else:
                    st.metric("Total Images", "N/A")
            
            with col3:
                if 'Images_Without_Alt' in results_df.columns:
                    missing_alt = results_df['Images_Without_Alt'].sum()
                    st.metric("Missing Alt Text", missing_alt, delta_color="inverse")
                else:
                    st.metric("Missing Alt Text", "N/A")
            
            with col4:
                if 'Has_Structured_Data' in results_df.columns:
                    structured_data_pages = len(results_df[results_df['Has_Structured_Data'] == True])
                    st.metric("Pages with Schema", structured_data_pages)
                else:
                    st.metric("Pages with Schema", "N/A")
            
            st.markdown("---")
            
            # Content Analysis Table
            content_columns = [
                'Address', 'Word Count', 'Flesch Reading Ease Score', 'Readability',
                'Total_Images', 'Images_With_Alt', 'Images_Without_Alt', 'Internal_Links', 'External_Links'
            ]
            
            # Filter columns that exist in the dataframe
            available_content_columns = [col for col in content_columns if col in results_df.columns]
            
            if available_content_columns:
                st.dataframe(
                    results_df[available_content_columns],
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No content analysis data available")
        
        with tab4:
            st.markdown("### SEO Issues")
            
            if issues:
                # Issue summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Critical", issue_summary['critical'], delta_color="inverse")
                with col2:
                    st.metric("High", issue_summary['high'], delta_color="inverse")
                with col3:
                    st.metric("Medium", issue_summary['medium'], delta_color="inverse")
                with col4:
                    st.metric("Low", issue_summary['low'], delta_color="inverse")
                
                st.markdown("---")
                
                # Filter issues by severity
                severity_filter = st.selectbox(
                    "Filter by Severity",
                    options=["All", "Critical", "High", "Medium", "Low"]
                )
                
                filtered_issues = issues
                if severity_filter != "All":
                    filtered_issues = [i for i in issues if i['Severity'] == severity_filter]
                
                st.markdown(f"**Showing {len(filtered_issues)} of {len(issues)} issues**")
                
                # Display issues
                for issue in filtered_issues:
                    severity_color = {
                        'Critical': '#dc3545',
                        'High': '#fd7e14', 
                        'Medium': '#ffc107',
                        'Low': '#28a745'
                    }.get(issue['Severity'], '#6c757d')
                    
                    with st.expander(f"🔴 {issue['Type']} - {issue['URL'][:50]}..."):
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"**Severity:** <span style='color: {severity_color}'>{issue['Severity']}</span>", unsafe_allow_html=True)
                            st.markdown(f"**Category:** {issue['Category']}")
                        with col2:
                            st.markdown(f"**Description:** {issue['Description']}")
                            st.markdown(f"**Impact:** {issue['Impact']}")
                            st.markdown(f"**Fix:** {issue['Fix']}")
            else:
                st.success("🎉 No SEO issues found! Your site is in great shape.")
        
        with tab5:
            st.markdown("### Crawl Statistics")
            
            if st.session_state.crawler_stats:
                stats = st.session_state.crawler_stats
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Crawl Configuration")
                    st.write(f"**Total Pages:** {stats['total_pages']}")
                    st.write(f"**Skipped URLs:** {stats['skipped_urls']}")
                    st.write(f"**Robots.txt Status:** {stats['robots_txt_status']}")
                    st.write(f"**Crawl Delay:** {stats['crawl_delay_used']}")
                
                with col2:
                    st.markdown("#### Performance Metrics")
                    if 'Load_Time' in results_df.columns:
                        load_times = results_df['Load_Time'].dropna()
                        if len(load_times) > 0:
                            st.write(f"**Avg Load Time:** {load_times.mean():.2f}s")
                            st.write(f"**Min Load Time:** {load_times.min():.2f}s")
                            st.write(f"**Max Load Time:** {load_times.max():.2f}s")
                
                # Load time distribution chart
                if 'Load_Time' in results_df.columns:
                    load_times = results_df['Load_Time'].dropna()
                    if len(load_times) > 0:
                        fig = px.histogram(
                            x=load_times,
                            nbins=20,
                            title="Page Load Time Distribution",
                            labels={'x': 'Load Time (seconds)', 'y': 'Number of Pages'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with tab6:
            st.markdown("### Export Data")
            
            # CSV Export
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"seo_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Issues Export
            if issues:
                issues_df = pd.DataFrame(issues)
                issues_csv = issues_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Issues CSV",
                    data=issues_csv,
                    file_name=f"seo_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            st.markdown("---")
            st.markdown("#### Export Options")
            st.info("💡 **Tip:** Use the CSV export to analyze data in Excel, Google Sheets, or other tools.")

if __name__ == "__main__":
    main()
