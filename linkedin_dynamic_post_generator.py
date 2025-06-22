#!/usr/bin/env python3
"""
LinkedIn DevOps Post Automation with Gemini AI Content Generation and Quality Review
Enhanced with Reach-Boosting Engagement Elements
---------------------------------------------------------------------------------
This script automatically generates unique DevOps content using Gemini AI and posts it to LinkedIn.
It uses Gemini to critically review its own posts before publishing to ensure high quality.
It checks for similarity with previous posts to avoid repetition.
Enhanced with engagement-boosting elements to increase reach and generate leads.

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

# Enhanced meta-prompts with engagement boosters
META_PROMPTS = [
    """Generate a unique, engaging LinkedIn post about {topic} with the latest trends, best practices, and controversial opinions. Include specific tools, metrics, and real-world examples. 
    
    IMPORTANT: End with strong engagement hooks like:
    - "What's been your biggest challenge with this? Drop a comment below!"
    - "DM me if you want to discuss implementation strategies for your team"
    - "Have you seen better results with different approaches? Let's connect!"
    
    Format with emojis and bullet points. Include hashtags. Make it 12-18 lines long and professional but attention-grabbing.""",
    
    """Create a thought-provoking LinkedIn post comparing different approaches to {topic}. Highlight pros, cons, and specific use cases for each approach. Include surprising statistics and industry trends.
    
    IMPORTANT: Include engagement elements like:
    - "Which approach has worked best for your organization? Share your experience!"
    - "Struggling with this decision? DM me for a quick consultation"
    - "Tag someone who needs to see this comparison!"
    
    Format with emojis and bullet points. Include relevant hashtags. Make it 12-18 lines long.""",
    
    """Write a technical LinkedIn post about solving common challenges in {topic}. Include specific tools, techniques, and code examples where relevant. Mention performance improvements and reliability gains.
    
    IMPORTANT: Add service-oriented CTAs like:
    - "Need help implementing this in your environment? Let's talk!"
    - "DM me if you want a free consultation on optimizing your setup"
    - "Facing similar challenges? Connect with me for solutions!"
    
    Format with emojis and bullet points. Make it 12-18 lines long and technically substantial but accessible.""",
    
    """Craft a forward-looking LinkedIn post about the future of {topic} in the next 2-3 years. Discuss emerging trends, tools, and practices that will become mainstream. Include specific predictions with reasoning.
    
    IMPORTANT: Include thought leadership CTAs:
    - "What trends are you most excited about? Share your predictions!"
    - "Planning your roadmap for these changes? DM me for strategic guidance"
    - "Agree or disagree with these predictions? Let's debate in the comments!"
    
    Format with emojis and bullet points. Make it 12-18 lines long and thought-provoking.""",
    
    """Write a LinkedIn post highlighting common mistakes and misconceptions about {topic}. Explain the correct approaches and why they matter. Include real-world consequences of these mistakes.
    
    IMPORTANT: Add problem-solving CTAs:
    - "Made any of these mistakes? You're not alone - let's fix them together!"
    - "DM me if you're dealing with these issues - I can help you avoid the pitfalls"
    - "What other mistakes have you seen? Share them below!"
    
    Format with emojis and bullet points. Make it 12-18 lines long and educational yet engaging."""
]

# Engagement boosting elements
ENGAGEMENT_HOOKS = [
    "💬 What's your experience with this? Drop a comment!",
    "🔥 Tag someone who needs to see this!",
    "💡 Have a different approach? I'd love to hear it!",
    "🚀 What challenges are you facing with this? Let's discuss!",
    "⚡ Agree or disagree? Let's debate in the comments!",
    "🎯 What's your biggest pain point here? Share below!",
    "🛠️ Which tools have worked best for you?",
    "📈 What results have you seen with this approach?",
    "🤔 What would you add to this list?",
    "💪 Ready to level up your game? Let's connect!"
]

SERVICE_ORIENTED_CTAS = [
    "🔥 Need help implementing this? DM me for a free consultation!",
    "💼 Struggling with your DevOps transformation? Let's chat about solutions!",
    "⚡ Want to accelerate your cloud journey? Send me a message!",
    "🎯 Looking for expert guidance on this? DM me - I help teams just like yours!",
    "🚀 Ready to optimize your infrastructure? Let's discuss your specific needs!",
    "💡 Need a strategy session? DM me for personalized recommendations!",
    "🛠️ Want hands-on help with implementation? Let's talk about your project!",
    "📈 Looking to improve your metrics? I can show you proven strategies!",
    "⭐ Need a DevOps audit or consultation? Message me for details!",
    "🔧 Facing technical challenges? I specialize in solving exactly these problems!"
]

URGENCY_CREATORS = [
    "🔥 Limited time: Free consultation this week only!",
    "⚡ Early bird special: Connect now for priority response!",
    "🎯 This week only: Free architecture review for qualified teams!",
    "🚀 Quick wins available: Let's identify your lowest-hanging fruit!",
    "💎 Exclusive offer: Free 30-min strategy session this month!",
    "⭐ Special opportunity: Connect now for custom recommendations!",
    "🔥 Act fast: Limited slots for new consultations!",
    "💡 Time-sensitive: Free assessment ends this Friday!"
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
    """Generates unique DevOps content using Gemini AI with engagement boosters."""
    
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
        
        It should be about something current and relevant in the tech industry that could generate engagement and discussion.
        
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
    
    def _enhance_content_with_engagement_boosters(self, content: str, topic: str) -> str:
        """
        Enhance content with engagement-boosting elements.
        
        Args:
            content: Original content
            topic: Post topic
            
        Returns:
            Enhanced content with engagement elements
        """
        # Decide what type of engagement elements to add based on randomization
        engagement_type = random.choice(["hooks_only", "service_cta", "urgency_combo"])
        
        enhanced_content = content.strip()
        
        if engagement_type == "hooks_only":
            # Add engagement hooks only
            hook = random.choice(ENGAGEMENT_HOOKS)
            enhanced_content += f"\n\n{hook}"
            
        elif engagement_type == "service_cta":
            # Add service-oriented CTA
            hook = random.choice(ENGAGEMENT_HOOKS)
            service_cta = random.choice(SERVICE_ORIENTED_CTAS)
            enhanced_content += f"\n\n{hook}\n{service_cta}"
            
        elif engagement_type == "urgency_combo":
            # Add engagement hook + service CTA + urgency creator
            hook = random.choice(ENGAGEMENT_HOOKS)
            service_cta = random.choice(SERVICE_ORIENTED_CTAS)
            urgency = random.choice(URGENCY_CREATORS)
            enhanced_content += f"\n\n{hook}\n{service_cta}\n\n{urgency}"
        
        # Add a professional connection request (30% chance)
        if random.random() < 0.3:
            connection_requests = [
                "\n\n🤝 Found this valuable? Connect with me for more DevOps insights!",
                "\n\n🌟 Follow for daily DevOps tips and industry updates!",
                "\n\n🚀 Connect with me to stay updated on the latest tech trends!",
                "\n\n💼 Building your professional network? Let's connect!",
                "\n\n⚡ Want more content like this? Hit that follow button!"
            ]
            enhanced_content += random.choice(connection_requests)
        
        # Add trending hashtags for better reach (always include)
        trending_hashtags = [
            "#DevOps", "#CloudNative", "#TechTrends", "#Innovation", "#TechLeadership",
            "#Engineering", "#SoftwareDevelopment", "#Automation", "#DigitalTransformation",
            "#Kubernetes", "#Cloud", "#CICD", "#Infrastructure", "#Microservices", 
            "#DevSecOps", "#SRE", "#Technology", "#CloudComputing", "#ArtificialIntelligence",
            "#MachineLearning", "#DataScience", "#Cybersecurity", "#OpenSource"
        ]
        
        # Select 8-12 hashtags for maximum reach
        selected_hashtags = random.sample(trending_hashtags, random.randint(8, 12))
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
        Generate a post and have Gemini verify its quality before finalizing.
        
        Args:
            topic: The topic to generate content about
            max_attempts: Maximum number of generation attempts
            
        Returns:
            Dictionary with title and content
        """
        logger.info(f"Generating and verifying content about: {topic}")
        
        for attempt in range(max_attempts):
            logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
            
            # Generate content
            content = self._generate_single_content(topic)
            
            # Enhance with engagement boosters
            enhanced_content = self._enhance_content_with_engagement_boosters(content, topic)
            
            # Check if content is similar to previous posts
            if self.history_manager.is_similar_to_previous(enhanced_content):
                logger.info(f"Generated content too similar to previous post, trying again...")
                continue
            
            # Self-review the post quality with Gemini
            review_result = self._review_post_quality(topic, enhanced_content)
            if review_result["is_good_quality"]:
                logger.info(f"Post passed quality review: {review_result['explanation']}")
                return {
                    "title": topic,
                    "content": enhanced_content,
                    "review": review_result['explanation']
                }
            else:
                logger.info(f"Post failed quality review: {review_result['explanation']}")
        
        # If we couldn't generate good quality content after max_attempts, create one with higher randomization
        logger.warning(f"Could not generate good quality content after {max_attempts} attempts, using higher randomization")
        content = self._generate_single_content(topic, temperature=1.0)
        enhanced_content = self._enhance_content_with_engagement_boosters(content, topic)
        review_result = self._review_post_quality(topic, enhanced_content)
        
        return {
            "title": topic,
            "content": enhanced_content,
            "review": review_result.get('explanation', 'No review available for final attempt')
        }
    
    def _review_post_quality(self, topic: str, content: str) -> Dict[str, Any]:
        """
        Have Gemini review the quality of a generated post.
        
        Args:
            topic: The post topic
            content: The post content
            
        Returns:
            Dictionary with review results
        """
        url = f"{self.api_url}?key={self.api_key}"
        
        review_prompt = f"""
        You are a critical content reviewer for DevOps and tech-related LinkedIn posts with a focus on engagement and lead generation.
        You have very high standards for content quality, originality, professionalism, and engagement potential.
        
        Review the following LinkedIn post about "{topic}" and determine if it meets these standards:
        
        1. Is it specific and insightful rather than generic?
        2. Does it avoid repetitive phrasing and awkward wording?
        3. Does it provide real value rather than empty platitudes?
        4. Is it authentic and not overly AI-generated sounding?
        5. Would a DevOps professional find it credible and valuable?
        6. Does it avoid repeating the same phrase multiple times?
        7. Does it have a natural flow with varied sentence structures?
        8. Does it include specific examples, tools, or practices?
        9. Does it have good engagement elements that would encourage interaction?
        10. Are the CTAs natural and not overly salesy?
        
        POST CONTENT TO REVIEW:
        ----------------------
        {content}
        ----------------------
        
        First, provide a yes/no determination if this post meets professional quality standards and has good engagement potential.
        Then, explain your reasoning in 2-3 sentences.
        
        Format your response exactly like this:
        VERDICT: [yes/no]
        EXPLANATION: [your explanation]
        """
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": review_prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,  # Low temperature for more consistent evaluation
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 200
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Gemini API error during review: {response.status_code}")
                # Default to accepting the post if review fails
                return {"is_good_quality": True, "explanation": "Review failed, defaulting to accept"}
            
            response_data = response.json()
            review_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse the review response
            verdict_line = next((line for line in review_text.split('\n') if line.startswith('VERDICT:')), '')
            explanation_line = next((line for line in review_text.split('\n') if line.startswith('EXPLANATION:')), '')
            
            verdict = 'yes' in verdict_line.lower() if verdict_line else True
            explanation = explanation_line.replace('EXPLANATION:', '').strip() if explanation_line else "No detailed explanation provided"
            
            return {
                "is_good_quality": verdict,
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error during post quality review: {e}")
            # Default to accepting the post if an exception occurs
            return {"is_good_quality": True, "explanation": f"Review error: {str(e)}"}
    
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
        
        # Add quality improvement instructions
        prompt += f"""

        IMPORTANT QUALITY GUIDELINES:
        1. Be specific and technical - mention specific tools, techniques or metrics
        2. Avoid repetitive phrasing - never repeat the title phrase multiple times
        3. Write in a natural human voice that sounds authentic and authoritative
        4. Include concrete examples and practical insights
        5. Avoid generic statements or empty platitudes
        6. Use varied sentence structures and natural transitions
        7. Ensure every point provides real value to DevOps professionals
        8. Make it engaging and encourage discussion
        9. Include strategic CTAs that feel natural, not pushy
        10. Focus on building trust and demonstrating expertise

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
            f"🚀 {topic} has seen dramatic evolution in recent years",
            f"📊 Most organizations struggle with implementing this effectively",
            f"💰 Proper implementation can deliver 300%+ ROI",
            f"⚡ Industry leaders report 60% faster time-to-market",
            f"🎯 Common misconceptions lead to implementation failures",
            f"🔧 Best practices include automated testing and continuous feedback",
            f"🔮 AI integration will reshape this space significantly",
            f"🔒 Security considerations are often overlooked initially",
            f"📈 Proper monitoring is essential for production success",
            f"👥 Team structure impacts effectiveness more than tools",
            f"🎓 Training and culture are as important as technology",
            f"💡 Cost optimization becomes critical at scale",
            f"🌟 Open source tools have democratized access",
            f"📈 Enterprise adoption has increased 85% this year",
            f"⚖️ Hybrid approaches often yield the best results",
            f"🧠 The biggest challenges are organizational, not technical",
            f"🎯 Success requires executive buy-in and cultural shift",
            f"🏆 Small wins build momentum for larger transformations",
            f"📊 Metrics and measurement drive continuous improvement",
            f"🔍 The talent gap remains a significant challenge"
        ]
        
        # Create a unique combination of points
        random.shuffle(random_points)
        selected_points = random_points[:random.randint(6, 8)]
        
        engagement_elements = [
            "💬 What's been your experience with this technology?",
            "🤔 Which challenges resonate most with your team?",
            "🎯 What would you add to this list?",
            "⚡ Ready to accelerate your implementation?"
        ]
        
        service_cta = random.choice(SERVICE_ORIENTED_CTAS)
        engagement = random.choice(engagement_elements)
        
        content = (
            f"🚀 Key insights about {topic} 🚀\n\n"
            f"Been diving deep into this lately and wanted to share some observations:\n\n"
            + "\n".join(selected_points) + 
            f"\n\n{engagement}\n{service_cta}"
        )
        
        return content


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
        
        # Generate and verify post content
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
        
        logger.info("LinkedIn post automation completed successfully with enhanced engagement features.")
    
    except Exception as e:
        logger.error(f"Error during LinkedIn post automation: {e}")
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write("post_status=failed\n")
        exit(1)


if __name__ == "__main__":
    main()
