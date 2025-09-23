"""
HTML Scraping Tool - Content extraction for OpenAI Agents SDK
"""

import asyncio
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.logger import setup_logger

logger = setup_logger(__name__)

class HTMLScrapingTool:
    def __init__(self):
        self.web_navigator = None
        
    async def initialize(self):
        """Initialize HTML Scraping Tool for OpenAI Agents SDK"""
        logger.info("Initializing HTML Scraping Tool for OpenAI Agents SDK")
        logger.info("HTML Scraping Tool initialized")
        
    def set_web_navigator(self, web_navigator):
        """Set the web navigator instance for the tool"""
        self.web_navigator = web_navigator
        
    async def scrape_page(self, include_links: bool = False, clean_text: bool = False) -> Dict[str, Any]:
        """Scrape current page content - OpenAI Agents SDK compatible"""
        if not self.web_navigator or not self.web_navigator.page:
            return {"success": False, "error": "No active web navigator or page"}
            
        logger.info("Scraping current page content")
        
        try:
            # Get HTML content
            html_content = await self.web_navigator.get_page_html()
            
            result = {
                "success": True,
                "html_content": html_content,
                "html_length": len(html_content),
                "current_url": self.web_navigator.page.url,
                "status": "scraping_completed"
            }
            
            if include_links:
                links = await self._extract_all_links(html_content, self.web_navigator.page.url)
                result["links"] = links
                result["links_count"] = len(links)
                
            if clean_text:
                clean_text_content = await self._extract_clean_text(html_content)
                result["clean_text"] = clean_text_content
                result["text_length"] = len(clean_text_content)
                
            logger.info(f"Scraped page: {len(html_content)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Page scraping failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "scraping_failed"
            }
            
    async def find_elements(self, selectors: List[str]) -> Dict[str, Any]:
        """Find elements using CSS selectors - OpenAI Agents SDK compatible"""
        if not self.web_navigator or not self.web_navigator.page:
            return {"success": False, "error": "No active web navigator or page"}
            
        logger.info(f"Finding elements with selectors: {selectors}")
        
        try:
            html_content = await self.web_navigator.get_page_html()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            results = {}
            total_elements = 0
            
            for selector in selectors:
                elements = soup.select(selector)
                element_data = []
                
                for element in elements:
                    element_info = {
                        'tag': element.name,
                        'text': element.get_text(strip=True),
                        'attrs': dict(element.attrs),
                        'html': str(element)[:500]  # Limit HTML length
                    }
                    element_data.append(element_info)
                    
                results[selector] = element_data
                total_elements += len(element_data)
                
            logger.info(f"Found {total_elements} total elements across {len(selectors)} selectors")
            
            return {
                "success": True,
                "elements": results,
                "total_elements": total_elements,
                "selectors_used": selectors,
                "status": "elements_found"
            }
            
        except Exception as e:
            logger.error(f"Element finding failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "selectors": selectors,
                "status": "element_finding_failed"
            }
            
    async def extract_job_links(self) -> Dict[str, Any]:
        """Extract job-related links - OpenAI Agents SDK compatible"""
        if not self.web_navigator or not self.web_navigator.page:
            return {"success": False, "error": "No active web navigator or page"}
            
        logger.info("Extracting job-related links")
        
        try:
            html_content = await self.web_navigator.get_page_html()
            current_url = self.web_navigator.page.url
            
            job_links = await self._find_job_links(html_content, current_url)
            
            return {
                "success": True,
                "job_links": job_links,
                "total_found": len(job_links),
                "current_url": current_url,
                "status": "job_links_extracted"
            }
            
        except Exception as e:
            logger.error(f"Job link extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "job_extraction_failed"
            }
            
    async def extract_forms(self) -> Dict[str, Any]:
        """Extract form information - OpenAI Agents SDK compatible"""
        if not self.web_navigator or not self.web_navigator.page:
            return {"success": False, "error": "No active web navigator or page"}
            
        logger.info("Extracting form information")
        
        try:
            html_content = await self.web_navigator.get_page_html()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            forms = []
            
            for form in soup.find_all('form'):
                form_data = {
                    'action': form.get('action'),
                    'method': form.get('method', 'GET').upper(),
                    'inputs': [],
                    'selects': [],
                    'textareas': [],
                    'buttons': []
                }
                
                # Extract inputs
                for input_elem in form.find_all('input'):
                    input_data = {
                        'type': input_elem.get('type', 'text'),
                        'name': input_elem.get('name'),
                        'id': input_elem.get('id'),
                        'placeholder': input_elem.get('placeholder'),
                        'required': input_elem.has_attr('required'),
                        'value': input_elem.get('value')
                    }
                    form_data['inputs'].append(input_data)
                    
                # Extract selects
                for select_elem in form.find_all('select'):
                    options = [opt.get_text(strip=True) for opt in select_elem.find_all('option')]
                    select_data = {
                        'name': select_elem.get('name'),
                        'id': select_elem.get('id'),
                        'required': select_elem.has_attr('required'),
                        'options': options
                    }
                    form_data['selects'].append(select_data)
                    
                # Extract textareas
                for textarea in form.find_all('textarea'):
                    textarea_data = {
                        'name': textarea.get('name'),
                        'id': textarea.get('id'),
                        'placeholder': textarea.get('placeholder'),
                        'required': textarea.has_attr('required')
                    }
                    form_data['textareas'].append(textarea_data)
                    
                # Extract buttons
                for button in form.find_all(['button', 'input']):
                    if button.name == 'input' and button.get('type') not in ['submit', 'button', 'reset']:
                        continue
                    button_data = {
                        'type': button.get('type', 'button'),
                        'text': button.get_text(strip=True) if button.name == 'button' else button.get('value', ''),
                        'name': button.get('name'),
                        'id': button.get('id')
                    }
                    form_data['buttons'].append(button_data)
                    
                forms.append(form_data)
                
            logger.info(f"Found {len(forms)} forms")
            
            return {
                "success": True,
                "forms": forms,
                "total_forms": len(forms),
                "status": "forms_extracted"
            }
            
        except Exception as e:
            logger.error(f"Form extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "form_extraction_failed"
            }
            
    async def check_for_iframes(self) -> Dict[str, Any]:
        """Check for iframes - OpenAI Agents SDK compatible"""
        if not self.web_navigator or not self.web_navigator.page:
            return {"success": False, "error": "No active web navigator or page"}
            
        logger.info("Checking for iframes")
        
        try:
            html_content = await self.web_navigator.get_page_html()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            iframes = []
            
            for iframe in soup.find_all('iframe'):
                iframe_data = {
                    'src': iframe.get('src'),
                    'id': iframe.get('id'),
                    'name': iframe.get('name'),
                    'width': iframe.get('width'),
                    'height': iframe.get('height'),
                    'title': iframe.get('title')
                }
                iframes.append(iframe_data)
                
            logger.info(f"Found {len(iframes)} iframes")
            
            return {
                "success": True,
                "iframes": iframes,
                "total_iframes": len(iframes),
                "has_iframes": len(iframes) > 0,
                "status": "iframes_checked"
            }
            
        except Exception as e:
            logger.error(f"Iframe checking failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "iframe_check_failed"
            }
            
    async def _extract_all_links(self, html_content: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract all links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Convert relative URLs to absolute
            if href.startswith('/') or not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
                
            # Skip invalid links
            if not href or href == '#' or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
                
            links.append({
                'url': href,
                'text': text,
                'original_href': link['href'],
                'title': link.get('title', ''),
                'class': link.get('class', [])
            })
            
        return links
        
    async def _extract_clean_text(self, html_content: str) -> str:
        """Extract clean text content from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
            
        # Extract text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        return clean_text
        
    async def _find_job_links(self, html_content: str, base_url: str) -> List[Dict[str, Any]]:
        """Find job-related links in HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        job_links = []
        
        # Job-related keywords and patterns
        job_keywords = [
            'job', 'career', 'position', 'role', 'opening', 'vacancy', 
            'opportunity', 'hiring', 'employment', 'apply', 'application'
        ]
        
        # Common job link selectors
        job_selectors = [
            'a[href*="job"]',
            'a[href*="career"]', 
            'a[href*="position"]',
            'a[href*="apply"]',
            '.job-title a',
            '.position-title a',
            '.job-listing a',
            '.career-item a',
            '[class*="job"] a',
            '[class*="career"] a'
        ]
        
        # First try specific selectors
        for selector in job_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    if link.get('href'):
                        href = link['href']
                        text = link.get_text(strip=True)
                        
                        # Convert to absolute URL
                        if href.startswith('/') or not href.startswith(('http://', 'https://')):
                            href = urljoin(base_url, href)
                            
                        job_links.append({
                            'url': href,
                            'title': text,
                            'selector': selector,
                            'type': 'selector_match'
                        })
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {str(e)}")
                continue
        
        # Then try keyword-based matching
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True).lower()
            href_lower = href.lower()
            
            # Check if link text or href contains job keywords
            keyword_score = 0
            for keyword in job_keywords:
                if keyword in text or keyword in href_lower:
                    keyword_score += 1
                    
            if keyword_score > 0:
                # Convert to absolute URL
                if href.startswith('/') or not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                    
                # Check if already added
                if not any(existing['url'] == href for existing in job_links):
                    job_links.append({
                        'url': href,
                        'title': link.get_text(strip=True),
                        'keyword_score': keyword_score,
                        'type': 'keyword_match'
                    })
        
        # Remove duplicates and sort by relevance
        seen_urls = set()
        unique_links = []
        
        for link in job_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
                
        # Sort by keyword score if available, otherwise by type
        unique_links.sort(key=lambda x: (
            x.get('keyword_score', 0),
            1 if x.get('type') == 'selector_match' else 0
        ), reverse=True)
        
        return unique_links
    
    async def extract_job_listings_with_llm(self, job_title: str) -> Dict[str, Any]:
        """Use LLM to analyze page and extract job listings intelligently"""
        if not self.web_navigator or not self.web_navigator.page:
            return {"success": False, "error": "No active web navigator or page"}
            
        logger.info("Using LLM to analyze page for job listings")
        
        try:
            html_content = await self.web_navigator.get_page_html()
            
            # Clean HTML for LLM analysis
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script/style but keep structure
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get a reasonable chunk of HTML for analysis (not too big for tokens)
            html_for_analysis = str(soup)#[:15000]
            
            # Create LLM analysis prompt
            prompt = f"""
            Analyze this careers page HTML and identify all job listings/postings.
            
            I'm looking for: "{job_title}"
            
            Please find ALL job opportunities on this page. Look for:
            - Job titles and position names
            - Links to individual job postings
            - Application buttons or "Apply" links
            - Job descriptions or snippets
            - Any clickable elements that represent job opportunities
            
            Don't rely on specific HTML tags or CSS classes. Understand the content semantically.
            
            HTML content:
            {html_for_analysis}
            
            Return JSON format:
            {{
                "jobs_found": [
                    {{
                        "title": "exact job title found",
                        "url": "link to job posting (href or onclick URL)",
                        "description": "any description/snippet found",
                        "relevance_score": 0-100,
                        "location": "location if mentioned"
                    }}
                ],
                "total_jobs": number,
                "analysis_notes": "what you observed about the page structure"
            }}
            """
            
            # For now, use heuristic analysis (replace with actual LLM call)
            analysis_result = await self._llm_analyze_jobs_heuristic(html_content, job_title)
            
            return {
                "success": True,
                "job_listings": analysis_result.get("jobs_found", []),
                "total_found": analysis_result.get("total_jobs", 0),
                "analysis": analysis_result.get("analysis_notes", "")
            }
            
        except Exception as e:
            logger.error(f"LLM job extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _llm_analyze_jobs_heuristic(self, html_content: str, job_title: str) -> Dict[str, Any]:
        """Heuristic LLM-like analysis until real LLM integration"""
        soup = BeautifulSoup(html_content, 'html.parser')
        current_url = self.web_navigator.current_url
        
        jobs_found = []
        
        # Strategy 1: Find text that looks like job titles
        job_title_indicators = ['engineer', 'manager', 'analyst', 'consultant', 'developer', 'specialist', 'berater', 'designer']
        
        # Look for headings, links, and divs containing job-like text
        potential_jobs = []
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'a', 'div', 'span']):
            text = element.get_text(strip=True)
            
            # Skip if text is too short or too long
            if len(text) < 5 or len(text) > 100:
                continue
                
            # Check if text looks like a job title
            text_lower = text.lower()
            
            # Score based on job-like characteristics
            job_score = 0
            
            # Contains job title indicators
            for indicator in job_title_indicators:
                if indicator in text_lower:
                    job_score += 20
                    
            # Contains specific search terms
            search_terms = job_title.lower().split()
            for term in search_terms:
                if len(term) > 2 and term in text_lower:
                    job_score += 30
                    
            # Patterns that suggest job titles
            if any(pattern in text_lower for pattern in ['(m/w/d)', '(m/f/d)', 'full-time', 'part-time']):
                job_score += 25
                
            # German job patterns
            if any(pattern in text_lower for pattern in ['berater', 'ingenieur', 'entwickler', 'manager']):
                job_score += 20
                
            # Penalty for non-job content
            if any(avoid in text_lower for avoid in ['cookie', 'privacy', 'about us', 'contact', 'footer']):
                job_score -= 50

            if job_score >= 30:
                logger.info(f"Found potential job: '{text}' (score: {job_score})")
                logger.info(f"Element: {element.name}, Parent: {element.parent.name if element.parent else 'None'}")
                
            if job_score >= 30:
                # Try to find associated URL
                job_url = None
                
                # If element itself is a link
                if element.name == 'a' and element.get('href'):
                    job_url = element['href']
                
                # Look for clickable parent
                elif element.parent and element.parent.name == 'a':
                    job_url = element.parent.get('href')
                    
                # Look for onclick events
                elif element.get('onclick'):
                    onclick_text = element.get('onclick', '')
                    if 'location' in onclick_text or 'href' in onclick_text:
                        job_url = onclick_text
                        
                # Convert relative URLs
                if job_url and not job_url.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    job_url = urljoin(current_url, job_url)
                    
                potential_jobs.append({
                    'title': text,
                    'url': job_url or current_url,
                    'score': job_score,
                    'element': element.name
                })
        
        # Sort by score and take best matches
        potential_jobs.sort(key=lambda x: x['score'], reverse=True)
        
        # Convert to final format
        for job in potential_jobs[:10]:  # Top 10 matches
            jobs_found.append({
                'title': job['title'],
                'url': job['url'],
                'description': f"Found in {job['element']} element",
                'relevance_score': job['score'],
                'location': None  # Could extract location later
            })
        
        return {
            'jobs_found': jobs_found,
            'total_jobs': len(jobs_found),
            'analysis_notes': f"Analyzed page content semantically, found {len(potential_jobs)} potential job matches"
        }
        
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up HTML Scraping Tool resources")
        # No specific cleanup needed for this tool