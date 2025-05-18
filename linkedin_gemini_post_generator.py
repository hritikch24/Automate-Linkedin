#!/usr/bin/env python3
"""
LinkedIn DevOps Post Automation with Gemini AI Content Generation
---------------------------------------------------------------
This script automatically generates DevOps content using Gemini AI and posts it to LinkedIn.
It tries several fallback methods to ensure successful posting.

Required environment variables:
- LINKEDIN_ACCESS_TOKEN: Your LinkedIn API access token
- LINKEDIN_ORGANIZATION_ID: Your LinkedIn organization/company ID
- GEMINI_API_KEY: Your Gemini API key
"""

import os
import json
import random
import logging
from datetime import datetime
import requests
import time
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# DevOps topics with the latest trends and technologies
DEVOPS_TOPICS = [
    {
        "title": "Kubernetes In-Place Pod Scaling",
        "prompt": "Write an engaging, professional LinkedIn post about Kubernetes' new in-place pod scaling feature. Include details on how it improves resource utilization compared to the old approach. Mention performance metrics, real-world benefits, and implementation tips. Use emojis and ensure good formatting with bullet points. Include hashtags related to Kubernetes, DevOps, and cloud native technologies. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and cutting-edge. Keep the post informative yet attention-grabbing with a slightly controversial angle."
    },
    {
        "title": "AI-Powered Observability",
        "prompt": "Write an engaging, professional LinkedIn post about how AI is revolutionizing observability in DevOps. Include specific examples of tools that use AI to detect anomalies, predict failures, and automate root cause analysis. Mention metrics on how AI-powered observability has reduced MTTR (Mean Time to Resolution) and prevented outages. Use emojis and ensure good formatting with bullet points. Include hashtags related to AI, DevOps, and observability. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and cutting-edge."
    },
    {
        "title": "eBPF for Kubernetes Security",
        "prompt": "Write an engaging, professional LinkedIn post about using eBPF for Kubernetes security. Explain how eBPF provides deeper visibility and control compared to traditional security approaches. Include specific examples of security threats it can detect and prevent. Mention real-world performance impact and implementation challenges. Use emojis and ensure good formatting with bullet points. Include relevant hashtags related to Kubernetes, security, and eBPF. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and cutting-edge."
    },
    {
        "title": "GitOps vs Platform Engineering",
        "prompt": "Write an engaging, provocative LinkedIn post comparing GitOps and Platform Engineering approaches. Discuss where each shines and falls short. Include specific metrics on adoption, resource requirements, and organizational impact. Mention how these approaches affect developer productivity and business outcomes. Use emojis and ensure good formatting with bullet points. Include hashtags related to GitOps, Platform Engineering, and DevOps. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable with a slightly controversial angle."
    },
    {
        "title": "Cost Optimization in Multi-Cloud",
        "prompt": "Write an engaging, professional LinkedIn post about cost optimization strategies for multi-cloud environments. Include specific techniques like spot instance automation, idle resource detection, and right-sizing. Mention real savings percentages achieved by implementing these methods. Compare the cost structures of AWS, Azure, and GCP for similar workloads. Use emojis and ensure good formatting with bullet points. Include hashtags related to cloud computing, FinOps, and cost optimization. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and include surprising statistics."
    },
    {
        "title": "DevSecOps Pipeline Automation",
        "prompt": "Write an engaging, professional LinkedIn post about automating security in DevOps pipelines. Include specific tools for SAST, DAST, SCA, and CSPM that can be integrated. Mention metrics on how automated security has caught vulnerabilities before production and reduced security debt. Discuss the shift-left approach and its benefits. Use emojis and ensure good formatting with bullet points. Include hashtags related to DevSecOps, security automation, and compliance. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and cutting-edge."
    },
    {
        "title": "Infrastructure as Code Testing",
        "prompt": "Write an engaging, professional LinkedIn post about testing Infrastructure as Code. Compare tools like Terratest, Open Policy Agent, and Checkov. Include code examples for common testing patterns. Mention metrics on how IaC testing has prevented outages and security incidents. Discuss testing in CI/CD pipelines. Use emojis and ensure good formatting with bullet points. Include hashtags related to IaC, testing, and DevOps. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and include surprising insights."
    },
    {
        "title": "Serverless vs Kubernetes",
        "prompt": "Write an engaging, provocative LinkedIn post comparing Serverless and Kubernetes approaches. Highlight the pros and cons of each in terms of operations overhead, scalability, cost, and developer experience. Include specific real-world scenarios where each approach excels. Mention performance metrics and cost comparisons. Use emojis and ensure good formatting with bullet points. Include hashtags related to Serverless, Kubernetes, and cloud architecture. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable with a slightly controversial angle."
    },
    {
        "title": "AI-Assisted Incident Response",
        "prompt": "Write an engaging, professional LinkedIn post about using AI for incident response in operations. Include specific examples of how LLMs can help diagnose issues, suggest remediations, and automate runbooks. Mention metrics on MTTR reduction and case studies from major companies. Discuss the future of autonomous operations. Use emojis and ensure good formatting with bullet points. Include hashtags related to AI, AIOps, and incident management. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and cutting-edge."
    },
    {
        "title": "Service Mesh Evolution",
        "prompt": "Write an engaging, professional LinkedIn post about the evolution of service mesh technologies. Compare Istio, Linkerd, and Cilium Service Mesh. Discuss performance improvements, simplified operations, and new capabilities in recent releases. Include metrics on latency impact and resource consumption. Mention when to use and when to avoid service mesh. Use emojis and ensure good formatting with bullet points. Include hashtags related to service mesh, microservices, and Kubernetes. Include a call to action directing people to automatedevops.tech. Make it sound knowledgeable and include surprising insights."
    }
]


