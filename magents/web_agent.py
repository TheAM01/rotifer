"""
Web Agent - Handles web navigation and scraping using OpenAI Agents SDK
"""

import asyncio
from typing import Dict, Any

from agents import Agent, function_tool
from tools.web_navigation_tool import WebNavigationTool
from tools.html_scraping_tool import HTMLScrapingTool
from tools.search_tool import SearchTool
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Define tools as functions for Web Agent
@function_tool
def navigate_to_url_tool(url: str) -> str:
    """Navigate to a specific URL"""
    return f"Navigating to: {url}"

@function_tool
def scrape_page_content_tool(include_links: bool = True, clean_text: bool = False) -> str:
    """Scrape HTML content from current page"""
    return f"Scraping page content (links: {include_links}, clean: {clean_text})"

@function_tool
def search_company_website_tool(company_name: str) -> str:
    """Search for a company's official website using search engines"""
    return f"Searching for company: {company_name}"

@function_tool
def interact_with_element_tool(action: str, selector: str, value: str = None) -> str:
    """Interact with page elements (click, fill forms, submit)"""
    return f"Interacting: {action} on {selector} with {value}"

@function_tool
def find_page_elements_tool(selectors: str) -> str:
    """Find specific elements on the page using CSS selectors"""
    return f"Finding elements: {selectors}"

@function_tool
def handle_page_search_tool(job_title: str) -> str:
    """Handle search functionality on current page"""
    return f"Searching page for: {job_title}"

@function_tool
def check_page_iframes_tool() -> str:
    """Check for iframes on current page"""
    return "Checking for iframes"

class WebAgent(Agent):
    def __init__(self, web_nav_tool: WebNavigationTool, scraping_tool: HTMLScrapingTool, search_tool: SearchTool):
        super().__init__(
            name="WebNavigationAgent",
            instructions="""
            You are a web navigation and scraping specialist agent.
            
            Your responsibilities:
            1. Navigate to websites and handle page loading
            2. Search for company websites using search engines
            3. Scrape HTML content from web pages
            4. Interact with web page elements (forms, buttons, search bars)
            5. Handle dynamic content, iframes, and complex page structures
            6. Perform searches within websites using their search functionality
            
            Always ensure pages are fully loaded before scraping content.
            Handle errors gracefully and provide detailed feedback about navigation results.
            """,
            model="gpt-4o-mini",
            tools=[
                navigate_to_url_tool,
                scrape_page_content_tool,
                search_company_website_tool,
                interact_with_element_tool,
                find_page_elements_tool,
                handle_page_search_tool,
                check_page_iframes_tool
            ]
        )
        
        # Store tool references
        self.web_nav_tool = web_nav_tool
        self.scraping_tool = scraping_tool
        self.search_tool = search_tool
        
    async def initialize(self):
        """Initialize the Web Agent with tools"""
        logger.info("Initializing Web Agent with OpenAI Agents SDK")
        
        # Set up scraping tool with navigator reference
        self.scraping_tool.set_web_navigator(self.web_nav_tool)
        
        logger.info("Web Agent initialized with all tools registered")
        
    async def search_company(self, company_name: str) -> Dict[str, Any]:
        """Search for company website and navigate to it"""
        logger.info(f"Web Agent searching for company: {company_name}")
        
        try:
            # Use search tool to find company website
            search_result = await self.search_tool.search_company_website(company_name)
            
            if search_result.get("success"):
                # Navigate to the found website
                nav_result = await self.web_nav_tool.navigate_to_url(search_result["url"])
                
                if nav_result.get("success"):
                    return {
                        "success": True,
                        "url": search_result["url"],
                        "title": nav_result.get("title", ""),
                        "confidence": search_result.get("confidence", "medium"),
                        "message": f"Successfully found and navigated to {company_name} website"
                    }
                    
            raise Exception(f"Could not find or navigate to website for {company_name}")
            
        except Exception as e:
            logger.error(f"Company search failed: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """Navigate to specific URL"""
        logger.info(f"Web Agent navigating to: {url}")
        
        try:
            result = await self.web_nav_tool.navigate_to_url(url)
            
            if result.get("success"):
                # Wait for page to stabilize
                await asyncio.sleep(2)
                
            return result
            
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def scrape_current_page(self) -> Dict[str, Any]:
        """Scrape HTML content from current page"""
        logger.info("Web Agent scraping current page")
        
        try:
            result = await self.scraping_tool.scrape_page(
                include_links=True, 
                clean_text=False
            )
            
            logger.info(f"Scraped page content: {result.get('html_length', 0)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Page scraping failed: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def search_jobs_on_page(self, job_title: str) -> Dict[str, Any]:
        """Search for jobs using the page's search functionality"""
        logger.info(f"Web Agent searching for jobs on page: {job_title}")
        
        try:
            # First, find search forms and inputs
            forms_result = await self.scraping_tool.extract_forms()
            
            if not forms_result.get("success") or not forms_result.get("forms"):
                return {"success": False, "error": "No search forms found on page"}
                
            # Find the most likely job search form/input
            search_input = None
            for form in forms_result["forms"]:
                for input_field in form["inputs"]:
                    if input_field["type"] in ["text", "search"]:
                        name = input_field.get("name", "").lower()
                        placeholder = input_field.get("placeholder", "").lower()
                        
                        if any(keyword in name or keyword in placeholder 
                              for keyword in ["search", "job", "title", "keyword", "query"]):
                            search_input = input_field
                            break
                            
                if search_input:
                    break
                    
            if not search_input:
                return {"success": False, "error": "No suitable search input found"}
                
            # Construct selector for the input
            if search_input.get("id"):
                selector = f"#{search_input['id']}"
            elif search_input.get("name"):
                selector = f"input[name='{search_input['name']}']"
            else:
                selector = "input[type='search'], input[type='text']"
                
            # Fill and submit the search
            fill_result = await self.web_nav_tool.interact_with_element("fill", selector, job_title)
            
            if fill_result.get("success"):
                submit_result = await self.web_nav_tool.interact_with_element("submit", selector)
                
                if submit_result.get("success"):
                    # Wait for search results
                    await asyncio.sleep(3)
                    return {
                        "success": True,
                        "current_url": submit_result.get("current_url"),
                        "message": f"Successfully searched for '{job_title}'"
                    }
                    
            return {"success": False, "error": "Failed to submit search"}
            
        except Exception as e:
            logger.error(f"Job search failed: {str(e)}")
            return {"success": False, "error": str(e)}
            
    async def handle_iframe_content(self) -> Dict[str, Any]:
        """Handle content inside iframes"""
        logger.info("Web Agent handling iframe content")
        
        try:
            iframe_result = await self.scraping_tool.check_for_iframes()
            
            if iframe_result.get("has_iframes"):
                iframes = iframe_result["iframes"]
                
                # Try to interact with the first meaningful iframe
                for iframe in iframes:
                    if iframe.get("src"):
                        # Navigate to iframe source if it's a full URL
                        if iframe["src"].startswith(("http://", "https://")):
                            nav_result = await self.web_nav_tool.navigate_to_url(iframe["src"])
                            if nav_result.get("success"):
                                return nav_result
                                
            return {"success": False, "error": "No actionable iframes found"}
            
        except Exception as e:
            logger.error(f"Iframe handling failed: {str(e)}")
            return {"success": False, "error": str(e)}
        
    async def cleanup(self):
        """Cleanup Web Agent resources"""
        logger.info("Cleaning up Web Agent resources")
        # Cleanup handled by tools