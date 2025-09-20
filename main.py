#!/usr/bin/env python3
"""
Job Scraper Main Script - Using OpenAI Agents SDK
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from agents import Agent
from magents.lead_agent import LeadAgent
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

class JobScraperSystem:
    def __init__(self):
        self.lead_agent = None
        self.output_file = "output.json"
        
    async def initialize(self):
        """Initialize the lead agent using OpenAI Agents SDK"""
        logger.info("Initializing Job Scraper System with OpenAI Agents SDK")
        
        self.lead_agent = LeadAgent()
        await self.lead_agent.initialize()
        
        logger.info("Job Scraper System initialized successfully")
        
    def get_user_input(self):
        """Get required inputs from user"""
        print("Job Scraper - Please provide the following information:")
        
        # Get job title (mandatory)
        job_title = input("Job Title (mandatory): ").strip()
        while not job_title:
            print("Job title is required!")
            job_title = input("Job Title (mandatory): ").strip()
            
        # Get company name or domain (at least one is mandatory)
        company_name = input("Company Name (optional if domain provided): ").strip()
        company_domain = input("Company Domain (optional if name provided): ").strip()
        
        while not company_name and not company_domain:
            print("Either company name or company domain is required!")
            company_name = input("Company Name: ").strip()
            if not company_name:
                company_domain = input("Company Domain: ").strip()
                
        # Get location (optional)
        location = input("Location (optional): ").strip()
        
        return {
            "job_title": job_title,
            "company_name": company_name if company_name else None,
            "company_domain": company_domain if company_domain else None,
            "location": location if location else None
        }
        
    async def scrape_job(self, job_params):
        """Main scraping workflow using OpenAI Agents SDK"""
        logger.info(f"Starting job scrape for: {job_params}")
        
        try:
            # Process job request using the lead agent
            result = await self.lead_agent.process_job_request(job_params)
            
            # Save result to JSON
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Job scraping completed. Results saved to {self.output_file}")
            return result
            
        except Exception as e:
            logger.error(f"Error during job scraping: {str(e)}")
            error_result = {
                "error": str(e),
                "job_params": job_params,
                "success": False
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)
                
            raise
            
    async def cleanup(self):
        """Cleanup resources"""
        if self.lead_agent:
            await self.lead_agent.cleanup()

async def main():
    """Main function"""
    scraper_system = JobScraperSystem()
    
    try:
        # Initialize the system
        await scraper_system.initialize()
        
        # Get user input
        job_params = scraper_system.get_user_input()
        
        # Perform scraping
        result = await scraper_system.scrape_job(job_params)
        
        print(f"\nScraping completed!")
        print(f"Results saved to: {scraper_system.output_file}")
        
        if result.get("success"):
            job_data = result.get('job_data', {})
            print(f"Job found: {job_data.get('title', 'Unknown')}")
            print(f"Company: {job_data.get('company', 'Unknown')}")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        logger.info("Scraping interrupted by user")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"Main execution error: {str(e)}")
        
    finally:
        await scraper_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())