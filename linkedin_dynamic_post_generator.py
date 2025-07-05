#!/usr/bin/env python3
"""
LinkedIn DevOps Post Automation with Business-Focused Content Generation
------------------------------------------------------------------------
Enhanced script that generates business-focused DevOps content with validation,
cost savings focus, and engagement optimization for startups.

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

# Business-focused DevOps topics
BUSINESS_FOCUSED_TOPICS = [
    "DevOps ROI and Cost Optimization",
    "Startup Infrastructure Scaling",
    "CI/CD Pipeline Automation",
    "Cloud Cost Management",
    "DevSecOps for Small Teams",
    "Kubernetes for Startups",
    "Infrastructure as Code Benefits",
    "Monitoring and Observability",
    "Deployment Automation",
    "Container Orchestration ROI",
    "AWS Cost Optimization",
    "Azure Infrastructure Efficiency",
    "GCP Startup Credits Maximization",
    "Database Performance Optimization",
    "Load Balancing Strategies",
    "Auto-scaling Implementation",
    "Security Automation",
    "Technical Debt Reduction",
    "Platform Engineering Value",
    "SRE Practices for Startups"
]

# Business value-focused prompts
BUSINESS_VALUE_PROMPTS = [
    """Generate a LinkedIn post about how {topic} can help startups save 40-60% on infrastructure costs. 
    Include specific examples of cost savings, efficiency improvements, and how small teams can achieve enterprise-level results.
    
    MUST include business benefits:
    - Specific cost savings percentages
    - Time-to-market improvements  
    - Reduced manual effort/errors
    - Scalability without complexity
    
    End with engagement CTAs like:
    - "Comment 'SAVE' if you want to cut your infrastructure costs by 50%"
    - "DM 'OPTIMIZE' for a free cost analysis of your current setup"
    
    Include hashtags and make it engaging with emojis.""",
    
    """Create a LinkedIn post explaining how {topic} eliminates startup pain points and reduces technical debt by 70%.
    Focus on real problems startups face and specific solutions.
    
    Address these pain points:
    - Scaling challenges as team grows
    - Security vulnerabilities
    - Manual processes wasting time
    - Unreliable deployments
    
    Include engagement hooks:
    - "Struggling with scaling? Comment below!"
    - "DM 'SOLVE' for a free consultation"
    
    Use emojis and professional tone."""
]

# High-converting CTAs
CONVERSION_CTAS = [
    "💰 Want to cut your AWS bill by 40%? DM 'OPTIMIZE' for a free audit!",
    "🚀 Ready to deploy 10x faster? Comment 'SPEED' below!",
    "🔒 Tired of security vulnerabilities? DM 'SECURE' for assessment!",
    "📈 Want to scale without breaking the bank? Comment 'SCALE'!",
    "⚡ Need 99.9% uptime on startup budget? DM 'UPTIME'!",
    "🛠️ Struggling with manual deployments? Comment 'AUTOMATE'!",
    "💡 Want enterprise infrastructure at startup cost? DM 'ENTERPRISE'!",
    "🎯 Ready to eliminate technical debt? Comment 'CLEANUP'!"
]

# Business metrics
BUSINESS_METRICS = [
    "40-60% cost reduction in first 3 months",
    "3x faster deployment cycles", 
    "80% reduction in production bugs",
    "99.9% uptime achievement",
    "50% less time on maintenance",
    "70% faster time-to-market"
]


class ContentValidator:
    """Validates content quality and business value."""
    
    @staticmethod
    def validate_content(topic: str, content: str) -> Dict[str, Any]:
        """Validate content quality."""
        issues = []
        score = 100
        
        # Check for business keywords
        business_keywords = [
            'cost', 'save', 'roi', 'revenue', 'efficiency', 'productivity',
            'scale', 'uptime', 'automation', 'reduce', 'optimize', 'improve'
        ]
        
        content_lower = content.lower()
        business_count = sum(1 for keyword in business_keywords if keyword in content_lower)
        
        if business_count < 3:
            issues.append("Lacks business value keywords")
            score -= 20
        
        # Check for metrics
        if not re.search(r'\d+%|\d+x|\$\d+', content):
            issues.append("Missing quantifiable metrics")
            score -= 15
        
        # Check for engagement
        engagement_patterns = [r'comment.*below', r'dm.*me', r'tag.*someone']
        has_engagement = any(re.search(pattern, content_lower) for pattern in engagement_patterns)
        
        if not has_engagement:
            issues.append("Missing engagement elements")
            score -= 10
        
        # Check for CTAs
        cta_keywords = ['dm', 'comment', 'connect', 'consultation']
        cta_count = sum(1 for keyword in cta_keywords if keyword in content_lower)
        
        if cta_count < 2:
            issues.append("Weak call-to-action")
            score -= 15
        
        # Length check
        if len(content) < 500:
            issues.append("Content too short")
            score -= 10
        elif len(content) > 3000:
            issues.append("Content too long")
            score -= 10
        
        return {
            'is_valid': score >= 70,
            'score': score,
            'issues': issues,
            'has_business_value': business_count >= 3,
            'has_metrics': bool(re.search(r'\d+%|\d+x|\$\d+', content)),
            'has_engagement': has_engagement,
            'has_cta': cta_count >= 2
        }


class PostHistoryManager:
    """Manages post history to avoid duplicates."""
    
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
        """Check similarity to previous posts."""
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
                logger.info(f"Content similarity: {similarity:.2f}")
                return True
        
        return False
    
    def add_post(self, title: str, content: str, score: int) -> None:
        """Add post to history."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp}: {title} (Score: {score})\n")
                f.write("-" * 40 + "\n")
                f.write(f"{content}\n\n")
            
            self.post_history.append(content)
            logger.info(f"Post added to history: {title}")
        except Exception as e:
            logger.warning(f"Failed to add post to history: {e}")


