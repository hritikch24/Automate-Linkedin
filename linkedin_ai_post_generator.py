#!/usr/bin/env python3
"""
LinkedIn DevOps Post Generator using Claude API
----------------------------------------------
This script dynamically generates DevOps content using Claude API and posts it to LinkedIn.
It's designed to be run via GitHub Actions on a schedule to maintain a consistent social media presence.

Required environment variables:
- LINKEDIN_ACCESS_TOKEN: Your LinkedIn API access token
- LINKEDIN_ORGANIZATION_ID: Your LinkedIn organization/company ID
- CLAUDE_API_KEY: Your Claude API key
"""

import os
import json
import random
import logging
import time
from datetime import datetime
import requests
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# DevOps topics for Claude to generate content about
DEVOPS_TOPICS = [
    {
        "title": "CI/CD Tool Comparison",
        "instructions": "Write a LinkedIn post comparing Jenkins, GitHub Actions, and CircleCI for DevOps. Include pros/cons of each, costs, and specific use cases where each excels. Mention AI integration possibilities. Include real commands or configs. Format with emojis and make it highly engaging. End by mentioning automatedevops.tech as a place to get more insights. Use appropriate hashtags."
    },
    {
        "title": "Kubernetes Cost Optimization",
        "instructions": "Write a LinkedIn post about Kubernetes cost optimization techniques. Include specific kubectl commands for resource analysis. Provide 3-4 concrete tips with potential savings percentages. Mention AI tools for predictive scaling. Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for more expertise. Include relevant hashtags."
    },
    {
        "title": "Container Security Best Practices",
        "instructions": "Write a LinkedIn post about container security best practices. Compare Docker, containerd, and cri-o security features. Include specific scanning and hardening tips with commands. Mention AI-powered security scanning benefits. Make it visually appealing with emojis and good formatting. End by mentioning automatedevops.tech for security consultations. Include relevant hashtags."
    },
    {
        "title": "Multi-Cloud Strategy",
        "instructions": "Write a LinkedIn post comparing AWS, Azure, and GCP for AI and DevOps workloads. Include unique strengths, pricing differences, and integration capabilities. Provide a specific cost-saving tip for multi-cloud. Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for multi-cloud strategy help. Include appropriate hashtags."
    },
    {
        "title": "Advanced Linux Commands",
        "instructions": "Write a LinkedIn post with 5 powerful Linux commands for DevOps engineers. For each command, include syntax and a specific use case. Focus on commands for troubleshooting, performance, or automation. Make it visually engaging with formatting and emojis. End by mentioning automatedevops.tech for more DevOps expertise. Include relevant hashtags."
    },
    {
        "title": "IaC Tools Comparison",
        "instructions": "Write a LinkedIn post comparing Terraform, Pulumi, and CloudFormation. Include code examples, learning curve comparisons, and specific strengths. Mention AI for infrastructure optimization. Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for IaC consulting. Include relevant hashtags."
    },
    {
        "title": "Database Performance",
        "instructions": "Write a LinkedIn post comparing self-hosted vs cloud database performance. Include PostgreSQL vs RDS vs Aurora with specific metrics on cost, performance, and maintenance needs. Include one SQL optimization tip. Mention AI for query optimization. Format with emojis for engagement. End by mentioning automatedevops.tech for database consulting. Include relevant hashtags."
    },
    {
        "title": "Monitoring and Observability",
        "instructions": "Write a LinkedIn post comparing Prometheus+Grafana, Datadog, and New Relic for monitoring. Include pros/cons, cost considerations, and integration efforts. Mention AI for anomaly detection. Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for monitoring setup help. Include relevant hashtags."
    },
    {
        "title": "Kubernetes Deployment Tools",
        "instructions": "Write a LinkedIn post comparing Helm vs Kustomize for Kubernetes deployments. Include specific benefits, code examples, and use cases for each. Mention AI for deployment optimization. Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for Kubernetes expertise. Include relevant hashtags."
    },
    {
        "title": "AI in DevOps",
        "instructions": "Write a LinkedIn post about 5 ways AI is revolutionizing DevOps. Include specific tools or techniques for each, with potential impact metrics (like time savings). Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for AI-enhanced DevOps services. Include relevant hashtags."
    },
    {
        "title": "Microservices Communication",
        "instructions": "Write a LinkedIn post comparing different microservices communication patterns: REST, gRPC, GraphQL, and event-driven. Include pros/cons and performance considerations for each. Mention AI for traffic optimization. Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for microservices architecture consulting. Include relevant hashtags."
    },
    {
        "title": "DevOps Productivity Tools",
        "instructions": "Write a LinkedIn post about 5 developer productivity tools for DevOps engineers. Include specific time-saving metrics, setup tips, and use cases. Mention AI assistants as one category. Make it visually engaging with emojis and formatting. End by mentioning automatedevops.tech for productivity consulting. Include relevant hashtags."
    }
]


