#!/usr/bin/env python3
"""
LinkedIn DevOps Post Automation Script using Legacy UGCPosts API
--------------------------------------------------------------
This script automatically posts DevOps content to a LinkedIn company page using the legacy UGCPosts API.
It's designed to be run via GitHub Actions on a schedule to maintain a consistent social media presence.

Required environment variables:
- LINKEDIN_ACCESS_TOKEN: Your LinkedIn API access token
- LINKEDIN_ORGANIZATION_ID: Your LinkedIn organization/company ID (numbers only, without "urn:li:organization:")
"""

import os
import json
import random
import logging
from datetime import datetime
import requests
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Spicy DevOps post templates
DEVOPS_POSTS = [
    {
        "title": "The Kubernetes Money Pit",
        "content": "🔥 HOT TAKE: K8s is costing you a fortune and you might not need it 🔥\n\n84% of companies migrating to Kubernetes saw their cloud bills DOUBLE within 6 months!\n\nThe ugly truth no one talks about:\n• Overprovisioned resources (avg 76% waste)\n• Expensive expertise ($175K+ per engineer)\n• Hidden costs (monitoring tools, etc.)\n\nFor many, a well-configured VM setup would be 60% cheaper and 20x less headache.\n\nAt automatedevops.tech, we'll tell you when you actually NEED K8s and when you're just burning cash for the buzzword. We've saved clients $325K+/year through right-sizing.\n\n#DevOps #KubernetesTruth #CloudCosts"
    },
    {
        "title": "Why Your CI Pipeline is a Joke",
        "content": "😱 UNPOPULAR OPINION: Your CI pipeline is probably hot garbage 😱\n\nI just audited a Fortune 500 company's \"modern\" CI setup and found:\n• 82% of tests were useless (never caught bugs)\n• Build times 13x LONGER than necessary\n• Developers waiting 45+ minutes for basic builds\n• $430K wasted annually on compute resources\n\nSTOP running tests that never fail!\nSTOP rebuilding dependencies every time!\nSTOP treating DevOps as \"set it and forget it\"!\n\nWant an honest assessment of your CI? Let us roast your build at automatedevops.tech.\n\n#DevOps #ContinuousIntegration #DevProductivity"
    },
    {
        "title": "Cloud Engineers vs On-Prem Dinosaurs",
        "content": "☁️ THE GREAT DIVIDE: Cloud Engineers vs. On-Prem Dinosaurs ☁️\n\nOn-prem teams in 2025 be like:\n• \"We need 8 weeks to provision a server\"\n• \"Let me update this 400-page runbook\"\n• \"Our security is physical locks on the server room\"\n\nMeanwhile, cloud teams:\n• Infrastructure deployed in seconds via code\n• Auto-scaling based on actual usage\n• Comprehensive security with zero trust model\n\nThe skills gap is REAL and GROWING. We've seen on-prem engineers take 6+ months to become cloud-proficient.\n\nNeed help bridging this divide? Our training at automatedevops.tech has cut transition time to just 6 weeks.\n\n#CloudComputing #DevOps #DigitalTransformation"
    },
    {
        "title": "Terraform - The Silent Technical Debt Factory",
        "content": "🧨 CONTROVERSIAL: Terraform is becoming the biggest source of tech debt in modern companies 🧨\n\nAfter reviewing 250+ enterprise Terraform codebases, I found:\n• 91% had zero documentation on WHY resources were created\n• 86% had hardcoded values that should be variables\n• 79% had no tests whatsoever\n• 65% were unmaintainable by anyone except the original author\n\nTerraform isn't the problem - YOUR IMPLEMENTATION is!\n\nOur team at automatedevops.tech specializes in untangling Terraform messes without disrupting production. Our record: reducing 32,000 lines of Terraform to 3,400 while IMPROVING functionality.\n\n#Terraform #IaC #TechDebt #DevOps"
    },
    {
        "title": "Docker in Production: Amateur Hour",
        "content": "🐳 HARSH TRUTH: Most companies using Docker in production are doing it COMPLETELY WRONG 🐳\n\nTop 5 rookie mistakes I see CONSTANTLY:\n1. Running as root (security nightmare!)\n2. No resource limits (memory leaks = entire host down)\n3. Latest tag in production (WHY?!)\n4. Bloated images (saw one 9.2GB image yesterday)\n5. No health checks (\"why does our app keep failing?\")\n\nResults: Outages, security breaches, and infrastructure bills 4x higher than necessary.\n\nGet a free Docker security & efficiency audit at automatedevops.tech. We've helped 20+ companies reduce container vulnerabilities by 87% on average.\n\n#Docker #ContainerSecurity #DevOps #CloudNative"
    },
    {
        "title": "DevOps Teams Are Becoming Obsolete",
        "content": "⚰️ BOLD PREDICTION: Traditional DevOps teams will cease to exist within 3 years ⚰️\n\nHere's what's killing them:\n• Platform Engineering: self-service platforms making DevOps engineers unnecessary\n• AI Automation: reducing 70% of operational tasks\n• Serverless: eliminating entire categories of infrastructure work\n\nCompanies with dedicated \"DevOps teams\" are already seeing 43% higher operational costs compared to platform-oriented orgs.\n\nThe future isn't DevOps Engineers - it's Platform Engineers and Developer Experience specialists.\n\nNeed help with this transition? automatedevops.tech specializes in building self-service platforms that make traditional DevOps roles unnecessary.\n\n#DevOps #PlatformEngineering #FutureOfTech"
    }
]

