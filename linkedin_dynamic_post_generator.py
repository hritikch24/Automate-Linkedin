#!/usr/bin/env python3
"""
Kubernetes Platform Feedback Post Generator with LinkedIn Publishing
------------------------------------------------------------------
Generates and publishes engaging LinkedIn posts to validate product ideas and gather community feedback.
Focuses on problem identification and solution validation rather than product promotion.

Required environment variables for LinkedIn posting:
- LINKEDIN_ACCESS_TOKEN: Your LinkedIn API access token
- Optional: LINKEDIN_ORGANIZATION_ID: Your LinkedIn organization/company ID

Usage:
    python feedback_post_generator.py
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

# Problem-focused post templates for validation
VALIDATION_POST_TEMPLATES = [
    {
        "hook": "Hey DevOps folks! 👋\n\nI've been thinking about a pain point that keeps coming up in conversations with fellow engineers...",
        "problem_intro": "**The Problem:** {main_problem} 😤",
        "pain_points": [
            "- {tool1} + {tool2} for {function1} 📊",
            "- {separate_tool} for {function2} 📝", 
            "- {additional_pain} 💰",
            "- Context switching kills productivity ⚡",
            "- {correlation_issue} 🔍"
        ],
        "solution_intro": "**What if there was a single dashboard where you could:**",
        "solution_points": [
            "✅ {feature1}",
            "✅ {feature2}", 
            "✅ {feature3}",
            "✅ {feature4}",
            "✅ {feature5}",
            "✅ {feature6}"
        ],
        "scenario_intro": "**Plus imagine this scenario:** 🤖",
        "engagement_questions": [
            "🔥 **Are you frustrated with {problem_area}?**",
            "💡 **Would you find value in a unified platform like this?**",
            "⚡ **What's your biggest {domain} challenge right now?**",
            "🎯 **What features would be absolute must-haves?**"
        ]
    },
    {
        "hook": "DevOps community! Need your honest thoughts... 🤔\n\nBeen chatting with teams about their {domain} setup and hearing similar frustrations:",
        "problem_intro": "**Current Reality:** {main_problem} 😩",
        "pain_points": [
            "→ {pain1} ⚠️",
            "→ {pain2} 🔄",
            "→ {pain3} 💸",
            "→ {pain4} ⏱️",
            "→ {pain5} 🚨"
        ],
        "solution_intro": "**Imagining a world where:**",
        "solution_points": [
            "🎯 {benefit1}",
            "⚡ {benefit2}",
            "🔍 {benefit3}",
            "💰 {benefit4}",
            "🤖 {benefit5}",
            "📊 {benefit6}"
        ],
        "scenario_intro": "**Real-world example:** 💭",
        "engagement_questions": [
            "🤷‍♂️ **Does this match your experience?**",
            "🔧 **How are you solving this today?**",
            "💯 **What would make the biggest impact for your team?**",
            "🚀 **Missing any critical capabilities in this vision?**"
        ]
    }
]

# K8s-specific problem scenarios
K8S_PROBLEM_SCENARIOS = {
    "observability_fragmentation": {
        "main_problem": "Managing Kubernetes clusters feels fragmented",
        "tool1": "Grafana + Prometheus",
        "tool2": "metrics",
        "function1": "metrics",
        "separate_tool": "ELK/Loki",
        "function2": "logs",
        "additional_pain": "Separate cost management tools",
        "correlation_issue": "Correlating issues across tools is manual and time-consuming",
        "problem_area": "tool sprawl in K8s observability",
        "domain": "K8s monitoring/cost",
        "features": [
            "Connect your K8s clusters instantly",
            "View pod logs with intelligent search & retention",
            "Monitor deployment/pod metrics in real-time", 
            "Get AI-powered troubleshooting suggestions",
            "Optimize costs with automated spot node management",
            "Receive smart recommendations for resource right-sizing"
        ],
        "scenario": [
            "- Your payment-service pod crashes",
            "- AI analyzes logs + metrics + events",
            "- Says: \"Memory limit too low, increase from 512Mi to 1Gi\"",
            "- One-click fix applied", 
            "- Problem solved in 30 seconds vs 30 minutes"
        ]
    },
    "cost_visibility": {
        "main_problem": "K8s cost optimization feels like shooting in the dark",
        "pain1": "No real-time visibility into pod-level costs",
        "pain2": "Resource waste is hidden until the bill arrives",
        "pain3": "Spot instance management is complex and risky",
        "pain4": "Right-sizing decisions are mostly guesswork",
        "pain5": "Cost allocation by team/project is nearly impossible",
        "problem_area": "K8s cost transparency",
        "domain": "Kubernetes cost management",
        "benefits": [
            "See real-time cost breakdown per pod/namespace",
            "Automated spot node lifecycle with zero downtime",
            "AI-powered right-sizing recommendations",
            "Waste detection with one-click optimization",
            "Cost attribution by team with detailed reports",
            "Predictive cost forecasting based on usage patterns"
        ],
        "scenario": [
            "- You notice your monthly K8s bill jumped 40%",
            "- Platform identifies: 15 over-provisioned deployments",
            "- Shows: $2,847 monthly savings with suggested changes",
            "- One-click applies optimizations safely",
            "- Next month: 35% cost reduction achieved"
        ]
    },
    "troubleshooting_complexity": {
        "main_problem": "Debugging K8s issues feels like detective work",
        "pain1": "Logs scattered across multiple namespaces and tools", 
        "pain2": "No context about what changed before the incident",
        "pain3": "Correlation between metrics and logs is manual",
        "pain4": "Root cause analysis takes hours or days",
        "pain5": "Team knowledge trapped in individual heads",
        "problem_area": "K8s troubleshooting complexity",
        "domain": "Kubernetes debugging",
        "benefits": [
            "AI-powered incident analysis with root cause suggestions",
            "Unified timeline showing logs + metrics + deployments",
            "Pattern recognition from historical incidents",
            "Natural language query interface for cluster data",
            "Automated runbook suggestions based on symptoms",
            "Team knowledge base built from resolved issues"
        ],
        "scenario": [
            "- \"Why is checkout service responding slowly?\"",
            "- AI finds: Database connection pool exhausted",
            "- Shows: 3 similar incidents last month",
            "- Suggests: Connection pool tuning + HPA adjustment",
            "- Provides: Step-by-step remediation guide"
        ]
    }
}

# Engagement elements specific to validation posts
VALIDATION_ENGAGEMENT_ELEMENTS = [
    "Really appreciate any insights you can share! 🙏",
    "Genuinely curious about your experiences and whether this resonates! 💭",
    "Would love to hear your take on this! 🤝",
    "Your insights would be incredibly valuable! ⭐",
    "Excited to learn from the community's experience! 🚀"
]

COMMUNITY_ASKS = [
    "**Drop a comment below with:**\n- Your current {domain} stack\n- Biggest pain points you face\n- Whether this type of solution would help your team",
    "**I'd love to know:**\n- How you're handling this today\n- What workarounds you've built\n- If this matches your experience",
    "**Quick ask:**\n- What's your current setup?\n- Where do you feel the most pain?\n- Would this approach solve real problems for you?",
    "**Help me understand:**\n- Your biggest {domain} headaches\n- Tools you love vs. hate\n- What would make your day-to-day easier"
]

# Validation-focused hashtags
VALIDATION_HASHTAGS = [
    "#DevOps", "#Kubernetes", "#CloudNative", "#Observability", "#TechTrends", 
    "#SRE", "#Monitoring", "#CostOptimization", "#AI", "#Innovation", 
    "#TechLeadership", "#CloudComputing", "#Automation", "#DigitalTransformation",
    "#CommunityFeedback", "#ProductValidation", "#TechSurvey"
]

class FeedbackPostGenerator:
    """Generates LinkedIn posts focused on gathering community feedback and validation."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the feedback post generator.
        
        Args:
            api_key: Optional Gemini API key for enhanced content generation
        """
        self.api_key = api_key
        if api_key:
            self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    def generate_validation_post(self, problem_type: str = None) -> Dict[str, str]:
        """
        Generate a validation-focused LinkedIn post.
        
        Args:
            problem_type: Specific problem type to focus on
            
        Returns:
            Dictionary with title and content
        """
        # Select problem scenario
        if problem_type and problem_type in K8S_PROBLEM_SCENARIOS:
            scenario = K8S_PROBLEM_SCENARIOS[problem_type]
        else:
            scenario = random.choice(list(K8S_PROBLEM_SCENARIOS.values()))
        
        # Select post template
        template = random.choice(VALIDATION_POST_TEMPLATES)
        
        # Build the post content
        content_parts = []
        
        # Hook
        content_parts.append(template["hook"].format(**scenario))
        content_parts.append("")
        
        # Problem statement
        content_parts.append(template["problem_intro"].format(**scenario))
        
        # Pain points
        if "pain_points" in template:
            for pain_point in template["pain_points"]:
                content_parts.append(pain_point.format(**scenario))
        content_parts.append("")
        
        # Solution vision
        content_parts.append(template["solution_intro"])
        
        # Solution features
        if "solution_points" in template:
            features = scenario.get("features", [])
            for i, solution_point in enumerate(template["solution_points"]):
                if i < len(features):
                    content_parts.append(solution_point.format(
                        feature1=features[0] if len(features) > 0 else "Advanced feature",
                        feature2=features[1] if len(features) > 1 else "Smart automation",
                        feature3=features[2] if len(features) > 2 else "Intelligent insights",
                        feature4=features[3] if len(features) > 3 else "Cost optimization",
                        feature5=features[4] if len(features) > 4 else "AI-powered analysis",
                        feature6=features[5] if len(features) > 5 else "Seamless integration"
                    ))
        content_parts.append("")
        
        # Scenario example
        content_parts.append(template["scenario_intro"])
        if "scenario" in scenario:
            for step in scenario["scenario"]:
                content_parts.append(step)
        content_parts.append("")
        
        # Engagement questions
        content_parts.append("**My questions for you:**")
        for question in template["engagement_questions"]:
            content_parts.append(question.format(**scenario))
        content_parts.append("")
        
        # Add community engagement
        community_context = "I'm genuinely curious about your experiences and whether this resonates with the community. The Kubernetes ecosystem is amazing but sometimes feels like you need a PhD to get proper observability 😅"
        content_parts.append(community_context)
        content_parts.append("")
        
        # Community ask
        community_ask = random.choice(COMMUNITY_ASKS).format(**scenario)
        content_parts.append(community_ask)
        content_parts.append("")
        
        # Appreciation
        appreciation = random.choice(VALIDATION_ENGAGEMENT_ELEMENTS)
        content_parts.append(appreciation)
        content_parts.append("")
        
        # Hashtags
        selected_hashtags = random.sample(VALIDATION_HASHTAGS, random.randint(10, 14))
        hashtag_string = " ".join(selected_hashtags)
        content_parts.append(hashtag_string)
        
        # Join all parts
        full_content = "\n".join(content_parts)
        
        # Generate title
        title = f"K8s {problem_type.replace('_', ' ').title()} - Community Feedback"
        
        return {
            "title": title,
            "content": full_content,
            "problem_type": problem_type or "general_observability"
        }
    
    def generate_enhanced_post_with_ai(self, problem_type: str = None) -> Dict[str, str]:
        """
        Generate an enhanced post using AI for more natural language.
        
        Args:
            problem_type: Specific problem type to focus on
            
        Returns:
            Dictionary with title and content
        """
        if not self.api_key:
            logger.warning("No API key provided, falling back to template-based generation")
            return self.generate_validation_post(problem_type)
        
        # Get base scenario
        if problem_type and problem_type in K8S_PROBLEM_SCENARIOS:
            scenario = K8S_PROBLEM_SCENARIOS[problem_type]
        else:
            problem_type = random.choice(list(K8S_PROBLEM_SCENARIOS.keys()))
            scenario = K8S_PROBLEM_SCENARIOS[problem_type]
        
        # Create AI prompt for natural content generation
        prompt = f"""
        Generate an engaging LinkedIn post to validate a Kubernetes platform idea with the DevOps community.

        CONTEXT:
        - You're exploring the problem: {scenario['main_problem']}
        - You want genuine community feedback, not to sell anything
        - The post should feel authentic and curiosity-driven
        - You're a DevOps engineer talking to fellow engineers

        POST STRUCTURE:
        1. Friendly hook acknowledging a shared pain point
        2. Clearly articulate the specific problem with examples
        3. Present a vision for a potential solution (without claiming you're building it)
        4. Include a concrete scenario showing the value
        5. Ask specific questions to gather feedback
        6. End with genuine appreciation for community input

        KEY ELEMENTS TO INCLUDE:
        - Problem: {scenario['main_problem']}
        - Current pain points around Kubernetes observability/cost management
        - Vision for unified platform with these capabilities: {', '.join(scenario.get('features', ['intelligent monitoring', 'cost optimization', 'AI assistance']))}
        - Specific scenario showing 30-second vs 30-minute problem resolution
        - Questions about their current stack, pain points, and feature priorities

        TONE:
        - Authentic and curious, not salesy
        - Technical but approachable
        - Community-focused ("fellow engineers", "your experience")
        - Humble and genuinely seeking input

        ENGAGEMENT:
        - Use emojis strategically for visual appeal
        - Include specific calls-to-action for comments
        - Ask about their current tools and challenges
        - Request feature prioritization feedback

        Make it feel like a genuine conversation starter, not a product pitch. Focus on problem validation and community insights.
        
        Length: 15-20 lines with good visual breaks.
        """
        
        try:
            url = f"{self.api_url}?key={self.api_key}"
            
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
                    "temperature": 0.8,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1200
                }
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                generated_content = response_data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Add hashtags
                hashtags = random.sample(VALIDATION_HASHTAGS, 12)
                hashtag_string = " ".join(hashtags)
                
                full_content = f"{generated_content.strip()}\n\n{hashtag_string}"
                
                return {
                    "title": f"K8s {problem_type.replace('_', ' ').title()} Validation Post",
                    "content": full_content,
                    "problem_type": problem_type,
                    "generation_method": "ai_enhanced"
                }
            else:
                logger.warning(f"AI generation failed, falling back to templates: {response.status_code}")
                return self.generate_validation_post(problem_type)
                
        except Exception as e:
            logger.error(f"Error in AI generation: {e}")
            return self.generate_validation_post(problem_type)
    
    def generate_multiple_variations(self, problem_type: str = None, count: int = 3) -> List[Dict[str, str]]:
        """
        Generate multiple variations of validation posts.
        
        Args:
            problem_type: Specific problem type to focus on
            count: Number of variations to generate
            
        Returns:
            List of post dictionaries
        """
        variations = []
        
        for i in range(count):
            if self.api_key and i % 2 == 0:  # Mix AI and template-based
                post = self.generate_enhanced_post_with_ai(problem_type)
            else:
                post = self.generate_validation_post(problem_type)
            
            post["variation_number"] = i + 1
            variations.append(post)
            
        return variations

class LinkedInHelper:
    """Helper class for LinkedIn API operations - using exact same structure as working code."""
    
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

def main():
    """Main function to generate and optionally publish validation posts."""
    try:
        # Get environment variables - using exact same variable names as working code
        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        organization_id = os.environ.get("LINKEDIN_ORGANIZATION_ID")
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        if not access_token:
            logger.warning("LINKEDIN_ACCESS_TOKEN not set. Will generate post without publishing.")
        
        # Make sure organization_id is just the ID number, not the full URN
        # Strip the "urn:li:organization:" prefix if it's included
        if organization_id and organization_id.startswith("urn:li:organization:"):
            organization_id = organization_id.replace("urn:li:organization:", "")
        
        # Initialize generator
        if gemini_api_key:
            logger.info("Using AI-enhanced generation with Gemini API")
        else:
            logger.info("Using template-based generation (set GEMINI_API_KEY for AI enhancement)")
        
        generator = FeedbackPostGenerator(gemini_api_key)
        
        # Check for specific problem type
        problem_type = os.environ.get("PROBLEM_TYPE")
        
        # Generate posts
        if os.environ.get("GENERATE_MULTIPLE") == "true":
            # Generate multiple variations
            variations = generator.generate_multiple_variations(problem_type, count=3)
            
            print(f"\n{'='*60}")
            print("GENERATED MULTIPLE VARIATIONS")
            print('='*60)
            
            for i, post in enumerate(variations, 1):
                print(f"\nVARIATION {i}: {post['title']}")
                print(f"Problem Type: {post['problem_type']}")
                print(f"Method: {post.get('generation_method', 'template_based')}")
                print('-'*40)
                print(post['content'])
                print('-'*40)
            
            # Ask user which variation to post (if LinkedIn credentials available)
            if access_token:
                try:
                    choice = input(f"\nWhich variation would you like to post to LinkedIn? (1-{len(variations)} or 'none'): ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(variations):
                        post = variations[int(choice) - 1]
                        print(f"\nSelected variation {choice} for posting...")
                    elif choice.lower() != 'none':
                        print("Invalid choice, skipping LinkedIn posting.")
                        return
                    else:
                        print("Skipping LinkedIn posting.")
                        return
                except KeyboardInterrupt:
                    print("\nSkipping LinkedIn posting.")
                    return
            else:
                print("\nTo post to LinkedIn, set LINKEDIN_ACCESS_TOKEN environment variable.")
                return
        else:
            # Generate single post
            if gemini_api_key:
                post = generator.generate_enhanced_post_with_ai(problem_type)
            else:
                post = generator.generate_validation_post(problem_type)
            
            print(f"\n{'='*60}")
            print(f"VALIDATION POST: {post['title']}")
            print(f"Problem Type: {post['problem_type']}")
            print(f"Method: {post.get('generation_method', 'template_based')}")
            print('='*60)
            print(post['content'])
            print('='*60)
        
        # Post to LinkedIn if credentials are available - using exact same flow as working code
        if access_token:
            # Debug output mode (if environment variable is set)
            if os.environ.get("DEBUG_MODE") == "true":
                logger.info("DEBUG MODE: Printing post without publishing")
                print("\n" + "="*60)
                print(f"Topic: {post['title']}")
                print("-"*60)
                print(post['content'])
                print("\n" + "="*60)
                print("DEBUG MODE: Set DEBUG_MODE=false to actually post")
                print("="*60 + "\n")
                return
            
            # Confirm posting unless AUTO_POST is set
            if os.environ.get("AUTO_POST") != "true":
                try:
                    confirm = input(f"\nPost this to LinkedIn? (y/N): ").strip().lower()
                    if confirm not in ['y', 'yes']:
                        print("Posting cancelled.")
                        return
                except KeyboardInterrupt:
                    print("\nPosting cancelled.")
                    return
            
            # Initialize LinkedIn helper - using exact same class name as working code
            linkedin = LinkedInHelper(access_token)
            
            # Get user profile
            profile = linkedin.get_user_profile()
            person_id = profile.get('id')
            
            if not person_id:
                logger.error("Failed to retrieve person ID from profile.")
                return
            
            # Try to post as the organization first, then fallback to personal - exact same logic
            try:
                logger.info("Attempting to post as organization...")
                linkedin.post_as_organization(person_id, organization_id, post["content"])
                logger.info("Successfully posted as organization!")
                
                # Output for GitHub Actions
                if os.environ.get("GITHUB_ACTIONS") == "true":
                    with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                        f.write(f"post_title={post['title']}\n")
                        f.write(f"post_status=success\n")
                        f.write(f"post_method=organization\n")
                        f.write(f"problem_type={post['problem_type']}\n")
                
            except Exception as e:
                logger.warning(f"Failed to post as organization: {e}")
                logger.info("Falling back to posting as personal profile...")
                
                # If posting as organization fails, fall back to posting as person
                try:
                    linkedin.post_as_person(person_id, post["content"])
                    logger.info("Successfully posted as personal profile!")
                    
                    # Output for GitHub Actions
                    if os.environ.get("GITHUB_ACTIONS") == "true":
                        with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                            f.write(f"post_title={post['title']}\n")
                            f.write(f"post_status=success\n")
                            f.write(f"post_method=personal\n")
                            f.write(f"problem_type={post['problem_type']}\n")
                            
                except Exception as e2:
                    logger.error(f"Failed to post as personal profile: {e2}")
                    
                    # Output for GitHub Actions  
                    if os.environ.get("GITHUB_ACTIONS") == "true":
                        with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                            f.write("post_status=failed\n")
                            f.write(f"error={str(e2)}\n")
                    return
        
        logger.info("LinkedIn post automation completed successfully with validation focus.")
        
    except Exception as e:
        logger.error(f"Error during LinkedIn post automation: {e}")
        # Output for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                f.write("post_status=failed\n")
                f.write(f"error={str(e)}\n")
    
    # Output usage instructions
    print(f"\n{'='*60}")
    print("VALIDATION POST USAGE:")
    print("1. Monitor LinkedIn comments and engagement")
    print("2. Also post on Reddit (r/devops, r/kubernetes)")
    print("3. Share in DevOps Discord/Slack communities") 
    print("4. Look for feedback patterns:")
    print("   - Problem validation (do people relate?)")
    print("   - Solution interest (would they use it?)")
    print("   - Feature priorities (what matters most?)")
    print("   - Current tool frustrations")
    print("   - Willingness to pay indicators")
    print("\nEnvironment Variables (same as working automation):")
    print("- LINKEDIN_ACCESS_TOKEN: Enable LinkedIn posting")
    print("- LINKEDIN_ORGANIZATION_ID: Post as company (optional)")
    print("- GEMINI_API_KEY: Enable AI-enhanced generation")
    print("- PROBLEM_TYPE: observability_fragmentation, cost_visibility, troubleshooting_complexity")
    print("- GENERATE_MULTIPLE: true (generate 3 variations)")
    print("- DEBUG_MODE: true (generate but don't post)")
    print("- AUTO_POST: true (skip confirmation prompt)")
    print('='*60)

if __name__ == "__main__":
    main()
