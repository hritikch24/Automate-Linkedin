#!/usr/bin/env python3
"""
LinkedIn DevOps Post Automation with Gemini AI Content Generation
---------------------------------------------------------------
This script automatically generates unique DevOps content using Gemini AI and posts it to LinkedIn.
It checks for similarity with previous posts to avoid repetition.

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
import re
import string
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# High-level tech topic categories to provide variety
TECH_CATEGORIES = [
    "DevOps", "Cloud Native", "Kubernetes", "CI/CD", "Security", 
    "Monitoring", "Infrastructure", "Automation", "Platform Engineering",
    "AWS", "Azure", "GCP", "Containers", "Microservices"
]

# Meta-prompts for Gemini to generate unique content
META_PROMPTS = [
    "Generate a unique, engaging LinkedIn post about {topic} with the latest trends, best practices, and controversial opinions. Include specific tools, metrics, and real-world examples. Format with emojis and bullet points. Include hashtags and a call to action for comments or connections. Make it 10-16 lines long and professional but attention-grabbing.",
    
    "Create a thought-provoking LinkedIn post comparing different approaches to {topic}. Highlight pros, cons, and specific use cases for each approach. Include surprising statistics and industry trends. Format with emojis and bullet points. Include relevant hashtags and ask readers to share their experiences. Make it 10-16 lines long and informative yet engaging.",
    
    "Write a technical LinkedIn post about solving common challenges in {topic}. Include specific tools, techniques, and code examples where relevant. Mention performance improvements and reliability gains. Format with emojis and bullet points. Add relevant hashtags and invite readers to discuss their own solutions. Make it 10-16 lines long and technically substantial but accessible.",
    
    "Craft a forward-looking LinkedIn post about the future of {topic} in the next 2-3 years. Discuss emerging trends, tools, and practices that will become mainstream. Include specific predictions with reasoning. Format with emojis and bullet points. Use relevant hashtags and ask readers what they think about these predictions. Make it 10-16 lines long and thought-provoking.",
    
    "Write a LinkedIn post highlighting common mistakes and misconceptions about {topic}. Explain the correct approaches and why they matter. Include real-world consequences of these mistakes. Format with emojis and bullet points. Add relevant hashtags and invite readers to share mistakes they've encountered. Make it 10-16 lines long and educational yet engaging."
]


class PostHistoryManager:
    """Manages post history to check for and avoid duplicate content."""
    
    def __init__(self, history_file_path: str = None):
        """
        Initialize the post history manager.
        
        Args:
            history_file_path: Path to the post history file
        """
        if history_file_path:
            self.history_file = history_file_path
        else:
            # Default path
            history_dir = os.path.join(os.getcwd(), ".github", "post-history")
            os.makedirs(history_dir, exist_ok=True)
            self.history_file = os.path.join(history_dir, "linkedin-posts.log")
        
        self.post_history = self._load_history()
    
    def _load_history(self) -> List[str]:
        """
        Load post history from file.
        
        Returns:
            List of previous post contents
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    content = f.read()
                    # Extract content sections from the log
                    posts = []
                    sections = content.split("----------------------------------------")
                    for section in sections:
                        if section.strip():
                            # Extract the post content after any timestamp and title
                            lines = section.strip().split("\n")
                            if len(lines) > 2:  # Skip the timestamp and title
                                post_content = "\n".join(lines[2:])
                                posts.append(post_content)
                    return posts
            return []
        except Exception as e:
            logger.warning(f"Failed to load post history: {e}")
            return []
    
    def is_similar_to_previous(self, content: str, threshold: float = 0.7) -> bool:
        """
        Check if the new content is too similar to any previous posts.
        
        Args:
            content: The new post content
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if content is similar to a previous post, False otherwise
        """
        # Normalize content for comparison (lowercase, remove punctuation, excess whitespace)
        def normalize(text):
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        normalized_content = normalize(content)
        
        for previous_post in self.post_history:
            normalized_previous = normalize(previous_post)
            
            # Use sequence matcher to determine similarity ratio
            similarity = SequenceMatcher(None, normalized_content, normalized_previous).ratio()
            if similarity > threshold:
                logger.info(f"Content is too similar to a previous post (similarity: {similarity:.2f})")
                return True
        
        return False
    
    def add_post(self, title: str, content: str) -> None:
        """
        Add a new post to the history.
        
        Args:
            title: Post title
            content: Post content
        """
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.history_file, 'a') as f:
                f.write(f"{timestamp}: {title}\n")
                f.write("-" * 40 + "\n")
                f.write(f"{content}\n\n")
            
            # Update the in-memory history
            self.post_history.append(content)
            logger.info(f"Post added to history: {title}")
        except Exception as e:
            logger.warning(f"Failed to add post to history: {e}")