class GeminiContentGenerator:
    """Generates business-focused DevOps content."""
    
    def __init__(self, api_key: str, history_manager: PostHistoryManager):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.history_manager = history_manager
        self.validator = ContentValidator()
    
    def generate_business_post(self, max_attempts: int = 5) -> Dict[str, Any]:
        """Generate a business-focused post."""
        for attempt in range(max_attempts):
            logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
            
            topic = random.choice(BUSINESS_FOCUSED_TOPICS)
            content = self._generate_content(topic)
            enhanced_content = self._enhance_content(content, topic)
            
            # Validate content
            validation = self.validator.validate_content(topic, enhanced_content)
            
            # Check similarity
            if self.history_manager.is_similar_to_previous(enhanced_content):
                logger.info("Content too similar, regenerating...")
                continue
            
            if validation['is_valid'] and validation['score'] >= 75:
                logger.info(f"Quality content generated (score: {validation['score']})")
                return {
                    'title': topic,
                    'content': enhanced_content,
                    'validation': validation,
                    'attempt': attempt + 1
                }
            else:
                logger.info(f"Quality insufficient (score: {validation['score']})")
        
        # Fallback
        logger.warning("Using fallback content")
        topic = random.choice(BUSINESS_FOCUSED_TOPICS)
        fallback_content = self._generate_fallback_content(topic)
        enhanced_fallback = self._enhance_content(fallback_content, topic)
        validation = self.validator.validate_content(topic, enhanced_fallback)
        
        return {
            'title': topic,
            'content': enhanced_fallback,
            'validation': validation,
            'attempt': max_attempts
        }
    
    def _generate_content(self, topic: str) -> str:
        """Generate content using Gemini API."""
        url = f"{self.api_url}?key={self.api_key}"
        
        prompt_template = random.choice(BUSINESS_VALUE_PROMPTS)
        prompt = prompt_template.format(topic=topic)
        
        prompt += f"""
        
        QUALITY REQUIREMENTS:
        1. Include specific, realistic metrics
        2. Focus on startup cost savings
        3. Add compelling CTAs for engagement
        4. Make content authentic and valuable
        5. Target startup founders and CTOs
        6. Emphasize ROI and efficiency
        
        Random seed: {random.randint(1000, 9999)}
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.8,
                "topK": 40,
                "topP": 0.9,
                "maxOutputTokens": 1000
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code}")
                return self._generate_fallback_content(topic)
            
            response_data = response.json()
            content = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            if len(content) > 2800:
                content = content[:2700] + "\n\n💬 What's your biggest challenge? Let's discuss!"
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return self._generate_fallback_content(topic)
    
    def _enhance_content(self, content: str, topic: str) -> str:
        """Enhance content with business elements."""
        enhanced = content.strip()
        
        # Add metrics if missing
        if not re.search(r'\d+%', enhanced):
            metric = random.choice(BUSINESS_METRICS)
            enhanced += f"\n\n📊 Real impact: {metric}"
        
        # Add CTA
        cta = random.choice(CONVERSION_CTAS)
        enhanced += f"\n\n{cta}"
        
        # Add hashtags
        hashtags = self._generate_hashtags(topic)
        enhanced += f"\n\n{hashtags}"
        
        return enhanced
    
    def _generate_hashtags(self, topic: str) -> str:
        """Generate relevant hashtags."""
        base_hashtags = ["#DevOps", "#StartupTech", "#CloudComputing", "#TechLeadership"]
        
        additional = []
        topic_lower = topic.lower()
        
        if "cost" in topic_lower or "optimization" in topic_lower:
            additional.extend(["#CostOptimization", "#CloudSavings"])
        if "security" in topic_lower:
            additional.extend(["#DevSecOps", "#Cybersecurity"])
        if "kubernetes" in topic_lower:
            additional.extend(["#Kubernetes", "#ContainerOrchestration"])
        if "startup" in topic_lower:
            additional.extend(["#StartupLife", "#ScaleUp"])
        
        all_hashtags = base_hashtags + additional[:4]
        return " ".join(all_hashtags)
    
    def _generate_fallback_content(self, topic: str) -> str:
        """Generate fallback content."""
        metric = random.choice(BUSINESS_METRICS)
        cta = random.choice(CONVERSION_CTAS)
        
        content = f"""🚀 {topic}: Game-Changer for Growing Startups

