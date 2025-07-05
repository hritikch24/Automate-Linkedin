#!/usr/bin/env python3
"""
Enhanced LinkedIn DevOps Post Automation with Business-Focused Content Generation
--------------------------------------------------------------------------------
This script generates business-focused DevOps content that showcases cost savings,
efficiency improvements, and client benefits. Includes validation to ensure
posts make logical sense before publishing.

Features:
- Content validation before posting
- Business-focused messaging with ROI emphasis
- Startup-friendly CTAs and engagement hooks
- Quality assurance checks
- Cost savings and efficiency metrics

Required environment variables:
- LINKEDIN_ACCESS_TOKEN: Your LinkedIn API access token
- LINKEDIN_ORGANIZATION_ID: Your LinkedIn organization/company ID
- GEMINI_API_KEY: Your Gemini API key
"""

import os
import json
import random
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Business-focused DevOps topics that showcase value
BUSINESS_FOCUSED_TOPICS = [
    "DevOps ROI", "Cloud Cost Optimization", "Startup Infrastructure", "Deployment Automation",
    "Monitoring Solutions", "Security Automation", "Scalable Architecture", "CI/CD Pipeline",
    "Container Orchestration", "Infrastructure as Code", "Performance Optimization",
    "Disaster Recovery", "Cloud Migration", "DevSecOps", "Microservices Architecture",
    "Database Optimization", "Load Balancing", "Auto-scaling", "Cost Management",
    "Technical Debt Reduction", "Platform Engineering", "SRE Practices"
]

# Business value-focused prompts
BUSINESS_VALUE_PROMPTS = [
    """Generate a LinkedIn post about how {topic} can help startups save 40-60% on infrastructure costs. 
    Include specific examples of cost savings, efficiency improvements, and how small teams can achieve enterprise-level results.
    
    MUST include these business benefits:
    - Specific cost savings percentages
    - Time-to-market improvements
    - Reduced manual effort/errors
    - Scalability without complexity
    
    End with engagement CTAs like:
    - "Comment 'SAVE' if you want to cut your infrastructure costs by 50%"
    - "DM 'OPTIMIZE' for a free cost analysis of your current setup"
    - "Want to see how we helped [company type] save $X/month? Drop a comment!"
    
    Include hashtags and make it 15-20 lines with emojis.""",
    
    """Create a LinkedIn post explaining how {topic} eliminates common startup pain points and reduces technical debt by 70%.
    Focus on real problems startups face and specific solutions.
    
    MUST address these pain points:
    - Scaling challenges as the team grows
    - Security vulnerabilities in rapid development
    - Manual processes eating up developer time
    - Unreliable deployments causing downtime
    
    Include engagement hooks:
    - "Struggling with [specific problem]? Comment below!"
    - "DM 'SOLVE' for a free consultation on fixing these issues"
    - "Tag a founder who needs to see this!"
    
    Use emojis, bullet points, and relevant hashtags.""",
    
    """Write a LinkedIn post about how proper {topic} implementation can increase development velocity by 3x while reducing bugs by 80%.
    Include case study elements and specific metrics.
    
    MUST include:
    - Before/after scenarios
    - Specific productivity metrics
    - Quality improvements
    - Team satisfaction benefits
    
    End with service-oriented CTAs:
    - "Ready to 3x your development speed? DM 'ACCELERATE'"
    - "Comment 'VELOCITY' for a free development process audit"
    - "Want to eliminate deployment fears? Let's chat!"
    
    Format with emojis and professional tone.""",
    
    """Generate a post about how {topic} helps startups achieve 99.9% uptime while reducing operational overhead by 60%.
    Focus on reliability, customer trust, and business continuity.
    
    MUST cover:
    - Uptime improvements and customer impact
    - Reduced operational burden
    - Automated incident response
    - Cost-effective monitoring solutions
    
    Include engaging CTAs:
    - "Tired of 3 AM outage calls? Comment 'SLEEP' below"
    - "DM 'UPTIME' for a free reliability assessment"
    - "Want bulletproof infrastructure? Let's talk!"
    
    Use professional language with startup-friendly tone.""",
    
    """Create a post about how {topic} enables startups to scale from 1K to 1M users without hiring additional DevOps engineers.
    Emphasize automation and cost-effective scaling.
    
    MUST highlight:
    - Scaling without team growth
    - Automated resource management
    - Predictable cost scaling
    - Performance under load
    
    End with growth-focused CTAs:
    - "Planning for rapid growth? Comment 'SCALE' below!"
    - "DM 'GROWTH' for a free scalability consultation"
    - "Ready to handle 10x traffic? Let's discuss your architecture!"
    
    Include relevant hashtags and emojis."""
]