class GeminiContentGenerator:
    """Generates unique DevOps content using Gemini AI."""
    
    def __init__(self, api_key: str, history_manager: PostHistoryManager):
        """
        Initialize the Gemini content generator.
        
        Args:
            api_key: Gemini API key
            history_manager: Post history manager for checking similarity
        """
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.history_manager = history_manager
    
    def generate_topic(self) -> str:
        """
        Generate a specific topic related to DevOps or cloud.
        
        Returns:
            Generated topic
        """
        # Use Gemini to generate a specific topic
        url = f"{self.api_url}?key={self.api_key}"
        
        # Generate a random seed for variation
        random_seed = random.randint(1, 10000)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Choose a random technology category as a starting point
        category = random.choice(TECH_CATEGORIES)
        
        prompt = f"""Generate a specific, technical topic related to {category} that would make a good LinkedIn post. 
        
        The topic should be specific (not general like just "Kubernetes" but rather something like "Kubernetes HPA vs. KEDA for autoscaling").
        
        It should be about something current and relevant in the tech industry.
        
        DO NOT include any explanations, just return the topic as a short title (5-10 words).
        
        Random seed: {random_seed}
        Timestamp: {timestamp}
        """
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.9,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 50
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                # Fall back to a random composed topic
                return self._fallback_topic_generation()
            
            response_data = response.json()
            topic = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Clean up the topic
            topic = topic.replace("\"", "").replace("'", "")
            if ":" in topic:
                topic = topic.split(":", 1)[1].strip()
            
            logger.info(f"Generated topic: {topic}")
            return topic
            
        except Exception as e:
            logger.error(f"Error generating topic: {e}")
            return self._fallback_topic_generation()
    
    def _fallback_topic_generation(self) -> str:
        """
        Generate a fallback topic if the API call fails.
        
        Returns:
            Generated topic
        """
        templates = [
            "{tech} Best Practices for Enterprise Adoption",
            "Optimizing {tech} Performance in Production",
            "Securing {tech} Deployments in 2025",
            "{tech} vs {alt_tech}: Which to Choose When",
            "The Future of {tech} in Modern DevOps",
            "Common {tech} Mistakes and How to Avoid Them",
            "Scaling {tech} for High-Traffic Applications",
            "Monitoring and Observability for {tech}",
            "Automating {tech} Deployments with {ci_tool}",
            "Cost Optimization Strategies for {tech}"
        ]
        
        techs = [
            "Kubernetes", "Docker", "Terraform", "AWS Lambda", "Azure AKS", 
            "GCP GKE", "GitOps", "Istio", "Prometheus", "Grafana", 
            "ArgoCD", "Jenkins", "GitHub Actions", "CircleCI", "CloudWatch",
            "EKS", "Ansible", "Chef", "Puppet", "Datadog"
        ]
        
        alt_techs = [
            "Nomad", "Podman", "Pulumi", "Azure Functions", "EKS", 
            "AKS", "Platform Engineering", "Linkerd", "Datadog", "New Relic",
            "Flux", "TeamCity", "GitLab CI", "Harness", "Nagios"
        ]
        
        ci_tools = [
            "GitHub Actions", "Jenkins", "CircleCI", "GitLab CI", "TeamCity",
            "Bamboo", "Travis CI", "Drone CI", "Concourse", "GoCD"
        ]
        
        template = random.choice(templates)
        tech = random.choice(techs)
        
        if "{alt_tech}" in template:
            # Ensure alt_tech is different from tech
            alt_tech = random.choice([t for t in alt_techs if t != tech])
            topic = template.format(tech=tech, alt_tech=alt_tech)
        elif "{ci_tool}" in template:
            ci_tool = random.choice(ci_tools)
            topic = template.format(tech=tech, ci_tool=ci_tool)
        else:
            topic = template.format(tech=tech)
        
        logger.info(f"Generated fallback topic: {topic}")
        return topic
    
    def generate_post_content(self, topic: str, max_attempts: int = 3) -> Dict[str, str]:
        """
        Generate unique post content that isn't too similar to previous posts.
        
        Args:
            topic: The topic to generate content about
            max_attempts: Maximum number of generation attempts
            
        Returns:
            Dictionary with title and content
            
        Raises:
            Exception: If unable to generate unique content after max_attempts
        """
        logger.info(f"Generating content about: {topic}")
        
        for attempt in range(max_attempts):
            logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
            
            # Generate content
            content = self._generate_single_content(topic)
            
            # Check if content is similar to previous posts
            if not self.history_manager.is_similar_to_previous(content):
                return {
                    "title": topic,
                    "content": content
                }
            
            logger.info(f"Generated content too similar to previous post, trying again...")
        
        # If we couldn't generate unique content after max_attempts, create a more random one
        logger.warning(f"Could not generate unique content after {max_attempts} attempts, using higher randomization")
        content = self._generate_single_content(topic, temperature=1.0)
        
        return {
            "title": topic,
            "content": content
        }
    
    def _generate_single_content(self, topic: str, temperature: float = 0.9) -> str:
        """
        Generate a single post content using Gemini API.
        
        Args:
            topic: The topic to generate content about
            temperature: Randomness parameter (0-1)
            
        Returns:
            Generated content
            
        Raises:
            Exception: If content generation fails
        """
        url = f"{self.api_url}?key={self.api_key}"
        
        # Add randomization to ensure unique content
        random_seed = random.randint(1, 10000)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Choose a random meta-prompt for more variation
        meta_prompt = random.choice(META_PROMPTS)
        prompt = meta_prompt.format(topic=topic)
        
        # Add uniqueness instructions
        prompt += f"\n\nMake this post absolutely unique and different from standard posts on this topic. Add a fresh perspective or unconventional insights. Random seed: {random_seed}. Timestamp: {timestamp}."
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
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
                generated_text = generated_text[:2900] + "...\n\nWhat's your experience with this? Share in the comments! #DevOps #TechTrends"
            
            logger.info(f"Successfully generated content ({len(generated_text)} chars)")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            # Generate a fallback content
            return self._generate_fallback_content(topic)
    
    def _generate_fallback_content(self, topic: str) -> str:
        """
        Generate fallback content in case of API failure.
        
        Args:
            topic: The topic to generate content about
            
        Returns:
            Fallback content
        """
        # Random facts/points about DevOps and tech topics
        random_points = [
            f"{topic} has seen a dramatic evolution in recent years",
            f"Most organizations struggle with implementing {topic} effectively",
            f"The ROI of proper {topic} implementation can exceed 300%",
            f"Industry leaders in {topic} report 60% faster time-to-market",
            f"Common misconceptions about {topic} lead to implementation failures",
            f"Best practices for {topic} include automated testing and continuous feedback",
            f"The future of {topic} will likely include more AI integration",
            f"Security considerations for {topic} are often overlooked",
            f"Proper monitoring is essential for successful {topic} projects",
            f"Team structure greatly impacts {topic} effectiveness",
            f"Training and culture are as important as tools for {topic}",
            f"Cost optimization is a key benefit of mature {topic} implementations",
            f"Open source tools have revolutionized how we approach {topic}",
            f"Enterprise adoption of {topic} has increased 85% in the past year",
            f"Hybrid approaches often yield the best results for {topic}",
            f"The biggest challenge with {topic} is often organizational, not technical",
            f"Successful {topic} requires executive sponsorship and cultural alignment",
            f"Small wins can build momentum for larger {topic} transformations",
            f"Metrics and measurement are critical for {topic} success",
            f"The talent gap in {topic} continues to challenge organizations"
        ]
        
        # Create a unique combination of points
        random.shuffle(random_points)
        selected_points = random_points[:random.randint(6, 8)]
        
        # Generate random hashtags
        hashtags = [
            "#DevOps", "#CloudNative", "#TechTrends", "#Innovation", 
            "#Engineering", "#SoftwareDevelopment", "#Automation",
            "#Kubernetes", "#Cloud", "#CI/CD", "#Infrastructure", 
            "#Microservices", "#DevSecOps", "#SRE", "#Technology"
        ]
        random.shuffle(hashtags)
        selected_hashtags = hashtags[:5]
        hashtag_str = " ".join(selected_hashtags)
        
        # Create a topic-specific hashtag
        topic_hashtag = "#" + "".join(word.capitalize() for word in topic.split())
        
        return (
            f"🚀 Thoughts on {topic} 🚀\n\n"
            f"I've been thinking about {topic} lately and wanted to share some insights:\n\n"
            + "\n".join(f"• {point}" for point in selected_points) + 
            f"\n\nWhat has been your experience with {topic}? What challenges have you faced?\n\n"
            f"I'd love to hear your thoughts in the comments below!\n\n"
            f"{hashtag_str} {topic_hashtag}"
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
        
        # Initialize post history manager
        history_manager = PostHistoryManager()
        
        # Initialize content generator
        gemini = GeminiContentGenerator(gemini_api_key, history_manager)
        
        # Generate a new topic
        topic = gemini.generate_topic()
        
        # Generate post content
        post = gemini.generate_post_content(topic)
        
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
            linkedin.post_as_organization(person_id, organization_id, post["content"])
            logger.info("Successfully posted as organization!")
        except Exception as e:
            logger.warning(f"Failed to post as organization: {e}")
            logger.info("Falling back to posting as personal profile...")
            
            # If posting as organization fails, fall back to posting as person
            linkedin.post_as_person(person_id, post["content"])
            logger.info("Successfully posted as personal profile!")
        
        # Log post history
        history_manager.add_post(post["title"], post["content"])
        
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