class GeminiContentGenerator:
    """Generates DevOps content using Gemini AI."""
    
    def __init__(self, api_key: str):
        """
        Initialize the Gemini content generator.
        
        Args:
            api_key: Gemini API key
        """
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    def generate_content(self, topic: Dict[str, str]) -> str:
        """
        Generate post content using Gemini API.
        
        Args:
            topic: Topic dictionary containing title and prompt
            
        Returns:
            Generated post content
            
        Raises:
            Exception: If content generation fails
        """
        logger.info(f"Generating content about: {topic['title']}")
        
        url = f"{self.api_url}?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": topic["prompt"]
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 800
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise Exception(f"Gemini API error: {response.status_code}")
            
            response_data = response.json()
            
            # Extract the generated text from the response
            generated_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Ensure content isn't too long for LinkedIn
            if len(generated_text) > 3000:
                generated_text = generated_text[:2900] + "...\n\nLearn more at automatedevops.tech #DevOps #AI"
            
            logger.info(f"Successfully generated content ({len(generated_text)} chars)")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            # Fallback content in case of API failure
            return (
                f"🔧 DevOps Insight: {topic['title']} 🔧\n\n"
                "Looking for expert guidance on optimizing your DevOps processes?\n\n"
                "Visit automatedevops.tech for in-depth articles and professional services.\n\n"
                "#DevOps #Automation #CloudNative"
            )


