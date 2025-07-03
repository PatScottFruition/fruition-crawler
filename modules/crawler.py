import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, urlunparse, quote
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import time
import random
import ssl
from typing import Dict, Set, List, Optional, Tuple
import re
from io import StringIO
import textstat
import json
import xml.etree.ElementTree as ET
import gzip

class SEOCrawler:
    def __init__(self, start_url: str, max_pages: int = 50, max_depth: int = 3, 
                 include_patterns: List[str] = None, exclude_patterns: List[str] = None,
                 ignore_noindex: bool = False, request_timeout: int = 30,
                 delay_range: Tuple[float, float] = (0.5, 2.0), respect_robots: bool = True,
                 follow_redirects: bool = True, use_sitemap: bool = True):
        self.start_url = self._normalize_url(start_url)
        self.domain = urlparse(self.start_url).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.to_visit: List[tuple[str, int]] = [(self.start_url, 0)]
        self.results: List[Dict] = []
        self.robots_parser = None
        self.robots_crawl_delay = 0
        self.session = None
        
        # Sprint 2 features
        self.include_patterns = self._compile_patterns(include_patterns or [])
        self.exclude_patterns = self._compile_patterns(exclude_patterns or [])
        self.ignore_noindex = ignore_noindex
        self.request_timeout = request_timeout
        self.delay_range = delay_range
        self.respect_robots = respect_robots
        self.follow_redirects = follow_redirects
        self.use_sitemap = use_sitemap
        self.robots_txt_status = "Not fetched"
        self.skipped_urls = []
        self.sitemap_urls = []
        self.sitemap_status = "Not fetched"
        self.urls_from_sitemap = 0
        self.urls_from_crawling = 0
        
        # Browser-like headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure consistency"""
        parsed = urlparse(url)
        # Remove fragment
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                               parsed.params, parsed.query, ''))
        # Remove trailing slash for consistency
        if normalized.endswith('/') and normalized != f"{parsed.scheme}://{parsed.netloc}/":
            normalized = normalized[:-1]
        return normalized
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain"""
        url_domain = urlparse(url).netloc
        # Handle www vs non-www
        url_domain_clean = url_domain.replace('www.', '')
        self_domain_clean = self.domain.replace('www.', '')
        return url_domain_clean == self_domain_clean
    
    def _should_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled based on robots.txt and other rules"""
        # Skip common non-HTML resources
        skip_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', 
                          '.exe', '.dmg', '.mp3', '.mp4', '.avi', '.mov',
                          '.css', '.js', '.ico', '.xml', '.txt', '.doc',
                          '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
        
        parsed_url = urlparse(url)
        path_lower = parsed_url.path.lower()
        
        if any(path_lower.endswith(ext) for ext in skip_extensions):
            return False
        
        # Check robots.txt
        if self.robots_parser:
            try:
                if not self.robots_parser.can_fetch("*", url):
                    return False
            except:
                pass  # If robots.txt parsing fails, continue
                
        return True
    
    async def fetch_and_parse_robots_txt(self, init_progress_callback=None):
        """Fetch and parse robots.txt"""
        robots_url = f"{urlparse(self.start_url).scheme}://{self.domain}/robots.txt"
        
        if init_progress_callback:
            init_progress_callback(20, "📋 Fetching robots.txt...")
        
        try:
            async with self.session.get(
                robots_url, 
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=10),
                ssl=self._get_ssl_context()
            ) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    
                    # Parse robots.txt
                    self.robots_parser = RobotFileParser()
                    self.robots_parser.parse(StringIO(robots_content).readlines())
                    
                    # Extract crawl delay if specified
                    for line in robots_content.split('\n'):
                        if line.lower().startswith('crawl-delay:'):
                            try:
                                self.robots_crawl_delay = float(line.split(':')[1].strip())
                            except:
                                pass
                    
                    if init_progress_callback:
                        init_progress_callback(40, "✅ Robots.txt fetched successfully")
                    
                    # Extract sitemap URLs from robots.txt
                    if self.use_sitemap:
                        await self._extract_sitemaps_from_robots(robots_content, init_progress_callback)
                else:
                    if init_progress_callback:
                        init_progress_callback(40, "⚠️ No robots.txt found, continuing...")
        except Exception as e:
            if init_progress_callback:
                init_progress_callback(40, f"⚠️ Could not fetch robots.txt: {str(e)}")
            print(f"Could not fetch robots.txt: {e}")
    
    async def _extract_sitemaps_from_robots(self, robots_content: str, init_progress_callback=None):
        """Extract sitemap URLs from robots.txt"""
        sitemap_urls = []
        for line in robots_content.split('\n'):
            if line.lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                sitemap_urls.append(sitemap_url)
        
        # Also try common sitemap locations
        base_url = f"{urlparse(self.start_url).scheme}://{self.domain}"
        common_sitemaps = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemaps.xml"
        ]
        
        # Combine and deduplicate
        all_sitemaps = list(set(sitemap_urls + common_sitemaps))
        
        if init_progress_callback:
            if sitemap_urls:
                init_progress_callback(50, f"🗺️ Found {len(sitemap_urls)} sitemaps in robots.txt")
            else:
                init_progress_callback(50, "🗺️ Checking common sitemap locations...")
        
        # Fetch and parse each sitemap
        for i, sitemap_url in enumerate(all_sitemaps):
            if init_progress_callback:
                progress = 50 + (40 * (i + 1) / len(all_sitemaps))  # 50-90% range
                sitemap_name = sitemap_url.split('/')[-1]
                init_progress_callback(int(progress), f"🗺️ Processing sitemap {i+1}/{len(all_sitemaps)}: {sitemap_name}")
            
            await self._fetch_and_parse_sitemap(sitemap_url)
        
        if init_progress_callback:
            if self.sitemap_urls:
                init_progress_callback(90, f"✅ Discovered {len(self.sitemap_urls)} URLs from sitemaps")
            else:
                init_progress_callback(90, "⚠️ No sitemap URLs found")
    
    async def _fetch_and_parse_sitemap(self, sitemap_url: str):
        """Fetch and parse a single sitemap"""
        try:
            async with self.session.get(
                sitemap_url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15),
                ssl=self._get_ssl_context()
            ) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    # Handle compressed sitemaps
                    if 'gzip' in content_type or sitemap_url.endswith('.gz'):
                        content = await response.read()
                        try:
                            content = gzip.decompress(content).decode('utf-8')
                        except:
                            content = content.decode('utf-8', errors='ignore')
                    else:
                        content = await response.text()
                    
                    # Parse XML
                    urls, nested_sitemaps = self._parse_sitemap_xml(content)
                    self.sitemap_urls.extend(urls)
                    
                    # Process nested sitemaps if this was a sitemap index
                    if nested_sitemaps:
                        print(f"Processing {len(nested_sitemaps)} nested sitemaps from sitemap index")
                        for nested_sitemap_url in nested_sitemaps:
                            await self._fetch_and_parse_sitemap(nested_sitemap_url)
                    
                    if urls or nested_sitemaps:
                        self.sitemap_status = f"Found {len(self.sitemap_urls)} URLs from sitemaps"
                    else:
                        self.sitemap_status = "Sitemap found but no URLs extracted"
                else:
                    self.sitemap_status = f"Sitemap not found (HTTP {response.status})"
        except Exception as e:
            self.sitemap_status = f"Error fetching sitemap: {str(e)}"
    
    def _parse_sitemap_xml(self, xml_content: str) -> Tuple[List[str], List[str]]:
        """Parse XML sitemap content and extract URLs or nested sitemap URLs"""
        urls = []
        nested_sitemaps = []
        try:
            # Remove namespace declarations to simplify parsing
            xml_content = re.sub(r'xmlns[^=]*="[^"]*"', '', xml_content)
            
            root = ET.fromstring(xml_content)
            
            # Check if this is a sitemap index
            if root.tag.endswith('sitemapindex'):
                # This is a sitemap index, extract sitemap URLs for later processing
                for sitemap in root.findall('.//sitemap'):
                    loc = sitemap.find('loc')
                    if loc is not None and loc.text:
                        nested_sitemap_url = loc.text.strip()
                        # Only include sitemaps from the same domain
                        if self._is_same_domain(nested_sitemap_url):
                            nested_sitemaps.append(nested_sitemap_url)
                print(f"Found sitemap index with {len(nested_sitemaps)} nested sitemaps")
            else:
                # This is a regular sitemap, extract page URLs
                for url_elem in root.findall('.//url'):
                    loc = url_elem.find('loc')
                    if loc is not None and loc.text:
                        url = loc.text.strip()
                        # Only include URLs from the same domain
                        if self._is_same_domain(url):
                            urls.append(url)
                print(f"Found regular sitemap with {len(urls)} URLs")
        except ET.ParseError as e:
            print(f"Error parsing sitemap XML: {e}")
        except Exception as e:
            print(f"Unexpected error parsing sitemap: {e}")
        
        return urls, nested_sitemaps
    
    def _get_ssl_context(self):
        """Create SSL context that handles certificate issues"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
    
    async def crawl_page_with_retry(self, url: str, depth: int, max_retries: int = 3) -> Optional[Dict]:
        """Crawl a page with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = await self.crawl_page(url, depth)
                if result and result.get('Status Code') not in ['Error', 'Timeout']:
                    return result
                last_error = result.get('Error', 'Unknown error') if result else 'No response'
            except Exception as e:
                last_error = str(e)
            
            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
        
        # Return error result after all retries failed
        return {
            'Address': url,
            'Status Code': 'Error',
            'Content Type': '',
            'Error': f'Failed after {max_retries} attempts. Last error: {last_error}',
            'Crawl Depth': depth,
        }
    
    async def crawl_page(self, url: str, depth: int) -> Optional[Dict]:
        """Crawl a single page and extract SEO data"""
        try:
            start_time = time.time()
            
            # Set referrer header if we have a parent page
            headers = self.headers.copy()
            if self.visited_urls:
                headers['Referer'] = list(self.visited_urls)[-1]
            
            async with self.session.get(
                url, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
                allow_redirects=True,
                ssl=self._get_ssl_context()
            ) as response:
                load_time = time.time() - start_time
                
                # Get final URL after redirects
                final_url = str(response.url)
                
                # Basic page data
                page_data = {
                    'Address': url,
                    'Final_URL': final_url,
                    'Status Code': response.status,
                    'Content Type': response.headers.get('Content-Type', ''),
                    'Load_Time': round(load_time, 2),
                    'Crawl Depth': depth,
                    'Error': '',  # No error if we got here
                }
                
                # Only parse HTML content
                if 'text/html' in page_data['Content Type']:
                    html = await response.text()
                    # Use html.parser (built into Python, no external dependencies)
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract SEO elements
                    page_data.update(self._extract_seo_data(soup, html))
                    
                    # Extract links for further crawling
                    if depth < self.max_depth:
                        links = self._extract_links(soup, final_url)
                        for link in links:
                            normalized_link = self._normalize_url(link)
                            if (normalized_link not in self.visited_urls and 
                                self._is_same_domain(normalized_link) and
                                self._should_crawl_url(normalized_link)):
                                self.to_visit.append((normalized_link, depth + 1))
                
                return page_data
                
        except asyncio.TimeoutError:
            return {
                'Address': url,
                'Status Code': 'Timeout',
                'Content Type': '',
                'Error': 'Request timeout after 30 seconds',
                'Crawl Depth': depth,
            }
        except aiohttp.ClientSSLError as e:
            return {
                'Address': url,
                'Status Code': 'Error',
                'Content Type': '',
                'Error': f'SSL Error: {str(e)}',
                'Crawl Depth': depth,
            }
        except aiohttp.ClientConnectorError as e:
            return {
                'Address': url,
                'Status Code': 'Error',
                'Content Type': '',
                'Error': f'Connection Error: {str(e)}',
                'Crawl Depth': depth,
            }
        except aiohttp.ClientError as e:
            return {
                'Address': url,
                'Status Code': 'Error',
                'Content Type': '',
                'Error': f'Client Error: {str(e)}',
                'Crawl Depth': depth,
            }
        except Exception as e:
            return {
                'Address': url,
                'Status Code': 'Error',
                'Content Type': '',
                'Error': f'Unexpected Error: {type(e).__name__}: {str(e)}',
                'Crawl Depth': depth,
            }
    
    def _compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        """Compile URL patterns (supports wildcards and regex)"""
        compiled = []
        for pattern in patterns:
            if not pattern.strip():
                continue
            try:
                # Convert wildcards to regex if needed
                if '*' in pattern and not pattern.startswith('^'):
                    # Simple wildcard pattern
                    regex_pattern = pattern.replace('*', '.*').replace('?', '.')
                    regex_pattern = f"^{regex_pattern}$"
                else:
                    # Assume it's already a regex pattern
                    regex_pattern = pattern
                
                compiled.append(re.compile(regex_pattern))
            except re.error:
                # Skip invalid patterns
                continue
        return compiled
    
    def _matches_patterns(self, url: str, patterns: List[re.Pattern]) -> bool:
        """Check if URL matches any of the patterns"""
        for pattern in patterns:
            if pattern.search(url):
                return True
        return False
    
    def _should_crawl_url_advanced(self, url: str) -> Tuple[bool, str]:
        """Advanced URL filtering with include/exclude patterns"""
        # Check exclude patterns first
        if self.exclude_patterns and self._matches_patterns(url, self.exclude_patterns):
            return False, "Excluded by pattern"
        
        # Check include patterns (if any are specified)
        if self.include_patterns and not self._matches_patterns(url, self.include_patterns):
            return False, "Not included by pattern"
        
        # Check robots.txt if enabled
        if self.respect_robots and self.robots_parser:
            try:
                if not self.robots_parser.can_fetch("*", url):
                    return False, "Blocked by robots.txt"
            except:
                pass
        
        # Check file extensions
        skip_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', 
                          '.exe', '.dmg', '.mp3', '.mp4', '.avi', '.mov',
                          '.css', '.js', '.ico', '.xml', '.txt', '.doc',
                          '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
        
        parsed_url = urlparse(url)
        path_lower = parsed_url.path.lower()
        
        if any(path_lower.endswith(ext) for ext in skip_extensions):
            return False, "Non-HTML resource"
        
        return True, ""
    
    def _extract_seo_data(self, soup: BeautifulSoup, html: str) -> Dict:
        """Extract SEO-relevant data from the page"""
        data = {}
        
        # Title tag
        title_tag = soup.find('title')
        data['Title tag'] = title_tag.text.strip() if title_tag else ''
        data['Title tag Length'] = len(data['Title tag'])
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        data['Meta Description'] = meta_desc.get('content', '').strip() if meta_desc else ''
        data['Meta Description Length'] = len(data['Meta Description'])
        
        # Enhanced Header Analysis (Sprint 3)
        h1_tags = soup.find_all('h1')
        data['H1-1'] = h1_tags[0].text.strip() if h1_tags else ''
        data['H1-1 Length'] = len(data['H1-1'])
        data['H1_Count'] = len(h1_tags)
        
        h2_tags = soup.find_all('h2')
        data['H2-1'] = h2_tags[0].text.strip() if h2_tags else ''
        data['H2-1 Length'] = len(data['H2-1'])
        data['H2-2'] = h2_tags[1].text.strip() if len(h2_tags) > 1 else ''
        data['H2-2 Length'] = len(data['H2-2'])
        data['H2_Count'] = len(h2_tags)
        
        # All heading levels (Sprint 3)
        for i in range(3, 7):  # H3 to H6
            h_tags = soup.find_all(f'h{i}')
            data[f'H{i}_Count'] = len(h_tags)
        
        # Heading hierarchy validation
        data['Heading_Hierarchy_Valid'] = self._validate_heading_hierarchy(soup)
        
        # Meta robots
        meta_robots = soup.find('meta', attrs={'name': 'robots'})
        data['Meta Robots 1'] = meta_robots.get('content', '').strip() if meta_robots else ''
        
        # Canonical
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        data['Canonical Link Element 1'] = canonical.get('href', '').strip() if canonical else ''
        
        # Enhanced Content Analysis (Sprint 3)
        main_content = self._extract_main_content(soup)
        data['Word Count'] = len(main_content.split())
        data['Paragraph_Count'] = len(soup.find_all('p'))
        data['Sentence_Count'] = main_content.count('.') + main_content.count('!') + main_content.count('?')
        
        # Flesch Reading Ease Score (Sprint 3)
        if main_content:
            try:
                flesch_score = textstat.flesch_reading_ease(main_content)
                data['Flesch Reading Ease Score'] = round(flesch_score, 1)
                data['Readability'] = self._get_readability_level(flesch_score)
            except:
                data['Flesch Reading Ease Score'] = 0
                data['Readability'] = 'N/A'
        else:
            data['Flesch Reading Ease Score'] = 0
            data['Readability'] = 'N/A'
        
        # Link Analysis (Sprint 3)
        link_data = self._analyze_links(soup)
        data.update(link_data)
        
        # Image SEO Analysis (Sprint 3)
        image_data = self._analyze_images(soup)
        data.update(image_data)
        
        # Structured Data Detection (Sprint 3)
        structured_data = self._detect_structured_data(soup, html)
        data.update(structured_data)
        
        # Indexability - Enhanced for Sprint 2
        robots_content = data['Meta Robots 1'].lower()
        is_noindex = 'noindex' in robots_content
        
        if is_noindex and not self.ignore_noindex:
            data['Indexability'] = 'Non-Indexable'
        elif is_noindex and self.ignore_noindex:
            data['Indexability'] = 'Non-Indexable (crawled anyway)'
        else:
            data['Indexability'] = 'Indexable'
        
        # Initialize fields that will be calculated after crawl
        data['Inlinks'] = 0  # Will calculate after crawl
        data['Unique Inlinks'] = 0  # Will calculate after crawl
        
        return data
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page"""
        links = []
        for tag in soup.find_all('a'):
            href = tag.get('href')
            if href and not href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                # Parse and normalize the URL
                parsed = urlparse(absolute_url)
                if parsed.scheme in ('http', 'https'):
                    links.append(absolute_url)
        return links
    
    def _get_delay(self) -> float:
        """Get delay between requests"""
        # Use robots.txt crawl-delay if specified, otherwise use configured range
        if self.robots_crawl_delay > 0:
            return self.robots_crawl_delay
        else:
            return random.uniform(self.delay_range[0], self.delay_range[1])
    
    async def crawl(self, progress_callback=None, init_progress_callback=None):
        """Main crawl method with hybrid sitemap integration"""
        # Create session with cookie jar for session management
        connector = aiohttp.TCPConnector(ssl=self._get_ssl_context())
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        
        if init_progress_callback:
            init_progress_callback(10, "🔧 Setting up crawler session...")
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar()
        ) as session:
            self.session = session
            
            # Fetch and parse robots.txt first (this also fetches sitemaps)
            if self.respect_robots or self.use_sitemap:
                await self.fetch_and_parse_robots_txt(init_progress_callback)
                self.robots_txt_status = "Fetched and parsed"
            else:
                if init_progress_callback:
                    init_progress_callback(90, "⚠️ Robots.txt and sitemaps disabled")
                self.robots_txt_status = "Ignored (disabled)"
                self.sitemap_status = "Disabled"
            
            # If sitemap is enabled but robots.txt didn't have sitemaps, try common locations
            if self.use_sitemap and not self.sitemap_urls:
                if init_progress_callback:
                    init_progress_callback(95, "🗺️ Trying common sitemap locations...")
                await self._try_common_sitemap_locations()
            
            # Create sitemap queue (lower priority than discovered URLs)
            sitemap_queue = []
            if self.use_sitemap and self.sitemap_urls:
                # Add sitemap URLs to queue with depth 0 (treat as seed URLs)
                for url in self.sitemap_urls:
                    normalized_url = self._normalize_url(url)
                    if normalized_url not in self.visited_urls:
                        sitemap_queue.append((normalized_url, 0))
            
            if init_progress_callback:
                total_urls = len(self.to_visit) + len(sitemap_queue)
                init_progress_callback(100, f"🚀 Starting crawl with {total_urls} URLs ready...")
            
            pages_crawled = 0
            
            # Hybrid crawling: prioritize discovered URLs, then sitemap URLs
            while pages_crawled < self.max_pages:
                url = None
                depth = 0
                source = ""
                
                # First priority: URLs discovered through crawling
                if self.to_visit:
                    url, depth = self.to_visit.pop(0)
                    source = "crawling"
                    self.urls_from_crawling += 1
                # Second priority: URLs from sitemap
                elif sitemap_queue:
                    url, depth = sitemap_queue.pop(0)
                    source = "sitemap"
                    self.urls_from_sitemap += 1
                else:
                    # No more URLs to crawl
                    break
                
                if url in self.visited_urls:
                    continue
                
                # Advanced URL filtering
                should_crawl, skip_reason = self._should_crawl_url_advanced(url)
                if not should_crawl:
                    self.skipped_urls.append({'url': url, 'reason': skip_reason, 'source': source})
                    continue
                
                self.visited_urls.add(url)
                
                # Crawl the page with retry logic
                page_data = await self.crawl_page_with_retry(url, depth)
                if page_data:
                    # Add source information
                    page_data['Discovery_Source'] = source
                    self.results.append(page_data)
                    pages_crawled += 1
                    
                    if progress_callback:
                        progress_callback(pages_crawled, self.max_pages, url)
                
                # Delay between requests
                delay = self._get_delay()
                await asyncio.sleep(delay)
            
            # Post-process to calculate inlinks
            self._calculate_inlinks()
            
            return self.results
    
    async def _try_common_sitemap_locations(self):
        """Try common sitemap locations if not found in robots.txt"""
        base_url = f"{urlparse(self.start_url).scheme}://{self.domain}"
        common_sitemaps = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemaps.xml"
        ]
        
        for sitemap_url in common_sitemaps:
            await self._fetch_and_parse_sitemap(sitemap_url)
            if self.sitemap_urls:  # Stop if we found URLs
                break
    
    def _calculate_inlinks(self):
        """Calculate inlinks for all pages after crawl is complete"""
        # This is a simplified version - will enhance in later sprints
        url_to_index = {page['Address']: i for i, page in enumerate(self.results)}
        
        for page in self.results:
            # For now, just set to 0 - will implement proper link tracking later
            page['Inlinks'] = 0
            page['Unique Inlinks'] = 0
    
    def get_crawl_stats(self) -> Dict:
        """Get crawl statistics"""
        return {
            'total_pages': len(self.results),
            'skipped_urls': len(self.skipped_urls),
            'robots_txt_status': self.robots_txt_status,
            'crawl_delay_used': self.robots_crawl_delay if self.robots_crawl_delay > 0 else f"{self.delay_range[0]}-{self.delay_range[1]}s"
        }
    
    # Sprint 3 Helper Methods
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content text, excluding navigation and footer"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Get text from main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|post|article'))
        
        if main_content:
            text = main_content.get_text()
        else:
            # Fallback to body text
            text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _get_readability_level(self, flesch_score: float) -> str:
        """Convert Flesch Reading Ease score to readability level"""
        if flesch_score >= 90:
            return "Very Easy"
        elif flesch_score >= 80:
            return "Easy"
        elif flesch_score >= 70:
            return "Fairly Easy"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Fairly Difficult"
        elif flesch_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    def _validate_heading_hierarchy(self, soup: BeautifulSoup) -> bool:
        """Check if heading hierarchy is properly structured"""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            return True
        
        current_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if current_level == 0:
                current_level = level
            elif level > current_level + 1:
                return False  # Skipped a level
            current_level = level
        
        return True
    
    def _analyze_links(self, soup: BeautifulSoup) -> Dict:
        """Analyze internal and external links"""
        links = soup.find_all('a', href=True)
        internal_links = 0
        external_links = 0
        
        for link in links:
            href = link.get('href', '')
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            
            # Convert relative to absolute for analysis
            if href.startswith('/') or not href.startswith('http'):
                internal_links += 1
            else:
                parsed_href = urlparse(href)
                if self._is_same_domain(href):
                    internal_links += 1
                else:
                    external_links += 1
        
        return {
            'Internal_Links': internal_links,
            'External_Links': external_links,
            'Total_Links': internal_links + external_links
        }
    
    def _analyze_images(self, soup: BeautifulSoup) -> Dict:
        """Analyze images for SEO"""
        images = soup.find_all('img')
        total_images = len(images)
        images_with_alt = len([img for img in images if img.get('alt')])
        images_without_alt = total_images - images_with_alt
        
        return {
            'Total_Images': total_images,
            'Images_With_Alt': images_with_alt,
            'Images_Without_Alt': images_without_alt,
            'Alt_Text_Coverage': round((images_with_alt / total_images * 100) if total_images > 0 else 0, 1)
        }
    
    def _detect_structured_data(self, soup: BeautifulSoup, html: str) -> Dict:
        """Detect structured data markup"""
        structured_data = {
            'JSON_LD_Count': 0,
            'Microdata_Count': 0,
            'Schema_Types': [],
            'Has_Structured_Data': False
        }
        
        # JSON-LD detection
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        structured_data['JSON_LD_Count'] = len(json_ld_scripts)
        
        # Extract schema types from JSON-LD
        schema_types = set()
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    schema_types.add(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            schema_types.add(item['@type'])
            except:
                pass
        
        # Microdata detection
        microdata_items = soup.find_all(attrs={'itemscope': True})
        structured_data['Microdata_Count'] = len(microdata_items)
        
        # Extract schema types from microdata
        for item in microdata_items:
            itemtype = item.get('itemtype', '')
            if itemtype:
                schema_type = itemtype.split('/')[-1]
                schema_types.add(schema_type)
        
        structured_data['Schema_Types'] = list(schema_types)
        structured_data['Has_Structured_Data'] = len(schema_types) > 0
        
        return structured_data
    
    # Sprint 4: Issue Detection Methods
    def detect_issues(self, results: List[Dict]) -> List[Dict]:
        """Detect SEO issues across all crawled pages"""
        issues = []
        
        # Collect data for duplicate detection
        titles = {}
        meta_descriptions = {}
        content_hashes = {}
        
        for page in results:
            url = page.get('Address', '')
            
            # Title analysis
            title = page.get('Title tag', '').strip()
            if title:
                if title not in titles:
                    titles[title] = []
                titles[title].append(url)
            
            # Meta description analysis
            meta_desc = page.get('Meta Description', '').strip()
            if meta_desc:
                if meta_desc not in meta_descriptions:
                    meta_descriptions[meta_desc] = []
                meta_descriptions[meta_desc].append(url)
            
            # Individual page issues
            page_issues = self._detect_page_issues(page)
            issues.extend(page_issues)
        
        # Duplicate detection
        duplicate_issues = self._detect_duplicates(titles, meta_descriptions)
        issues.extend(duplicate_issues)
        
        # Sort by severity
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        issues.sort(key=lambda x: severity_order.get(x['Severity'], 4))
        
        return issues
    
    def _detect_page_issues(self, page: Dict) -> List[Dict]:
        """Detect issues for a single page"""
        issues = []
        url = page.get('Address', '')
        
        # Critical Issues
        if not page.get('Title tag', '').strip():
            issues.append({
                'Type': 'Missing Title Tag',
                'URL': url,
                'Severity': 'Critical',
                'Description': 'Page has no title tag',
                'Impact': 'Blocks proper indexing and search result display',
                'Fix': 'Add a unique, descriptive title tag (50-60 characters)',
                'Category': 'Technical SEO'
            })
        
        if page.get('Status Code') in [404, 500, 502, 503]:
            issues.append({
                'Type': 'Server Error',
                'URL': url,
                'Severity': 'Critical',
                'Description': f"HTTP {page.get('Status Code')} error",
                'Impact': 'Page cannot be indexed by search engines',
                'Fix': 'Fix server configuration or restore missing content',
                'Category': 'Technical SEO'
            })
        
        # High Priority Issues
        if page.get('H1_Count', 0) == 0:
            issues.append({
                'Type': 'Missing H1 Tag',
                'URL': url,
                'Severity': 'High',
                'Description': 'Page has no H1 heading',
                'Impact': 'Reduces content structure and SEO effectiveness',
                'Fix': 'Add a single, descriptive H1 tag that matches the page topic',
                'Category': 'Content'
            })
        
        if page.get('H1_Count', 0) > 1:
            issues.append({
                'Type': 'Multiple H1 Tags',
                'URL': url,
                'Severity': 'High',
                'Description': f"Page has {page.get('H1_Count')} H1 tags",
                'Impact': 'Confuses search engines about page topic hierarchy',
                'Fix': 'Use only one H1 tag per page, convert others to H2-H6',
                'Category': 'Content'
            })
        
        if not page.get('Meta Description', '').strip():
            issues.append({
                'Type': 'Missing Meta Description',
                'URL': url,
                'Severity': 'High',
                'Description': 'Page has no meta description',
                'Impact': 'Search engines will generate their own snippet',
                'Fix': 'Add a compelling meta description (150-160 characters)',
                'Category': 'Technical SEO'
            })
        
        # Medium Priority Issues
        title_length = page.get('Title tag Length', 0)
        if title_length > 60:
            issues.append({
                'Type': 'Title Too Long',
                'URL': url,
                'Severity': 'Medium',
                'Description': f'Title tag is {title_length} characters (recommended: 50-60)',
                'Impact': 'Title may be truncated in search results',
                'Fix': 'Shorten title to 50-60 characters while keeping it descriptive',
                'Category': 'Content'
            })
        
        meta_desc_length = page.get('Meta Description Length', 0)
        if meta_desc_length > 160:
            issues.append({
                'Type': 'Meta Description Too Long',
                'URL': url,
                'Severity': 'Medium',
                'Description': f'Meta description is {meta_desc_length} characters (recommended: 150-160)',
                'Impact': 'Description may be truncated in search results',
                'Fix': 'Shorten meta description to 150-160 characters',
                'Category': 'Technical SEO'
            })
        
        if page.get('Word Count', 0) < 300:
            issues.append({
                'Type': 'Thin Content',
                'URL': url,
                'Severity': 'Medium',
                'Description': f"Page has only {page.get('Word Count', 0)} words",
                'Impact': 'May be considered low-quality content by search engines',
                'Fix': 'Expand content to at least 300 words with valuable information',
                'Category': 'Content'
            })
        
        if not page.get('Heading_Hierarchy_Valid', True):
            issues.append({
                'Type': 'Poor Heading Hierarchy',
                'URL': url,
                'Severity': 'Medium',
                'Description': 'Heading tags skip levels (e.g., H1 to H3)',
                'Impact': 'Reduces content accessibility and SEO structure',
                'Fix': 'Use heading tags in proper order: H1 → H2 → H3 → H4',
                'Category': 'Content'
            })
        
        # Image Issues
        if page.get('Images_Without_Alt', 0) > 0:
            missing_alt = page.get('Images_Without_Alt', 0)
            issues.append({
                'Type': 'Missing Alt Text',
                'URL': url,
                'Severity': 'Medium',
                'Description': f'{missing_alt} images missing alt text',
                'Impact': 'Reduces accessibility and image SEO potential',
                'Fix': 'Add descriptive alt text to all images',
                'Category': 'Accessibility'
            })
        
        # Low Priority Issues
        if page.get('Flesch Reading Ease Score', 0) < 30:
            issues.append({
                'Type': 'Difficult Readability',
                'URL': url,
                'Severity': 'Low',
                'Description': f"Readability score: {page.get('Flesch Reading Ease Score', 0)} (Very Difficult)",
                'Impact': 'Content may be hard for users to understand',
                'Fix': 'Simplify language, use shorter sentences and paragraphs',
                'Category': 'Content'
            })
        
        if not page.get('Canonical Link Element 1', '').strip():
            issues.append({
                'Type': 'Missing Canonical Tag',
                'URL': url,
                'Severity': 'Low',
                'Description': 'Page has no canonical tag',
                'Impact': 'May cause duplicate content issues',
                'Fix': 'Add self-referencing canonical tag or specify preferred URL',
                'Category': 'Technical SEO'
            })
        
        return issues
    
    def _detect_duplicates(self, titles: Dict, meta_descriptions: Dict) -> List[Dict]:
        """Detect duplicate titles and meta descriptions"""
        issues = []
        
        # Duplicate titles
        for title, urls in titles.items():
            if len(urls) > 1:
                for url in urls:
                    issues.append({
                        'Type': 'Duplicate Title Tag',
                        'URL': url,
                        'Severity': 'High',
                        'Description': f'Title "{title[:50]}..." is used on {len(urls)} pages',
                        'Impact': 'Search engines cannot distinguish between pages',
                        'Fix': 'Create unique, descriptive titles for each page',
                        'Category': 'Technical SEO'
                    })
        
        # Duplicate meta descriptions
        for meta_desc, urls in meta_descriptions.items():
            if len(urls) > 1:
                for url in urls:
                    issues.append({
                        'Type': 'Duplicate Meta Description',
                        'URL': url,
                        'Severity': 'Medium',
                        'Description': f'Meta description is used on {len(urls)} pages',
                        'Impact': 'Reduces uniqueness and click-through rates',
                        'Fix': 'Write unique meta descriptions for each page',
                        'Category': 'Technical SEO'
                    })
        
        return issues
    
    def get_issue_summary(self, issues: List[Dict]) -> Dict:
        """Generate issue summary statistics"""
        summary = {
            'total_issues': len(issues),
            'critical': len([i for i in issues if i['Severity'] == 'Critical']),
            'high': len([i for i in issues if i['Severity'] == 'High']),
            'medium': len([i for i in issues if i['Severity'] == 'Medium']),
            'low': len([i for i in issues if i['Severity'] == 'Low']),
            'categories': {}
        }
        
        # Count by category
        for issue in issues:
            category = issue.get('Category', 'Other')
            if category not in summary['categories']:
                summary['categories'][category] = 0
            summary['categories'][category] += 1
        
        return summary