# High-converting engagement hooks
CONVERSION_FOCUSED_CTAS = [
    "💰 Want to cut your AWS bill by 40%? DM 'OPTIMIZE' for a free audit!",
    "🚀 Ready to deploy 10x faster? Comment 'SPEED' below!",
    "🔒 Tired of security vulnerabilities? DM 'SECURE' for a free assessment!",
    "📈 Want to scale without breaking the bank? Comment 'SCALE'!",
    "⚡ Need 99.9% uptime on a startup budget? DM 'UPTIME'!",
    "🛠️ Struggling with manual deployments? Comment 'AUTOMATE'!",
    "💡 Want enterprise-level infrastructure at startup cost? DM 'ENTERPRISE'!",
    "🎯 Ready to eliminate technical debt? Comment 'CLEANUP'!",
    "🔥 Need help choosing the right DevOps stack? DM 'STACK'!",
    "⭐ Want a free infrastructure review? Comment 'REVIEW'!"
]

# Business metrics and social proof elements
BUSINESS_METRICS = [
    "40-60% cost reduction in first 3 months",
    "3x faster deployment cycles",
    "80% reduction in production bugs",
    "99.9% uptime achievement",
    "50% less time spent on maintenance",
    "70% faster time-to-market",
    "90% reduction in manual tasks",
    "60% improvement in developer productivity",
    "75% fewer security incidents",
    "45% reduction in server costs"
]

# Urgency and scarcity elements for better conversion
URGENCY_ELEMENTS = [
    "🔥 Limited slots: Only 5 free consultations available this month!",
    "⏰ Act fast: Free infrastructure audit ends Friday!",
    "🎯 This week only: Complimentary DevOps assessment for startups!",
    "⚡ Quick wins available: 30-minute call to identify cost savings!",
    "💡 Special offer: Free architecture review for the first 10 comments!",
    "🚀 Time-sensitive: Holiday pricing ends December 31st!",
    "⭐ Limited availability: Book your free consultation today!",
    "🔥 Early bird special: 50% off DevOps transformation this quarter!"
]