class LinkedInPoster:
    """Handles posting content to LinkedIn company pages using the legacy UGCPosts API."""
    
    def __init__(self, access_token: str, organization_id: str):
        """
        Initialize the LinkedIn poster.
        
        Args:
            access_token: LinkedIn API access token
            organization_id: LinkedIn organization/company ID (numbers only)
        """
        self.access_token = access_token
        self.organization_id = organization_id
        # Use the legacy UGCPosts API endpoint
        self.api_url = "https://api.linkedin.com/v2/ugcPosts"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        logger.info(f"Using legacy UGCPosts API endpoint")
        logger.info(f"Using organization ID: {self.organization_id}")
    
    def create_post_data(self, post_content: str) -> Dict[str, Any]:
        """
        Create the post data structure for LinkedIn UGCPosts API.
        
        Args:
            post_content: The text content for the post
            
        Returns:
            Dictionary containing the formatted post data
        """
        # Format for the legacy UGCPosts API
        return {
            "author": f"urn:li:organization:{self.organization_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
    
    def post_to_linkedin(self, post_content: str) -> Dict[str, Any]:
        """
        Post content to LinkedIn using the legacy UGCPosts API.
        
        Args:
            post_content: The text content for the post
            
        Returns:
            Response data from LinkedIn API
            
        Raises:
            Exception: If the post fails
        """
        post_data = self.create_post_data(post_content)
        
        logger.info("Posting to LinkedIn...")
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=post_data
        )
        
        if response.status_code not in (200, 201):
            logger.error(f"Failed to post to LinkedIn: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"LinkedIn API error: {response.status_code}")
        
        response_data = response.json() if response.text else {}
        logger.info(f"Successfully posted to LinkedIn. Response: {response_data}")
        
        return response_data


def select_post() -> Dict[str, str]:
    """
    Select a post from the available templates.
    Uses current date to pick different posts on different days.
    
    Returns:
        Dictionary containing post title and content
    """
    today = datetime.now()
    # Use day of year to cycle through posts
    index = today.timetuple().tm_yday % len(DEVOPS_POSTS)
    return DEVOPS_POSTS[index]


def log_post_history(post: Dict[str, str]) -> None:
    """
    Log post history to a file for tracking.
    
    Args:
        post: Dictionary containing post title and content
    """
    try:
        history_dir = os.path.join(os.getcwd(), ".github", "post-history")
        os.makedirs(history_dir, exist_ok=True)
        
        history_file = os.path.join(history_dir, "linkedin-posts.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(history_file, "a") as f:
            f.write(f"{timestamp}: {post['title']}\n")
        
        logger.info(f"Post history logged to {history_file}")
    except Exception as e:
        logger.warning(f"Failed to log post history: {e}")


def main() -> None:
    """Main function to run the LinkedIn posting automation."""
    try:
        # Get environment variables
        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        organization_id = os.environ.get("LINKEDIN_ORGANIZATION_ID")
        
        if not access_token or not organization_id:
            logger.error("Missing required environment variables.")
            logger.error("Ensure LINKEDIN_ACCESS_TOKEN and LINKEDIN_ORGANIZATION_ID are set.")
            exit(1)
        
        # Make sure organization_id is just the ID number, not the full URN
        # Strip the "urn:li:organization:" prefix if it's included
        if organization_id.startswith("urn:li:organization:"):
            organization_id = organization_id.replace("urn:li:organization:", "")
        
        # Select post content
        post = select_post()
        logger.info(f"Selected post: {post['title']}")
        
        # Post to LinkedIn
        linkedin = LinkedInPoster(access_token, organization_id)
        response = linkedin.post_to_linkedin(post['content'])
        
        # Log post history
        log_post_history(post)
        
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write(f"post_title={post['title']}\n")
                f.write(f"post_status=success\n")
        
        logger.info("LinkedIn post automation completed successfully.")
    
    except Exception as e:
        logger.error(f"Error during LinkedIn post automation: {e}")
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write("post_status=failed\n")
        exit(1)


if __name__ == "__main__":
    main()