Tired of infrastructure costs spiraling out of control? 

Here's what proper {topic.lower()} can do:

✅ {metric}
✅ Eliminate manual deployment headaches  
✅ Scale without hiring DevOps engineers
✅ Sleep better with bulletproof systems
✅ Focus on features, not infrastructure

Most startups wait until it's too late. The best time to optimize was yesterday. The second best time is now.

{cta}

💬 What's your biggest infrastructure challenge? Share below!"""

        return content


class LinkedInHelper:
    """LinkedIn API helper."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile."""
        logger.info("Retrieving user profile...")
        url = "https://api.linkedin.com/v2/me"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Profile retrieval failed: {response.status_code}")
            
            profile_data = response.json()
            logger.info(f"Profile retrieved: {profile_data.get('id')}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Profile error: {e}")
            raise
    
    def post_content(self, person_id: str, organization_id: str, content: str) -> Dict[str, Any]:
        """Post content with fallback."""
        try:
            logger.info("Attempting organization post...")
            return self._post_as_organization(person_id, organization_id, content)
        except Exception as e:
            logger.warning(f"Organization post failed: {e}")
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
            raise Exception(f"Organization post failed: {response.status_code}")
        
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
            raise Exception(f"Personal post failed: {response.status_code}")
        
        logger.info("Successfully posted as person")
        return response.json() if response.text else {}


def main() -> None:
    """Main function."""
    try:
        # Get environment variables
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
        
        # Generate content
        logger.info("Generating business-focused content...")
        post_data = gemini.generate_business_post()
        
        # Log validation
        validation = post_data['validation']
        logger.info(f"Validation score: {validation['score']}/100")
        logger.info(f"Business value: {'✅' if validation['has_business_value'] else '❌'}")
        logger.info(f"Metrics: {'✅' if validation['has_metrics'] else '❌'}")
        logger.info(f"Engagement: {'✅' if validation['has_engagement'] else '❌'}")
        logger.info(f"CTAs: {'✅' if validation['has_cta'] else '❌'}")
        
        if validation['issues']:
            logger.warning(f"Issues: {', '.join(validation['issues'])}")
        
        # Debug mode
        if debug_mode:
            logger.info("DEBUG MODE: Preview only")
            print("\n" + "="*80)
            print(f"📝 TOPIC: {post_data['title']}")
            print("="*80)
            print(f"📊 SCORE: {validation['score']}/100")
            print(f"🔄 ATTEMPTS: {post_data['attempt']}")
            print("-"*80)
            print("📄 CONTENT:")
            print("-"*80)
            print(post_data['content'])
            print("\n" + "="*80)
            print("🔍 VALIDATION:")
            print(f"   Business Value: {'✅' if validation['has_business_value'] else '❌'}")
            print(f"   Metrics: {'✅' if validation['has_metrics'] else '❌'}")
            print(f"   Engagement: {'✅' if validation['has_engagement'] else '❌'}")
            print(f"   CTAs: {'✅' if validation['has_cta'] else '❌'}")
            if validation['issues']:
                print(f"   Issues: {', '.join(validation['issues'])}")
            print("="*80 + "\n")
            return
        
        # Quality check
        if validation['score'] < 60:
            logger.error(f"Quality too low (score: {validation['score']})")
            exit(1)
        
        # Post to LinkedIn
        linkedin = LinkedInHelper(access_token)
        profile = linkedin.get_user_profile()
        person_id = profile.get('id')
        
        if not person_id:
            logger.error("Failed to get person ID")
            exit(1)
        
        logger.info("Posting to LinkedIn...")
        response = linkedin.post_content(person_id, organization_id, post_data['content'])
        
        # Add to history
        history_manager.add_post(
            post_data['title'], 
            post_data['content'], 
            validation['score']
        )
        
        # GitHub Actions output
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write(f"post_title={post_data['title']}\n")
                f.write(f"post_status=success\n")
                f.write(f"post_quality={validation['score']}\n")
                f.write(f"validation_score={validation['score']}\n")
                f.write(f"has_business_value={validation['has_business_value']}\n")
                f.write(f"generation_attempts={post_data['attempt']}\n")
        
        logger.info("✅ LinkedIn automation completed!")
        logger.info(f"📝 Posted: {post_data['title']}")
        logger.info(f"📊 Quality Score: {validation['score']}/100")
    
    except Exception as e:
        logger.error(f"❌ Automation failed: {e}")
        
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write("post_status=failed\n")
                f.write(f"error_message={str(e)}\n")
        
        exit(1)


if __name__ == "__main__":
    main()
