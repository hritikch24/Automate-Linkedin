#!/usr/bin/env python3
"""
LinkedIn K8s Platform Validation Post Generator
----------------------------------------------
Generates and publishes validation-focused LinkedIn posts about Kubernetes platform ideas.
Uses the exact same structure and flow as the working DevOps automation.

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

# K8s validation topics - using same structure as your working code
K8S_VALIDATION_TOPICS = [
    "K8s Observability Tool Sprawl",
    "Kubernetes Cost Visibility Challenges", 
    "K8s Troubleshooting Complexity",
    "Kubernetes Monitoring Fragmentation",
    "K8s Cost Optimization Pain Points",
    "Kubernetes Log Management Issues",
    "K8s Metrics Correlation Problems",
    "Kubernetes AI-Powered Debugging",
    "K8s Resource Right-Sizing Challenges",
    "Kubernetes Spot Instance Management"
]

# Validation post templates - using same meta-prompt structure as your working code
VALIDATION_META_PROMPTS = [
    """Generate a unique, engaging LinkedIn post asking for community feedback about {topic}. Focus on identifying pain points and validating problems rather than selling solutions.

    IMPORTANT: Structure it as a genuine question to the DevOps community:
    - Start with a relatable problem statement
    - Present a potential solution vision (without claiming you're building it)
    - Ask specific questions about their current experience
    - End with engagement hooks asking for their input

    Format with emojis and bullet points. Include hashtags. Make it 15-20 lines long and community-focused.""",

    """Create a validation-focused LinkedIn post about challenges with {topic}. Present yourself as someone exploring this problem space and genuinely seeking community input.

    IMPORTANT: Include elements like:
    - "Been thinking about this pain point..."
    - "What if there was a platform that..."
    - "What's your experience with..."
    - "Would this solve real problems for your team?"

    Format with emojis and bullet points. Include relevant hashtags. Make it 15-20 lines long and authentic.""",

    """Write a LinkedIn post seeking community feedback on {topic}. Focus on problem validation and feature prioritization rather than product promotion.

    IMPORTANT: Ask specific questions like:
    - "Are you frustrated with current solutions?"
    - "What features would be must-haves?"
    - "How are you solving this today?"
    - "What would make the biggest impact?"

    Format with emojis and bullet points. Make it 15-20 lines long and genuinely curious."""
]

# Same engagement elements as your working code
ENGAGEMENT_HOOKS = [
    "💬 What's your experience with this? Drop a comment!",
    "🔥 Tag someone who needs to see this discussion!",
    "💡 Have a different approach? I'd love to hear it!",
    "🚀 What challenges are you facing with this?",
    "⚡ Agree or disagree? Let's discuss in the comments!",
    "🎯 What's your biggest pain point here? Share below!",
    "🛠️ Which tools have worked best for you?",
    "📈 What results have you seen with different approaches?",
    "🤔 What would you add to this list?",
    "💪 Ready to solve this together? Let's connect!"
]

# Validation-focused CTAs
VALIDATION_CTAS = [
    "🔍 Genuinely curious about your experiences - please share!",
    "💭 Would love to hear how you're tackling this challenge!",
    "🤝 Building solutions starts with understanding problems - help me learn!",
    "📊 Your insights would be incredibly valuable for the community!",
    "🎯 What am I missing from this analysis? Set me straight!",
    "💡 Crowdsourcing wisdom from the best DevOps minds - that's you!",
    "🚀 Together we can figure out better approaches to this!",
    "⭐ The community's experience is worth more than any survey!",
    "🔧 Real-world insights beat theoretical solutions every time!",
    "🌟 DevOps folks have the best war stories - share yours!"
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
                logger.info("LinkedIn validation post automation completed successfully.")
    
    except Exception as e:
        logger.error(f"Error during LinkedIn post automation: {e}")
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write("post_status=failed\n")
        exit(1)


if __name__ == "__main__":
    main()(f"Content is too similar to a previous post (similarity: {similarity:.2f})")
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

class GeminiValidationGenerator:
    """Generates validation-focused K8s platform posts using Gemini AI - same structure as working code."""
    
    def __init__(self, api_key: str, history_manager: PostHistoryManager):
        """
        Initialize the Gemini validation generator.
        
        Args:
            api_key: Gemini API key
            history_manager: Post history manager for checking similarity
        """
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.history_manager = history_manager
    
    def generate_topic(self) -> str:
        """
        Generate a specific K8s validation topic.
        
        Returns:
            Generated topic
        """
        # Use Gemini to generate a specific topic - same logic as working code
        url = f"{self.api_url}?key={self.api_key}"
        
        # Generate a random seed for variation
        random_seed = random.randint(1, 10000)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Choose a random K8s validation topic as starting point
        base_topic = random.choice(K8S_VALIDATION_TOPICS)
        
        prompt = f"""Generate a specific, technical topic related to "{base_topic}" that would make a good LinkedIn validation post. 
        
        The topic should be specific and focused on community feedback gathering about Kubernetes platform challenges.
        
        It should be about real problems DevOps engineers face that could generate discussion and validation.
        
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
                # Fall back to a random topic
                return random.choice(K8S_VALIDATION_TOPICS)
            
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
            return random.choice(K8S_VALIDATION_TOPICS)
    
    def _enhance_content_with_validation_elements(self, content: str, topic: str) -> str:
        """
        Enhance content with validation-focused engagement elements.
        
        Args:
            content: Original content
            topic: Post topic
            
        Returns:
            Enhanced content with validation elements
        """
        enhanced_content = content.strip()
        
        # Add validation-focused engagement
        hook = random.choice(ENGAGEMENT_HOOKS)
        validation_cta = random.choice(VALIDATION_CTAS)
        enhanced_content += f"\n\n{hook}\n{validation_cta}"
        
        # Add trending hashtags for better reach - same as working code
        validation_hashtags = [
            "#DevOps", "#Kubernetes", "#CloudNative", "#Observability", "#TechTrends", 
            "#SRE", "#Monitoring", "#CostOptimization", "#Innovation", "#TechLeadership",
            "#Engineering", "#SoftwareDevelopment", "#Automation", "#DigitalTransformation",
            "#Cloud", "#Infrastructure", "#Microservices", "#DevSecOps", "#Technology",
            "#CloudComputing", "#ArtificialIntelligence", "#OpenSource", "#ProductValidation"
        ]
        
        # Select 8-12 hashtags for maximum reach
        selected_hashtags = random.sample(validation_hashtags, random.randint(8, 12))
        hashtag_string = " ".join(selected_hashtags)
        
        # Add topic-specific hashtag
        topic_words = re.findall(r'\b\w+\b', topic)
        if topic_words:
            topic_hashtag = "#" + "".join(word.capitalize() for word in topic_words[:3])
            hashtag_string = f"{topic_hashtag} {hashtag_string}"
        
        enhanced_content += f"\n\n{hashtag_string}"
        
        return enhanced_content
    
    def generate_and_verify_post(self, topic: str, max_attempts: int = 5) -> Dict[str, str]:
        """
        Generate a validation post and verify its quality - same structure as working code.
        
        Args:
            topic: The topic to generate content about
            max_attempts: Maximum number of generation attempts
            
        Returns:
            Dictionary with title and content
        """
        logger.info(f"Generating and verifying validation content about: {topic}")
        
        for attempt in range(max_attempts):
            logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
            
            # Generate content
            content = self._generate_single_content(topic)
            
            # Enhance with validation elements
            enhanced_content = self._enhance_content_with_validation_elements(content, topic)
            
            # Check if content is similar to previous posts
            if self.history_manager.is_similar_to_previous(enhanced_content):
                logger.info(f"Generated content too similar to previous post, trying again...")
                continue
            
            # Simple quality check - validation posts should ask questions
            if "?" in enhanced_content and ("experience" in enhanced_content.lower() or "challenge" in enhanced_content.lower()):
                logger.info(f"Post passed validation quality check")
                return {
                    "title": topic,
                    "content": enhanced_content,
                    "review": "Validation post with community engagement focus"
                }
            else:
                logger.info(f"Post lacks validation elements, trying again...")
        
        # If we couldn't generate good quality content after max_attempts, use fallback
        logger.warning(f"Could not generate good validation content after {max_attempts} attempts, using fallback")
        content = self._generate_fallback_content(topic)
        enhanced_content = self._enhance_content_with_validation_elements(content, topic)
        
        return {
            "title": topic,
            "content": enhanced_content,
            "review": "Fallback validation post"
        }
    
    def _generate_single_content(self, topic: str, temperature: float = 0.9) -> str:
        """
        Generate a single validation post content using Gemini API.
        
        Args:
            topic: The topic to generate content about
            temperature: Randomness parameter (0-1)
            
        Returns:
            Generated content
        """
        url = f"{self.api_url}?key={self.api_key}"
        
        # Add randomization to ensure unique content
        random_seed = random.randint(1, 10000)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Choose a random meta-prompt for more variation
        meta_prompt = random.choice(VALIDATION_META_PROMPTS)
        prompt = meta_prompt.format(topic=topic)
        
        # Add validation-specific guidelines
        prompt += f"""

        IMPORTANT VALIDATION GUIDELINES:
        1. Focus on problem identification and community feedback
        2. Present yourself as exploring the problem space, not selling a solution
        3. Ask specific questions about their current tools and pain points
        4. Include phrases like "What's your experience..." and "How are you solving..."
        5. Make it genuinely curious and community-focused
        6. Avoid sales language - focus on learning and validation
        7. Include concrete examples of the problems you're exploring
        8. End with specific asks for feedback and experiences

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
                "temperature": temperature,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1000
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
            if len(generated_text) > 2800:
                generated_text = generated_text[:2700] + "...\n\nWhat's your take on this? Share your thoughts below!"
            
            logger.info(f"Successfully generated validation content ({len(generated_text)} chars)")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            # Generate a fallback content
            return self._generate_fallback_content(topic)
    
    def _generate_fallback_content(self, topic: str) -> str:
        """
        Generate fallback validation content in case of API failure.
        
        Args:
            topic: The topic to generate content about
            
        Returns:
            Fallback validation content
        """
        validation_templates = [
            f"Hey DevOps community! 👋\n\nBeen thinking about {topic} lately and wondering...\n\nAre you also struggling with:\n→ Tool sprawl across monitoring, logs, and costs\n→ Context switching between different dashboards\n→ Manual correlation when issues arise\n→ Lack of unified K8s observability\n\nWhat if there was a single platform that could:\n✅ Connect to your clusters instantly\n✅ Unify logs, metrics, and cost data\n✅ Provide AI-powered troubleshooting\n✅ Optimize costs automatically\n\n🤔 What's your current setup?\n💭 What would be most valuable to you?\n🎯 Missing anything from this vision?",
            
            f"DevOps folks - need your honest input! 🔍\n\nObservation: {topic} seems to be a common pain point.\n\nCurrent reality:\n• Multiple tools for K8s monitoring\n• Logs scattered everywhere\n• Cost visibility is poor\n• Troubleshooting takes forever\n• Context switching kills productivity\n\nImagining a world where:\n🎯 One dashboard shows everything\n⚡ AI helps debug issues instantly\n💰 Cost optimization happens automatically\n🔍 Logs and metrics are correlated\n\n💬 Does this match your experience?\n🛠️ How are you solving this today?\n🚀 What would make the biggest impact?",
            
            f"Quick question for the DevOps community... 🤔\n\n{topic} - anyone else finding this challenging?\n\nWhat I'm seeing:\n📊 Great tools exist (Grafana, Prometheus, ELK)\n🔄 But they're all separate systems\n⏰ Correlation takes manual work\n💸 Cost visibility is an afterthought\n🐛 Debugging feels like detective work\n\nWondering about a unified approach:\n• Single pane of glass for K8s\n• AI-powered incident analysis\n• Real-time cost optimization\n• Intelligent log correlation\n\n🔥 Are you frustrated with current solutions?\n💡 What features would be must-haves?\n📈 What results matter most to you?"
        ]
        
        return random.choice(validation_templates)

class LinkedInHelper:
    """Helper class for LinkedIn API operations - exact same as working code."""
    
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
    """Main function to run the K8s validation post automation - exact same structure as working code."""
    try:
        # Get environment variables - exact same validation as working code
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
        
        # Initialize validation content generator
        gemini = GeminiValidationGenerator(gemini_api_key, history_manager)
        
        # Generate a validation topic
        topic = gemini.generate_topic()
        
        # Generate and verify validation post content
        post = gemini.generate_and_verify_post(topic)
        
        # Log the review result
        logger.info(f"Post quality review: {post.get('review', 'No review available')}")
        
        # Debug output mode (if environment variable is set)
        if os.environ.get("DEBUG_MODE") == "true":
            logger.info("DEBUG MODE: Printing post without publishing")
            print("\n" + "="*60)
            print(f"Topic: {post['title']}")
            print("-"*60)
            print(post['content'])
            print("\n" + "="*60)
            print(f"Quality Review: {post.get('review', 'No review available')}")
            print("="*60 + "\n")
            return
        
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
                f.write(f"post_quality={post.get('review', 'No review available')}\n")
        
        logger.info