class ContentValidator:
    """Validates content for logical consistency and business value."""
    
    @staticmethod
    def validate_content(topic: str, content: str) -> Dict[str, Any]:
        """
        Validate that content makes logical sense and includes business value.
        
        Args:
            topic: The post topic
            content: The post content
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        score = 100
        
        # Check for business value indicators
        business_keywords = [
            'cost', 'save', 'roi', 'revenue', 'profit', 'efficiency', 'productivity',
            'scale', 'growth', 'uptime', 'performance', 'automation', 'reduce',
            'eliminate', 'optimize', 'improve', 'faster', 'better', 'cheaper'
        ]
        
        content_lower = content.lower()
        business_keyword_count = sum(1 for keyword in business_keywords if keyword in content_lower)
        
        if business_keyword_count < 3:
            issues.append("Content lacks sufficient business value keywords")
            score -= 20
        
        # Check for specific metrics or percentages
        metric_pattern = r'\d+%|\d+x|\$\d+|\d+k|\d+m'
        if not re.search(metric_pattern, content):
            issues.append("Content lacks specific metrics or quantifiable benefits")
            score -= 15
        
        # Check for engagement elements
        engagement_patterns = [
            r'comment.*below', r'dm.*me', r'tag.*someone', r'share.*your',
            r'drop.*comment', r'let.*me.*know', r'what.*do.*you.*think'
        ]
        
        has_engagement = any(re.search(pattern, content_lower) for pattern in engagement_patterns)
        if not has_engagement:
            issues.append("Content lacks engagement elements")
            score -= 10
        
        # Check for CTAs
        cta_keywords = ['dm', 'comment', 'connect', 'message', 'consultation', 'audit', 'review']
        cta_count = sum(1 for keyword in cta_keywords if keyword in content_lower)
        
        if cta_count < 2:
            issues.append("Content lacks strong call-to-action elements")
            score -= 15
        
        # Check content length (optimal for LinkedIn)
        if len(content) < 500:
            issues.append("Content might be too short for good engagement")
            score -= 10
        elif len(content) > 3000:
            issues.append("Content might be too long for LinkedIn")
            score -= 10
        
        # Check for logical flow
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) < 5:
            issues.append("Content might lack sufficient detail or examples")
            score -= 10
        
        # Check for professional tone while being engaging
        if content.count('🔥') > 3 or content.count('💰') > 2:
            issues.append("Content might be too emoji-heavy")
            score -= 5
        
        return {
            'is_valid': score >= 70,
            'score': score,
            'issues': issues,
            'has_business_value': business_keyword_count >= 3,
            'has_metrics': bool(re.search(metric_pattern, content)),
            'has_engagement': has_engagement,
            'has_cta': cta_count >= 2
        }


class PostHistoryManager:
    """Manages post history to avoid duplicates and track performance."""
    
    def __init__(self, history_file_path: str = None):
        if history_file_path:
            self.history_file = history_file_path
        else:
            history_dir = os.path.join(os.getcwd(), ".github", "post-history")
            os.makedirs(history_dir, exist_ok=True)
            self.history_file = os.path.join(history_dir, "linkedin-posts.log")
        
        self.post_history = self._load_history()
    
    def _load_history(self) -> List[str]:
        """Load post history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    posts = []
                    sections = content.split("----------------------------------------")
                    for section in sections:
                        if section.strip():
                            lines = section.strip().split("\n")
                            if len(lines) > 2:
                                post_content = "\n".join(lines[2:])
                                posts.append(post_content)
                    return posts
            return []
        except Exception as e:
            logger.warning(f"Failed to load post history: {e}")
            return []
    
    def is_similar_to_previous(self, content: str, threshold: float = 0.6) -> bool:
        """Check if content is too similar to previous posts."""
        def normalize(text):
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        normalized_content = normalize(content)
        
        for previous_post in self.post_history:
            normalized_previous = normalize(previous_post)
            similarity = SequenceMatcher(None, normalized_content, normalized_previous).ratio()
            if similarity > threshold:
                logger.info(f"Content similarity detected: {similarity:.2f}")
                return True
        
        return False
    
    def add_post(self, title: str, content: str, validation_score: int) -> None:
        """Add a new post to history with validation score."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp}: {title} (Score: {validation_score})\n")
                f.write("-" * 40 + "\n")
                f.write(f"{content}\n\n")
            
            self.post_history.append(content)
            logger.info(f"Post added to history: {title}")
        except Exception as e:
            logger.warning(f"Failed to add post to history: {e}")


class GeminiContentGenerator:
    """Generates business-focused DevOps content using Gemini AI."""
    
    def __init__(self, api_key: str, history_manager: PostHistoryManager):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.history_manager = history_manager
        self.validator = ContentValidator()
    
    def generate_business_focused_post(self, max_attempts: int = 7) -> Dict[str, Any]:
        """
        Generate a business-focused DevOps post with validation.
        
        Returns:
            Dictionary with post data and validation results
        """
        for attempt in range(max_attempts):
            logger.info(f"Content generation attempt {attempt + 1}/{max_attempts}")
            
            # Select a business-focused topic
            topic = random.choice(BUSINESS_FOCUSED_TOPICS)
            
            # Generate content
            content = self._generate_content_with_business_focus(topic)
            
            # Enhance with business elements
            enhanced_content = self._enhance_with_business_elements(content, topic)
            
            # Validate content
            validation = self.validator.validate_content(topic, enhanced_content)
            
            # Check similarity to previous posts
            if self.history_manager.is_similar_to_previous(enhanced_content):
                logger.info("Content too similar to previous posts, regenerating...")
                continue
            
            # Check if content meets quality standards
            if validation['is_valid'] and validation['score'] >= 80:
                logger.info(f"High-quality content generated (score: {validation['score']})")
                return {
                    'title': topic,
                    'content': enhanced_content,
                    'validation': validation,
                    'attempt': attempt + 1
                }
            elif validation['score'] >= 70:
                logger.info(f"Acceptable content generated (score: {validation['score']})")
                return {
                    'title': topic,
                    'content': enhanced_content,
                    'validation': validation,
                    'attempt': attempt + 1
                }
            else:
                logger.info(f"Content quality insufficient (score: {validation['score']}), retrying...")
                logger.info(f"Issues: {', '.join(validation['issues'])}")
        
        # If we can't generate good content, create a fallback
        logger.warning("Could not generate high-quality content, using fallback")
        topic = random.choice(BUSINESS_FOCUSED_TOPICS)
        fallback_content = self._generate_fallback_content(topic)
        enhanced_fallback = self._enhance_with_business_elements(fallback_content, topic)
        validation = self.validator.validate_content(topic, enhanced_fallback)
        
        return {
            'title': topic,
            'content': enhanced_fallback,
            'validation': validation,
            'attempt': max_attempts
        }
    
    def _generate_content_with_business_focus(self, topic: str) -> str:
        """Generate business-focused content using Gemini."""
        url = f"{self.api_url}?key={self.api_key}"
        
        # Add randomization for uniqueness
        random_seed = random.randint(1000, 9999)
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        
        # Select a business-focused prompt
        prompt_template = random.choice(BUSINESS_VALUE_PROMPTS)
        prompt = prompt_template.format(topic=topic)
        
        # Add specific instructions for quality and business focus
        prompt += f"""
        
        CRITICAL REQUIREMENTS:
        1. Include specific, realistic metrics and percentages
        2. Focus on startup pain points and cost-effective solutions
        3. Add compelling CTAs that drive engagement and leads
        4. Make it authentic and avoid generic DevOps buzzwords
        5. Include social proof elements or case study hints
        6. Ensure content is logically consistent and makes business sense
        7. Target startup founders and CTOs specifically
        8. Emphasize ROI and cost savings throughout
        
        VALIDATION CHECKLIST:
        - Does this solve a real business problem?
        - Are the metrics realistic and credible?
        - Would a startup founder find this valuable?
        - Does it clearly communicate cost savings or efficiency gains?
        - Are the CTAs compelling and conversion-focused?
        
        Unique seed: {random_seed}
        Timestamp: {timestamp}
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.8,
                "topK": 40,
                "topP": 0.9,
                "maxOutputTokens": 1200
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code}")
                return self._generate_fallback_content(topic)
            
            response_data = response.json()
            content = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean up content
            content = content.strip()
            if len(content) > 2800:
                content = content[:2700] + "\n\n💬 What's your biggest challenge with this? Let's discuss!"
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return self._generate_fallback_content(topic)
    
    def _enhance_with_business_elements(self, content: str, topic: str) -> str:
        """Enhance content with business-focused elements."""
        enhanced = content.strip()
        
        # Add business metrics if missing
        if not re.search(r'\d+%', enhanced):
            metric = random.choice(BUSINESS_METRICS)
            enhanced += f"\n\n📊 Real impact: {metric}"
        
        # Add compelling CTA
        cta = random.choice(CONVERSION_FOCUSED_CTAS)
        enhanced += f"\n\n{cta}"
        
        # Add urgency element (50% chance)
        if random.random() < 0.5:
            urgency = random.choice(URGENCY_ELEMENTS)
            enhanced += f"\n\n{urgency}"
        
        # Add relevant hashtags for visibility
        hashtags = self._generate_relevant_hashtags(topic)
        enhanced += f"\n\n{hashtags}"
        
        return enhanced
    
    def _generate_relevant_hashtags(self, topic: str) -> str:
        """Generate relevant hashtags based on topic."""
        base_hashtags = ["#DevOps", "#StartupTech", "#CloudComputing", "#TechLeadership"]
        
        topic_map = {
            "cost": ["#CostOptimization", "#AWSCosts", "#CloudSavings"],
            "security": ["#DevSecOps", "#Cybersecurity", "#SecureCloud"],
            "scale": ["#Scalability", "#GrowthHacking", "#TechScaling"],
            "automation": ["#Automation", "#CICD", "#NoOps"],
            "startup": ["#StartupLife", "#TechFounder", "#ScaleUp"],
            "kubernetes": ["#Kubernetes", "#ContainerOrchestration", "#CloudNative"],
            "monitoring": ["#Observability", "#SRE", "#PerformanceMonitoring"]
        }
        
        topic_lower = topic.lower()
        additional_hashtags = []
        
        for key, hashtags in topic_map.items():
            if key in topic_lower:
                additional_hashtags.extend(hashtags[:2])
        
        # Combine and limit to 10 total hashtags
        all_hashtags = base_hashtags + additional_hashtags
        selected_hashtags = random.sample(all_hashtags, min(10, len(all_hashtags)))
        
        return " ".join(selected_hashtags)
    
    def _generate_fallback_content(self, topic: str) -> str:
        """Generate fallback content when API fails."""
        metric = random.choice(BUSINESS_METRICS)
        cta = random.choice(CONVERSION_FOCUSED_CTAS)
        
        content = f"""🚀 {topic}: The Game-Changer for Growing Startups

Are you tired of watching your infrastructure costs spiral out of control as you scale? 

Here's what proper {topic.lower()} implementation can do for your startup:

✅ {metric}
✅ Eliminate manual deployment headaches
✅ Scale automatically without hiring DevOps engineers
✅ Sleep better knowing your systems are bulletproof
✅ Focus on building features, not fighting infrastructure

The difference between startups that scale smoothly and those that struggle? They invested early in the right {topic.lower()} strategy.

💡 Pro tip: Most startups wait until it's too late. The best time to optimize your infrastructure was yesterday. The second best time is now.

{cta}

🤔 What's your biggest infrastructure challenge right now? Drop it in the comments!"""

        return content