class LinkedInHelper:
    """Helper class for LinkedIn API operations."""
    
    def __init__(self, access_token: str):
        """
        Initialize the LinkedIn helper.
        
        Args:
            access_token: LinkedIn API access token
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        Retrieve the user's LinkedIn profile.
        
        Returns:
            User profile data
        """
        logger.info("Retrieving user profile...")
        url = "https://api.linkedin.com/v2/me"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to retrieve user profile: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"LinkedIn API error: {response.status_code}")
        
        profile_data = response.json()
        logger.info(f"Successfully retrieved user profile. ID: {profile_data.get('id')}")
        return profile_data
    
    def get_organization_access(self, organization_id: str) -> Dict[str, Any]:
        """
        Check if the user has access to the organization.
        
        Args:
            organization_id: LinkedIn organization ID
            
        Returns:
            Organization access data
        """
        logger.info(f"Checking organization access for org ID: {organization_id}...")
        url = f"https://api.linkedin.com/v2/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&projection=(elements*(roleAssignee~(localizedFirstName,localizedLastName),state,role,organization~(localizedName)))"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to check organization access: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"LinkedIn API error: {response.status_code}")
        
        access_data = response.json()
        logger.info(f"Successfully retrieved organization access data.")
        return access_data
    
    def post_as_person(self, person_id: str, content: str) -> Dict[str, Any]:
        """
        Post content as a person.
        
        Args:
            person_id: LinkedIn person ID
            content: Post content
            
        Returns:
            Response data
        """
        logger.info(f"Posting as person {person_id}...")
        url = "https://api.linkedin.com/v2/ugcPosts"
        
        post_data = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        logger.info(f"Post data: {json.dumps(post_data, indent=2)}")
        response = requests.post(url, headers=self.headers, json=post_data)
        
        if response.status_code not in (200, 201):
            logger.error(f"Failed to post as person: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"LinkedIn API error: {response.status_code}")
        
        response_data = response.json() if response.text else {}
        logger.info(f"Successfully posted as person.")
        return response_data
    
    def post_as_organization(self, person_id: str, organization_id: str, content: str) -> Dict[str, Any]:
        """
        Post content as an organization.
        
        Args:
            person_id: LinkedIn person ID
            organization_id: LinkedIn organization ID
            content: Post content
            
        Returns:
            Response data
        """
        logger.info(f"Posting as organization {organization_id} with person {person_id}...")
        url = "https://api.linkedin.com/v2/ugcPosts"
        
        # First try the standard format
        post_data = {
            "author": f"urn:li:organization:{organization_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        logger.info(f"Post data: {json.dumps(post_data, indent=2)}")
        
        # Try several attempts with different headers to see what works
        logger.info("First attempt: Standard headers...")
        response = requests.post(url, headers=self.headers, json=post_data)
        
        if response.status_code in (200, 201):
            response_data = response.json() if response.text else {}
            logger.info(f"Successfully posted as organization on first attempt.")
            return response_data
        else:
            logger.warning(f"First attempt failed: {response.status_code}")
            logger.warning(f"Response: {response.text}")
            
            # Try legacy Shares API
            logger.info("Second attempt: Using Shares API...")
            shares_url = "https://api.linkedin.com/v2/shares"
            shares_data = {
                "owner": f"urn:li:organization:{organization_id}",
                "content": {
                    "contentEntities": [
                        {
                            "entityLocation": "https://automatedevops.tech",
                            "thumbnails": [
                                {
                                    "resolvedUrl": "https://automatedevops.tech/logo.jpg"
                                }
                            ]
                        }
                    ],
                    "title": "DevOps Insights",
                    "description": "Latest DevOps trends and best practices"
                },
                "text": {
                    "text": content[:1000]  # Limit text to 1000 chars for Shares API
                },
                "distribution": {
                    "linkedInDistributionTarget": {}
                }
            }
            
            shares_response = requests.post(shares_url, headers=self.headers, json=shares_data)
            
            if shares_response.status_code in (200, 201):
                shares_data = shares_response.json() if shares_response.text else {}
                logger.info(f"Successfully posted as organization using Shares API.")
                return shares_data
            else:
                logger.warning(f"Second attempt failed: {shares_response.status_code}")
                logger.warning(f"Response: {shares_response.text}")
                
                # If all attempts failed, raise exception
                logger.error("All attempts to post as organization failed.")
                raise Exception("Failed to post as organization after multiple attempts")


def select_topic() -> Dict[str, str]:
    """
    Select a topic for content generation.
    Uses current date to pick different topics on different days.
    
    Returns:
        Dictionary containing topic title and prompt
    """
    today = datetime.now()
    # Use day of year to cycle through topics
    index = today.timetuple().tm_yday % len(DEVOPS_TOPICS)
    return DEVOPS_TOPICS[index]


def log_post_history(topic: Dict[str, str], content: str) -> None:
    """
    Log post history to a file for tracking.
    
    Args:
        topic: Dictionary containing topic title and prompt
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
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        if not access_token or not organization_id or not gemini_api_key:
            logger.error("Missing required environment variables.")
            logger.error("Ensure LINKEDIN_ACCESS_TOKEN, LINKEDIN_ORGANIZATION_ID, and GEMINI_API_KEY are set.")
            exit(1)
        
        # Make sure organization_id is just the ID number, not the full URN
        # Strip the "urn:li:organization:" prefix if it's included
        if organization_id.startswith("urn:li:organization:"):
            organization_id = organization_id.replace("urn:li:organization:", "")
        
        # Select topic for content generation
        topic = select_topic()
        logger.info(f"Selected topic: {topic['title']}")
        
        # Generate content using Gemini
        gemini = GeminiContentGenerator(gemini_api_key)
        content = gemini.generate_content(topic)
        
        # Initialize LinkedIn helper
        linkedin = LinkedInHelper(access_token)
        
        # Get user profile
        profile = linkedin.get_user_profile()
        person_id = profile.get('id')
        
        if not person_id:
            logger.error("Failed to retrieve person ID from profile.")
            exit(1)
        
        # Try to post as the organization
        try:
            logger.info("Attempting to post as organization...")
            linkedin.post_as_organization(person_id, organization_id, content)
            logger.info("Successfully posted as organization!")
        except Exception as e:
            logger.warning(f"Failed to post as organization: {e}")
            logger.info("Falling back to posting as personal profile...")
            
            # If posting as organization fails, fall back to posting as person
            linkedin.post_as_person(person_id, content)
            logger.info("Successfully posted as personal profile!")
        
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