class ClaudeContentGenerator:
    """Generates DevOps content using Claude API."""
    
    def __init__(self, api_key: str):
        """
        Initialize the Claude content generator.
        
        Args:
            api_key: Claude API key
        """
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
    def generate_content(self, topic: Dict[str, str]) -> str:
        """
        Generate post content using Claude API.
        
        Args:
            topic: Topic dictionary containing title and instructions
            
        Returns:
            Generated post content
            
        Raises:
            Exception: If content generation fails
        """
        logger.info(f"Generating content about: {topic['title']}")
        
        system_prompt = """
        You are a DevOps expert creating engaging LinkedIn posts. Your posts should:
        1. Be informative and provide genuine value with specific details and examples
        2. Include relevant emojis for visual appeal
        3. Format content for easy scanning (bullet points, comparisons)
        4. Include concrete metrics, commands, or code snippets where appropriate
        5. Maintain a professional but conversational tone
        6. Be 1200-1500 characters maximum (LinkedIn limit)
        7. End with subtle promotion of automatedevops.tech and relevant hashtags
        """
        
        try:
            payload = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": topic["instructions"]
                    }
                ]
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise Exception(f"Claude API error: {response.status_code}")
            
            response_data = response.json()
            generated_content = response_data["content"][0]["text"]
            
            # Ensure content isn't too long for LinkedIn
            if len(generated_content) > 3000:
                generated_content = generated_content[:2900] + "...\n\nLearn more at automatedevops.tech #DevOps #AI"
            
            logger.info(f"Successfully generated content ({len(generated_content)} chars)")
            return generated_content
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            # Fallback content in case of API failure
            return (
                f"🔧 DevOps Tip: {topic['title']} 🔧\n\n"
                "Looking for expert guidance on optimizing your DevOps processes?\n\n"
                "Visit automatedevops.tech for in-depth articles and professional services.\n\n"
                "#DevOps #Automation #CloudNative"
            )


class LinkedInPoster:
    """Handles posting content to LinkedIn company pages."""
    
    def __init__(self, access_token: str, organization_id: str):
        """
        Initialize the LinkedIn poster.
        
        Args:
            access_token: LinkedIn API access token
            organization_id: LinkedIn organization/company ID
        """
        self.access_token = access_token
        self.organization_id = organization_id
        self.api_url = "https://api.linkedin.com/v2/ugcPosts"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
    
    def create_post_data(self, post_content: str) -> Dict[str, Any]:
        """
        Create the post data structure required by LinkedIn API.
        
        Args:
            post_content: The text content for the post
            
        Returns:
            Dictionary containing the formatted post data
        """
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
        Post content to LinkedIn.
        
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
        
        response_data = response.json()
        logger.info(f"Successfully posted to LinkedIn. Post ID: {response_data.get('id', 'unknown')}")
        
        return response_data


def select_topic() -> Dict[str, str]:
    """
    Select a topic for content generation.
    Uses current date to pick different topics on different days.
    
    Returns:
        Dictionary containing topic title and instructions
    """
    today = datetime.now()
    # Use day of year to cycle through topics
    index = today.timetuple().tm_yday % len(DEVOPS_TOPICS)
    return DEVOPS_TOPICS[index]


def log_post_history(topic: Dict[str, str], content: str) -> None:
    """
    Log post history to a file for tracking.
    
    Args:
        topic: Dictionary containing topic title and instructions
        content: The generated post content
    """
    try:
        history_dir = os.path.join(os.getcwd(), ".github", "post-history")
        os.makedirs(history_dir, exist_ok=True)
        
        history_file = os.path.join(history_dir, "linkedin-posts.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(history_file, "a") as f:
            f.write(f"{timestamp}: {topic['title']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"{content[:200]}...\n\n")
        
        logger.info(f"Post history logged to {history_file}")
    except Exception as e:
        logger.warning(f"Failed to log post history: {e}")


def main() -> None:
    """Main function to run the LinkedIn posting automation."""
    try:
        # Get environment variables
        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        organization_id = os.environ.get("LINKEDIN_ORGANIZATION_ID")
        claude_api_key = os.environ.get("CLAUDE_API_KEY")
        
        if not access_token or not organization_id or not claude_api_key:
            logger.error("Missing required environment variables.")
            logger.error("Ensure LINKEDIN_ACCESS_TOKEN, LINKEDIN_ORGANIZATION_ID, and CLAUDE_API_KEY are set.")
            exit(1)
        
        # Select topic
        topic = select_topic()
        logger.info(f"Selected topic: {topic['title']}")
        
        # Generate content using Claude
        claude = ClaudeContentGenerator(claude_api_key)
        content = claude.generate_content(topic)
        
        # Post to LinkedIn
        linkedin = LinkedInPoster(access_token, organization_id)
        response = linkedin.post_to_linkedin(content)
        
        # Log post history
        log_post_history(topic, content)
        
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write(f"post_title={topic['title']}\n")
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