class LinkedInHelper:
    """Enhanced LinkedIn API helper with better error handling."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Retrieve user profile with enhanced error handling."""
        logger.info("Retrieving user profile...")
        url = "https://api.linkedin.com/v2/me"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Profile retrieval failed: {response.status_code}")
                raise Exception(f"LinkedIn API error: {response.status_code}")
            
            profile_data = response.json()
            logger.info(f"Profile retrieved successfully. ID: {profile_data.get('id')}")
            return profile_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error retrieving profile: {e}")
            raise
    
    def post_content(self, person_id: str, organization_id: str, content: str) -> Dict[str, Any]:
        """Post content with fallback strategies."""
        # Try organization post first
        try:
            logger.info(f"Attempting to post as organization {organization_id}...")
            return self._post_as_organization(person_id, organization_id, content)
        except Exception as e:
            logger.warning(f"Organization post failed: {e}")
            
            # Fallback to personal post
            logger.info("Falling back to personal post...")
            return self._post_as_person(person_id, content)
    
    def _post_as_organization(self, person_id: str, organization_id: str, content: str) -> Dict[str, Any]:
        """Post as organization."""
        url = "https://api.linkedin.com/v2/ugcPosts"
        
        post_data = {
            "author": f"urn:li:organization:{organization_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        response = requests.post(url, headers=self.headers, json=post_data, timeout=30)
        
        if response.status_code not in (200, 201):
            raise Exception(f"Personal post failed: {response.status_code}")
        
        logger.info("Successfully posted as person")
        return response.json() if response.text else {}


def main() -> None:
    """Main function with enhanced error handling and validation."""
    try:
        # Validate environment variables
        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        organization_id = os.environ.get("LINKEDIN_ORGANIZATION_ID")
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
        
        if not all([access_token, organization_id, gemini_api_key]):
            logger.error("Missing required environment variables")
            logger.error("Required: LINKEDIN_ACCESS_TOKEN, LINKEDIN_ORGANIZATION_ID, GEMINI_API_KEY")
            exit(1)
        
        # Clean organization ID
        if organization_id.startswith("urn:li:organization:"):
            organization_id = organization_id.replace("urn:li:organization:", "")
        
        # Initialize components
        history_manager = PostHistoryManager()
        gemini = GeminiContentGenerator(gemini_api_key, history_manager)
        
        # Generate business-focused content
        logger.info("Generating business-focused DevOps content...")
        post_data = gemini.generate_business_focused_post()
        
        # Log validation results
        validation = post_data['validation']
        logger.info(f"Content validation score: {validation['score']}/100")
        logger.info(f"Business value: {'✅' if validation['has_business_value'] else '❌'}")
        logger.info(f"Includes metrics: {'✅' if validation['has_metrics'] else '❌'}")
        logger.info(f"Has engagement: {'✅' if validation['has_engagement'] else '❌'}")
        logger.info(f"Has CTAs: {'✅' if validation['has_cta'] else '❌'}")
        
        if validation['issues']:
            logger.warning(f"Content issues: {', '.join(validation['issues'])}")
        
        # Debug mode - show content without posting
        if debug_mode:
            logger.info("DEBUG MODE: Displaying content without posting")
            print("\n" + "="*80)
            print(f"📝 TOPIC: {post_data['title']}")
            print("="*80)
            print(f"📊 VALIDATION SCORE: {validation['score']}/100")
            print(f"🔄 GENERATION ATTEMPTS: {post_data['attempt']}")
            print("-"*80)
            print("📄 CONTENT:")
            print("-"*80)
            print(post_data['content'])
            print("\n" + "="*80)
            print("🔍 VALIDATION DETAILS:")
            print(f"   Business Value: {'✅' if validation['has_business_value'] else '❌'}")
            print(f"   Metrics Included: {'✅' if validation['has_metrics'] else '❌'}")
            print(f"   Engagement Elements: {'✅' if validation['has_engagement'] else '❌'}")
            print(f"   Call-to-Action: {'✅' if validation['has_cta'] else '❌'}")
            if validation['issues']:
                print(f"   Issues: {', '.join(validation['issues'])}")
            print("="*80 + "\n")
            return
        
        # Only proceed with posting if content meets minimum quality
        if validation['score'] < 60:
            logger.error(f"Content quality too low (score: {validation['score']}), aborting post")
            exit(1)
        
        # Initialize LinkedIn helper and post
        linkedin = LinkedInHelper(access_token)
        
        # Get user profile
        profile = linkedin.get_user_profile()
        person_id = profile.get('id')
        
        if not person_id:
            logger.error("Failed to retrieve person ID from profile")
            exit(1)
        
        # Post content
        logger.info("Posting content to LinkedIn...")
        response = linkedin.post_content(person_id, organization_id, post_data['content'])
        
        # Add to post history
        history_manager.add_post(
            post_data['title'], 
            post_data['content'], 
            validation['score']
        )
        
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write(f"post_title={post_data['title']}\n")
                f.write(f"post_status=success\n")
                f.write(f"post_quality={validation['score']}\n")
                f.write(f"validation_score={validation['score']}\n")
                f.write(f"has_business_value={validation['has_business_value']}\n")
                f.write(f"generation_attempts={post_data['attempt']}\n")
        
        logger.info("✅ LinkedIn post automation completed successfully!")
        logger.info(f"📝 Posted: {post_data['title']}")
        logger.info(f"📊 Quality Score: {validation['score']}/100")
        logger.info(f"🎯 Business-focused content with engagement optimization")
    
    except Exception as e:
        logger.error(f"❌ LinkedIn post automation failed: {e}")
        
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write("post_status=failed\n")
                f.write(f"error_message={str(e)}\n")
        
        exit(1)


if __name__ == "__main__":
    main() Exception(f"Organization post failed: {response.status_code}")
        
        logger.info("Successfully posted as organization")
        return response.json() if response.text else {}
    
    def _post_as_person(self, person_id: str, content: str) -> Dict[str, Any]:
        """Post as person."""
        url = "https://api.linkedin.com/v2/ugcPosts"
        
        post_data = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        response = requests.post(url, headers=self.headers, json=post_data, timeout=30)
        
        if response.status_code not in (200, 201):
            raise
