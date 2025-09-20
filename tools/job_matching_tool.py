"""
Job Matching Tool - Fuzzy matching and data extraction for OpenAI Agents SDK
"""

import asyncio
from typing import Dict, Any, List
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from utils.logger import setup_logger
import json

logger = setup_logger(__name__)

class JobMatchingTool:
    def __init__(self):
        pass
        
    async def initialize(self):
        """Initialize Job Matching Tool for OpenAI Agents SDK"""
        logger.info("Initializing Job Matching Tool for OpenAI Agents SDK")
        logger.info("Job Matching Tool initialized")
        
    async def find_careers_link(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """Find careers page link from HTML - OpenAI Agents SDK compatible"""
        logger.info("Finding careers page link")
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Extract all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True).lower()
                
                # Convert relative URLs to absolute
                if href.startswith('/') or not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                    
                links.append({
                    'url': href,
                    'text': text,
                    'href_original': link['href']
                })
            
            # Write all links to links.json file
            try:
                links_data = {
                    "base_url": base_url,
                    "total_links": len(links),
                    "timestamp": asyncio.get_event_loop().time(),
                    "links": links
                }
                
                with open("links.json", "w", encoding="utf-8") as f:
                    json.dump(links_data, f, indent=2, ensure_ascii=False)
                    
                logger.info(f"Wrote {len(links)} links to links.json")
                
            except Exception as file_error:
                logger.error(f"Failed to write links to file: {str(file_error)}")
            
            # Find best careers link using fuzzy matching
            careers_keywords = ['career', 'job', 'hiring', 'opportunity', 'employment', 'join', 'work', 'talent', 'careers', 'karriere']
            
            best_match = None
            best_score = 0
            
            for link in links:
                text = link['text']
                url = link['url'].lower()
                
                score = 0
                
                # Direct keyword matching
                for keyword in careers_keywords:
                    if keyword in text:
                        score += 30
                    if keyword in url:
                        score += 25
                        
                # Fuzzy matching for variations
                for keyword in careers_keywords:
                    text_similarity = fuzz.partial_ratio(keyword, text)
                    url_similarity = fuzz.partial_ratio(keyword, url)
                    
                    if text_similarity > 80:
                        score += 20
                    if url_similarity > 80:
                        score += 15
                
                # Bonus for official indicators
                official_words = ['official', 'corporate', 'company']
                if any(word in text or word in url for word in official_words):
                    score += 10
                    
                # Penalty for non-careers content
                penalty_words = ['news', 'blog', 'contact', 'about', 'investor']
                if any(word in text or word in url for word in penalty_words):
                    score -= 15
                
                # Add score to link for debugging
                link['score'] = score
                
                if score > best_score:
                    best_score = score
                    best_match = link
                    
            if best_match and best_score > 20:
                confidence = "high" if best_score > 60 else "medium" if best_score > 35 else "low"
                
                return {
                    "success": True,
                    "careers_url": best_match['url'],
                    "confidence": confidence,
                    "score": best_score,
                    "reasoning": f"Best match found with score {best_score}",
                    "status": "careers_link_found"
                }
            else:
                # Fallback to common careers path
                fallback_url = urljoin(base_url, "/careers")
                return {
                    "success": True,
                    "careers_url": fallback_url,
                    "confidence": "low",
                    "score": 0,
                    "reasoning": "No clear careers link found, using fallback /careers",
                    "status": "fallback_careers_url"
                }
                
        except Exception as e:
            logger.error(f"Careers link finding failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "careers_link_failed"
            }
            
    async def find_best_match(self, job_links: List[Dict], job_title: str, location: str = None) -> Dict[str, Any]:
        """Find best job match using fuzzy matching - OpenAI Agents SDK compatible"""
        logger.info(f"Finding best job match for '{job_title}' from {len(job_links)} links")
        
        try:
            if not job_links:
                return {
                    "success": False,
                    "error": "No job links provided for matching",
                    "status": "no_links_provided"
                }
                
            matches = []
            job_title_lower = job_title.lower()
            location_lower = location.lower() if location else ""
            
            for link in job_links:
                title = link.get('title', '').lower()
                url = link.get('url', '').lower()
                
                # Calculate similarity scores
                title_similarity = fuzz.token_sort_ratio(job_title_lower, title)
                partial_similarity = fuzz.partial_ratio(job_title_lower, title)
                url_similarity = fuzz.partial_ratio(job_title_lower, url)
                
                # Base score from title matching
                base_score = max(title_similarity, partial_similarity * 0.8)
                
                # URL bonus
                url_bonus = url_similarity * 0.3
                
                # Location bonus
                location_bonus = 0
                if location_lower and location_lower in title:
                    location_bonus = 20
                elif location_lower and location_lower in url:
                    location_bonus = 10
                    
                # Keyword matching bonus
                job_keywords = job_title_lower.split()
                keyword_bonus = 0
                for keyword in job_keywords:
                    if len(keyword) > 2:  # Skip short words
                        if keyword in title:
                            keyword_bonus += 15
                        elif fuzz.partial_ratio(keyword, title) > 85:
                            keyword_bonus += 10
                            
                # Calculate total score
                total_score = base_score + url_bonus + location_bonus + keyword_bonus
                
                matches.append({
                    **link,
                    'match_score': total_score,
                    'title_similarity': title_similarity,
                    'partial_similarity': partial_similarity,
                    'url_similarity': url_similarity,
                    'location_bonus': location_bonus,
                    'keyword_bonus': keyword_bonus
                })
                
            # Sort by match score
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            if matches:
                best_match = matches[0]
                confidence = self._get_match_confidence(best_match['match_score'])
                
                return {
                    "success": True,
                    "best_match": best_match,
                    "all_matches": matches[:10],  # Top 10 matches
                    "match_confidence": confidence,
                    "status": "best_match_found"
                }
            else:
                return {
                    "success": False,
                    "error": "No job matches found",
                    "status": "no_matches_found"
                }
                
        except Exception as e:
            logger.error(f"Job matching failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "job_matching_failed"
            }
            
    def _get_match_confidence(self, score: float) -> str:
        """Convert match score to confidence level"""
        if score >= 80:
            return "high"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "low"
        else:
            return "very_low"
            
    async def extract_job_data(self, html_content: str, job_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured job data from HTML - OpenAI Agents SDK compatible"""
        logger.info("Extracting structured job data")
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            text_content = soup.get_text()
            
            # Initialize job data structure
            job_data = {
                "title": None,
                "company": job_params.get("company_name"),
                "location": None,
                "employment_type": None,
                "department": None,
                "salary_range": None,
                "requirements": [],
                "responsibilities": [],
                "description": None,
                "benefits": [],
                "experience_level": None,
                "remote_option": None,
                "posted_date": None,
                "application_deadline": None
            }
            
            # Extract title
            job_data["title"] = await self._extract_job_title(soup, job_params.get("job_title"))
            
            # Extract location
            job_data["location"] = await self._extract_location(text_content)
            
            # Extract employment type
            job_data["employment_type"] = await self._extract_employment_type(text_content)
            
            # Extract salary
            job_data["salary_range"] = await self._extract_salary(text_content)
            
            # Extract remote option
            job_data["remote_option"] = await self._extract_remote_option(text_content)
            
            # Extract experience level
            job_data["experience_level"] = await self._extract_experience_level(text_content)
            
            # Extract requirements and responsibilities
            job_data["requirements"] = await self._extract_requirements(text_content)
            job_data["responsibilities"] = await self._extract_responsibilities(text_content)
            
            # Extract benefits
            job_data["benefits"] = await self._extract_benefits(text_content)
            
            # Create description from first few sentences
            sentences = [s.strip() for s in text_content.split('.') if len(s.strip()) > 20][:5]
            job_data["description"] = '. '.join(sentences) + '.' if sentences else None
            
            return {
                "success": True,
                "job_data": job_data,
                "extracted_text_length": len(text_content),
                "status": "job_data_extracted"
            }
            
        except Exception as e:
            logger.error(f"Job data extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "job_data_extraction_failed"
            }
            
    async def _extract_job_title(self, soup, expected_title: str) -> str:
        """Extract job title from soup"""
        # Try common title selectors
        title_selectors = ['h1', '.job-title', '.position-title', '[class*="title"]', 'title']
        
        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                title_text = element.get_text(strip=True)
                if title_text and len(title_text) > 5:
                    # Check if it's similar to expected title
                    if expected_title and fuzz.partial_ratio(expected_title.lower(), title_text.lower()) > 60:
                        return title_text
                    # Or if it contains job-related keywords
                    if any(word in title_text.lower() for word in ['engineer', 'developer', 'manager', 'analyst', 'consultant', 'specialist']):
                        return title_text
                        
        return expected_title  # Fallback to expected title
        
    async def _extract_location(self, text: str) -> str:
        """Extract location from text using patterns"""
        location_patterns = [
            r'Location:?\s*([^,\n]+(?:,\s*[^,\n]+)*)',
            r'Based in:?\s*([^,\n]+)',
            r'Office:?\s*([^,\n]+)',
            r'City:?\s*([^,\n]+)',
            r'\b([A-Z][a-z]+,\s*[A-Z]{2})\b',  # City, State format
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+,\s*[A-Z]{2})\b'  # City Name, State
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 2 and len(location) < 50:
                    return location
                    
        return None
        
    async def _extract_employment_type(self, text: str) -> str:
        """Extract employment type from text"""
        employment_types = {
            'full-time': ['full-time', 'full time', 'fulltime', 'permanent'],
            'part-time': ['part-time', 'part time', 'parttime'],
            'contract': ['contract', 'contractor', 'freelance', 'temporary'],
            'internship': ['intern', 'internship', 'trainee'],
            'temporary': ['temp', 'temporary', 'seasonal']
        }
        
        text_lower = text.lower()
        
        for emp_type, keywords in employment_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return emp_type.title()
                
        return None
        
    async def _extract_salary(self, text: str) -> str:
        """Extract salary information from text"""
        salary_patterns = [
            r'\$[\d,]+-\$?[\d,]+',
            r'£[\d,]+-£?[\d,]+',
            r'€[\d,]+-€?[\d,]+',
            r'\$[\d,]+(?:\.\d{2})?\s*-\s*\$?[\d,]+(?:\.\d{2})?',
            r'Salary:?\s*([^\n]+)',
            r'Pay:?\s*([^\n]+)',
            r'Compensation:?\s*([^\n]+)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group().strip()
                if '$' in salary or '£' in salary or '€' in salary or any(word in salary.lower() for word in ['salary', 'pay', 'compensation']):
                    return salary
                    
        return None
        
    async def _extract_remote_option(self, text: str) -> str:
        """Extract remote work option from text"""
        remote_indicators = {
            'remote': ['remote', 'work from home', 'wfh', 'telecommute'],
            'hybrid': ['hybrid', 'flexible', 'mixed'],
            'onsite': ['on-site', 'onsite', 'office-based', 'in-office']
        }
        
        text_lower = text.lower()
        
        for option, keywords in remote_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                return option.title()
                
        return None
        
    async def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from text"""
        experience_levels = {
            'entry': ['entry', 'junior', 'graduate', 'trainee', '0-2 years'],
            'mid': ['mid', 'intermediate', '2-5 years', '3-7 years'],
            'senior': ['senior', 'lead', 'principal', '5+ years', '7+ years'],
            'executive': ['director', 'vp', 'executive', 'head of', 'chief']
        }
        
        text_lower = text.lower()
        
        for level, keywords in experience_levels.items():
            if any(keyword in text_lower for keyword in keywords):
                return level.title()
                
        return None
        
    async def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements from text"""
        requirements = []
        
        # Look for requirements sections
        req_patterns = [
            r'Requirements?:?\s*([^:]+(?:\n[^:]+)*)',
            r'Qualifications?:?\s*([^:]+(?:\n[^:]+)*)',
            r'Skills?:?\s*([^:]+(?:\n[^:]+)*)'
        ]
        
        for pattern in req_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                req_text = match.group(1)
                # Split by bullet points or new lines
                req_items = re.split(r'[•\*\-\n]', req_text)
                for item in req_items:
                    item = item.strip()
                    if len(item) > 10 and len(item) < 200:
                        requirements.append(item)
                break
                
        return requirements[:10]  # Limit to 10 requirements
        
    async def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract responsibilities from text"""
        responsibilities = []
        
        # Look for responsibilities sections
        resp_patterns = [
            r'Responsibilities:?\s*([^:]+(?:\n[^:]+)*)',
            r'Duties:?\s*([^:]+(?:\n[^:]+)*)',
            r'You will:?\s*([^:]+(?:\n[^:]+)*)'
        ]
        
        for pattern in resp_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                resp_text = match.group(1)
                # Split by bullet points or new lines
                resp_items = re.split(r'[•\*\-\n]', resp_text)
                for item in resp_items:
                    item = item.strip()
                    if len(item) > 10 and len(item) < 200:
                        responsibilities.append(item)
                break
                
        return responsibilities[:10]  # Limit to 10 responsibilities
        
    async def _extract_benefits(self, text: str) -> List[str]:
        """Extract benefits from text"""
        benefits = []
        
        # Look for benefits sections
        benefit_patterns = [
            r'Benefits:?\s*([^:]+(?:\n[^:]+)*)',
            r'Perks:?\s*([^:]+(?:\n[^:]+)*)',
            r'We offer:?\s*([^:]+(?:\n[^:]+)*)'
        ]
        
        for pattern in benefit_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                benefit_text = match.group(1)
                # Split by bullet points or new lines
                benefit_items = re.split(r'[•\*\-\n]', benefit_text)
                for item in benefit_items:
                    item = item.strip()
                    if len(item) > 5 and len(item) < 100:
                        benefits.append(item)
                break
                
        return benefits[:10]  # Limit to 10 benefits
        
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Job Matching Tool resources")
        # No specific cleanup needed