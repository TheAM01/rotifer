"""
Lead Agent - Main orchestrator using OpenAI Agents SDK
"""

import asyncio
import json
from typing import Dict, Any

from agents import Agent, function_tool
from magents.web_agent import WebAgent
from magents.analyzer_agent import AnalyzerAgent
from tools.web_navigation_tool import WebNavigationTool
from tools.html_scraping_tool import HTMLScrapingTool
from tools.search_tool import SearchTool
from tools.job_matching_tool import JobMatchingTool
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Define tools as functions for the Lead Agent
@function_tool
def coordinate_company_search(company_name: str) -> str:
    """Search for company website and navigate to it"""
    return f"Searching for company: {company_name}"

@function_tool 
def coordinate_navigation(url: str) -> str:
    """Navigate to specific URL"""
    return f"Navigating to: {url}"

@function_tool
def coordinate_page_analysis(page_type: str, content: str) -> str:
    """Analyze page content for specific purpose"""
    return f"Analyzing {page_type} page content"

class LeadAgent(Agent):
    def __init__(self):
        super().__init__(
            name="JobScrapingLeadAgent",
            instructions="""
            You are the lead agent responsible for orchestrating job scraping operations.
            
            Your responsibilities:
            1. Coordinate with specialized agents to complete job scraping tasks
            2. Manage the workflow: company discovery → careers page → job listings → specific job → data extraction
            3. Handle errors and coordinate retry strategies
            4. Ensure all steps complete successfully before returning results
            
            Available sub-agents:
            - WebAgent: For navigation, scraping, and web interactions
            - AnalyzerAgent: For HTML analysis, job matching, and data extraction
            
            Always maintain context and coordinate the full workflow to completion.
            """,
            model="gpt-4o-mini",  # Use gpt-4o-mini as it's more available
            tools=[coordinate_company_search, coordinate_navigation, coordinate_page_analysis]
        )
        
        # Initialize sub-agents
        self.web_agent = None
        self.analyzer_agent = None
        
        # Initialize tools
        self.web_nav_tool = None
        self.scraping_tool = None
        self.search_tool = None
        self.job_matching_tool = None
        
    async def initialize(self):
        """Initialize all agents and tools using OpenAI Agents SDK"""
        logger.info("Initializing Lead Agent with OpenAI Agents SDK")
        
        # Initialize tools first
        self.web_nav_tool = WebNavigationTool()
        self.scraping_tool = HTMLScrapingTool()
        self.search_tool = SearchTool()
        self.job_matching_tool = JobMatchingTool()
        
        await self.web_nav_tool.initialize()
        await self.scraping_tool.initialize()
        await self.search_tool.initialize()
        await self.job_matching_tool.initialize()
        
        # Initialize sub-agents with tools
        self.web_agent = WebAgent(
            web_nav_tool=self.web_nav_tool,
            scraping_tool=self.scraping_tool,
            search_tool=self.search_tool
        )
        
        self.analyzer_agent = AnalyzerAgent(
            scraping_tool=self.scraping_tool,
            job_matching_tool=self.job_matching_tool
        )
        
        await self.web_agent.initialize()
        await self.analyzer_agent.initialize()
        
        logger.info("All agents and tools initialized successfully")
        
    async def process_job_request(self, job_params: Dict[str, Any]) -> Dict[str, Any]:
        """Process job scraping request by coordinating agents"""
        logger.info(f"Lead Agent processing job request: {job_params}")
        
        try:
            # Step 1: Determine company URL
            logger.info("Step 1: Determining company URL")
            company_url = await self._get_company_url(job_params)
            
            # Step 2: Find careers page
            logger.info("Step 2: Finding careers page")
            careers_url = await self._find_careers_page(company_url)
            
            # Step 3: Navigate to careers and analyze page structure
            logger.info("Step 3: Analyzing careers page structure")
            careers_analysis = await self._analyze_careers_page(careers_url, job_params)
            
            # Step 4: Find job listings
            logger.info("Step 4: Finding job listings")
            job_listings_url = await self._find_job_listings(careers_analysis, job_params)
            
            # Step 5: Find specific job match
            logger.info("Step 5: Finding specific job match")
            specific_job_url = await self._find_specific_job(job_listings_url, job_params)
            
            # Step 6: Extract job data
            logger.info("Step 6: Extracting job data")
            job_data = await self._extract_job_data(specific_job_url, job_params)
            
            # Compile final results
            result = {
                "success": True,
                "job_params": job_params,
                "workflow_steps": {
                    "company_url": company_url,
                    "careers_url": careers_url,
                    "job_listings_url": job_listings_url,
                    "specific_job_url": specific_job_url
                },
                "job_data": job_data,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            logger.info("Job scraping workflow completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Lead Agent error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "job_params": job_params,
                "timestamp": asyncio.get_event_loop().time()
            }
            
    async def _get_company_url(self, job_params: Dict[str, Any]) -> str:
        """Get company URL using Web Agent"""
        if job_params.get("company_domain"):
            domain = job_params["company_domain"]
            if not domain.startswith(("http://", "https://")):
                domain = f"https://{domain}"
            return domain
        else:
            # Use Web Agent to search for company
            company_name = job_params["company_name"]
            search_result = await self.web_agent.search_company(company_name)
            return search_result["url"]
            
    async def _find_careers_page(self, company_url: str) -> str:
        """Find careers page using Web Agent and Analyzer Agent coordination"""
        # Navigate to company website using Web Agent
        await self.web_agent.navigate_to_url(company_url)
        
        # Get page content using Web Agent
        page_content = await self.web_agent.scrape_current_page()
        
        # Analyze content to find careers link using Analyzer Agent
        careers_analysis = await self.analyzer_agent.find_careers_link(
            page_content["html_content"], 
            {"base_url": company_url}
        )
        
        return careers_analysis["careers_url"]
        
    async def _analyze_careers_page(self, careers_url: str, job_params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze careers page structure"""
        # Navigate to careers page
        await self.web_agent.navigate_to_url(careers_url)
        
        # Scrape careers page
        page_content = await self.web_agent.scrape_current_page()
        
        # Analyze page structure
        analysis = await self.analyzer_agent.analyze_page_structure(
            page_content["html_content"],
            {"goal": "find_job_listings", "job_params": job_params}
        )
        
        analysis["careers_url"] = careers_url
        return analysis
        
    async def _find_job_listings(self, careers_analysis: Dict[str, Any], job_params: Dict[str, Any]) -> str:
        """Find job listings using LLM decision making"""
        
        # Get current page content
        page_content = await self.web_agent.scrape_current_page()
        
        # Let LLM decide what to do on this careers page
        decision = await self.analyzer_agent.decide_careers_page_action(
            page_content["html_content"],
            job_params["job_title"]
        )
        
        logger.info(f"LLM Decision: {decision['reasoning']}")
        
        action = decision.get("action", "search_links")
        
        if action == "use_search":
            # Use search functionality
            search_result = await self.web_agent.search_jobs_on_page(job_params["job_title"])
            return search_result.get("current_url", self.web_nav_tool.current_url)
            
        elif action == "navigate_to_link":
            # Navigate to specific promising link
            target_url = decision["target_url"]
            if not target_url.startswith(('http://', 'https://')):
                from urllib.parse import urljoin
                target_url = urljoin(self.web_nav_tool.current_url, target_url)
            await self.web_agent.navigate_to_url(target_url)
            return target_url
            
        elif action == "extract_jobs_current_page":
            # Current page has job listings
            return self.web_nav_tool.current_url
            
        else:
            # Fallback: analyze all links
            return await self._fallback_link_analysis(page_content, job_params)
            
    async def _find_specific_job(self, job_listings_url: str, job_params: Dict[str, Any]) -> str:
        """Find specific job posting"""
        # Get current page content
        page_content = await self.web_agent.scrape_current_page()
        
        # Extract job links using Analyzer Agent
        job_links_result = await self.analyzer_agent.extract_job_links(
            page_content["html_content"],
            job_params
        )
        
        if not job_links_result.get("job_links"):
            raise Exception("No job listings found on the page")
            
        # Find best match using Analyzer Agent
        best_match = await self.analyzer_agent.find_best_job_match(
            job_links_result["job_links"],
            job_params
        )
        
        # Navigate to the best matching job
        await self.web_agent.navigate_to_url(best_match["url"])
        
        return best_match["url"]
        
    async def _extract_job_data(self, job_url: str, job_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract job data using Analyzer Agent"""
        # Get job posting content
        page_content = await self.web_agent.scrape_current_page()
        
        # Extract structured job data using Analyzer Agent
        job_data = await self.analyzer_agent.extract_job_data(
            page_content["html_content"],
            job_params
        )
        
        return job_data["job_data"]
        
    async def cleanup(self):
        """Cleanup all resources"""
        logger.info("Cleaning up Lead Agent resources")
        
        # Cleanup sub-agents
        if self.web_agent:
            await self.web_agent.cleanup()
            
        if self.analyzer_agent:
            await self.analyzer_agent.cleanup()
            
        # Cleanup tools
        for tool in [self.web_nav_tool, self.scraping_tool, self.search_tool, self.job_matching_tool]:
            if tool and hasattr(tool, 'cleanup'):
                await tool.cleanup()
                
        logger.info("Lead Agent cleanup completed")