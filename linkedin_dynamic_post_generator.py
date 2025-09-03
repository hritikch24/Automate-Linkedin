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

Optional environment variables (added):
- FREELANCER_MODE (default: "true") -> if "true", posts are framed to attract companies looking for freelance/consulting DevOps help
- SIMILARITY_THRESHOLD (default: "0.75") -> combined similarity threshold to reject content as too similar
- DIVERSITY_DAYS (default: "10") -> avoid repeating the same topic within N days
- MAX_EMOJIS (default: "6") -> cap emojis to keep it human, not spammy
- MAX_HASHTAGS (default: "8") -> limit hashtags
"""

import os
import json
import random
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
import hashlib
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -----------------------------
# Existing content definitions
# -----------------------------

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

# 🔹 ADD: Freelancer/Hiring-focused prompts (keeps originals; optionally preferred via FREELANCER_MODE)
FREELANCER_PROMPTS = [
    """Write a LinkedIn post about how {topic} helps startups avoid hiring a full-time DevOps team while still hitting enterprise-grade reliability.
    Frame it from the perspective of a freelance DevOps consultant who delivers outcomes quickly.

    Include:
    - Cost savings vs hiring full-time staff
    - Faster implementation speed
    - A mini case-style example with realistic numbers
    - Clear, hiring-focused CTA (fractional/freelance DevOps)

    Use emojis, concise paragraphs, and hashtags for #DevOps, #Cloud, #Startups, #Freelance.""",

    """Generate a LinkedIn post explaining how {topic} solves real startup pain points and how I provide this as a freelance DevOps consultant.

    Emphasize:
    - Cutting cloud bills with autoscaling & rightsizing
    - Speeding up releases with CI/CD improvements
    - Reducing security risks with DevSecOps automation
    - Scaling infra without scaling headcount

    End with CTAs such as:
    - "Need on-demand DevOps help? DM me."
    - "I help startups scale without hiring full-time. Let’s chat." """,

    """Create a hiring-focused LinkedIn post on {topic} with a strong opening hook.
    Audience: founders, CTOs, and hiring managers who need flexible DevOps help.

    Must include:
    - A hook that calls out a common pain (e.g., ballooning AWS bill, slow releases)
    - 3-4 bullet points on the approach
    - Concrete result metrics (time/cost/reliability)
    - A soft, professional CTA to work with a freelancer/consultant"""
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

# 🔹 ADD: Extra freelance-positioned CTAs (keeps originals; combined in pool)
FREELANCE_CTAS = [
    "💼 Need DevOps help without hiring full-time? DM me.",
    "🚀 Scaling your startup? I offer fractional DevOps expertise. Let’s connect.",
    "📊 Want infra savings and faster releases? Message me for freelance support.",
    "🔒 Security + scalability without full-time hires — DM me.",
    "⚡ I help startups cut costs & boost uptime as a consultant. Reach out!",
    "🛠️ Freelance DevOps support: cheaper than hiring, faster than waiting. DM me.",
    "💡 I’ve helped startups cut AWS bills 40% — let’s discuss yours.",
    "🎯 Looking for flexible DevOps support? Let’s connect."
]

# 🔹 ADD: Strong opening hooks to grab attention
OPENING_HOOKS = [
    "Why is your AWS bill bigger than your payroll? 🤔",
    "Scaling shouldn’t require doubling your DevOps headcount. 🚀",
    "Stop burning runway on idle cloud resources. 💸",
    "Your release pipeline shouldn’t be your bottleneck. ⛓️",
    "Security shouldn’t slow your team down. 🔒"
]

# 🔹 ADD: Mini case-studies for realism (lightweight, generic but believable)
MINI_CASE_STUDIES = [
    ("Seed-stage SaaS, 8 engineers",
     "Rightsized EC2, moved to GP3 volumes, and tightened autoscaling. "
     "Outcome: ~38% monthly savings and deploy time down from 22m → 9m."),
    ("Fintech MVP, pre-series A",
     "Introduced staged CI/CD with canary + feature flags. "
     "Outcome: 3x faster releases and rollback time cut to under 2 minutes."),
    ("B2B analytics startup",
     "Centralized logging + metrics with alert thresholds. "
     "Outcome: MTTR improved from ~90m to ~18m and 99.9% monthly uptime."),
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

# -----------------------------
# Existing validator
# -----------------------------

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

# -----------------------------
# Existing history manager
# -----------------------------

class PostHistoryManager:
    """Manages post history to avoid duplicates."""
    
    def __init__(self, history_file_path: str = None):
        if history_file_path:
            self.history_file = history_file_path
        else:
            history_dir = os.path.join(os.getcwd(), ".github", "post-history")
            os.makedirs(history_dir, exist_ok=True)
            self.history_file = os.path.join(history_dir, "linkedin-posts.log")
            # 🔹 ADD: a small state file for diversity/rotation
            self.state_file = os.path.join(history_dir, "state.json")
        
        self.post_history = self._load_history()
        # 🔹 ADD: load diversity state
        self.state = self._load_state()
    
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
    
    def _load_state(self) -> Dict[str, Any]:
        """🔹 ADD: Load diversity state."""
        try:
            if hasattr(self, "state_file") and os.path.exists(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
        return {"recent_topics": [], "recent_ctas": [], "recent_hooks": [], "recent_hashes": []}

    def _save_state(self) -> None:
        """🔹 ADD: Save diversity state."""
        try:
            if hasattr(self, "state_file"):
                os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
    def _normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def _cosine_sim(self, a: str, b: str) -> float:
        from collections import Counter
        ta, tb = Counter(self._tokenize(a)), Counter(self._tokenize(b))
        keys = set(ta) | set(tb)
        dot = sum(ta[k]*tb[k] for k in keys)
        na = sum(v*v for v in ta.values())**0.5
        nb = sum(v*v for v in tb.values())**0.5
        return dot / (na*nb) if na and nb else 0.0

    def _jaccard(self, a: str, b: str, n: int = 3) -> float:
        def ngrams(s, n):
            toks = self._tokenize(s)
            return set(tuple(toks[i:i+n]) for i in range(max(0, len(toks)-n+1)))
        A, B = ngrams(a, n), ngrams(b, n)
        return len(A & B) / len(A | B) if A and B else 0.0

    def is_similar_to_previous(self, content: str, threshold: float = 0.6) -> bool:
        """Check similarity to previous posts (existing)."""
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

    # 🔹 ADD: stronger similarity guard (cosine + Jaccard + SequenceMatcher)
    def is_too_similar(self, content: str, combo_threshold: float) -> bool:
        new = content
        for prev in self.post_history[-50:]:  # recent 50 only
            seq = SequenceMatcher(None, self._normalize(new), self._normalize(prev)).ratio()
            cos = self._cosine_sim(new, prev)
            jac = self._jaccard(new, prev, n=3)
            score = max(seq, (cos + jac) / 2.0)  # robust combo
            if score >= combo_threshold:
                logger.info(f"Similarity block: seq={seq:.2f} cos={cos:.2f} jac={jac:.2f} combo={score:.2f}")
                return True
        return False

    # 🔹 ADD: topic rotation (avoid repeating recently)
    def topic_allowed(self, topic: str, diversity_days: int = 10) -> bool:
        now = datetime.now()
        for entry in self.state.get("recent_topics", []):
            if entry.get("topic") == topic:
                ts = datetime.fromisoformat(entry.get("ts"))
                if (now - ts).days < diversity_days:
                    logger.info(f"Topic '{topic}' used { (now - ts).days } days ago; rotating.")
                    return False
        return True

    def remember_topic(self, topic: str) -> None:
        now = datetime.now().isoformat()
        topics = [e for e in self.state.get("recent_topics", []) if e.get("topic") != topic]
        topics.append({"topic": topic, "ts": now})
        # keep last 20
        self.state["recent_topics"] = topics[-20:]
        self._save_state()

    def remember_choice(self, key: str, value: str) -> None:
        arr = self.state.get(key, [])
        arr.append({"val": value, "ts": datetime.now().isoformat()})
        self.state[key] = arr[-30:]
        self._save_state()

    def remember_hash(self, content: str) -> None:
        h = hashlib.sha256(self._normalize(content).encode()).hexdigest()[:16]
        arr = self.state.get("recent_hashes", [])
        arr.append({"hash": h, "ts": datetime.now().isoformat()})
        self.state["recent_hashes"] = arr[-100:]
        self._save_state()

    def seen_hash(self, content: str) -> bool:
        h = hashlib.sha256(self._normalize(content).encode()).hexdigest()[:16]
        for obj in self.state.get("recent_hashes", []):
            if obj.get("hash") == h:
                logger.info("Exact/near-exact hash seen recently; regenerating.")
                return True
        return False
    
    def add_post(self, title: str, content: str, score: int) -> None:
        """Add post to history (existing)."""
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

# -----------------------------
# 🔹 ADD: Humanizer utilities
# -----------------------------

class Humanizer:
    """Make copy feel human, varied, and credible—without removing original content."""
    def __init__(self):
        try:
            self.max_emojis = int(os.environ.get("MAX_EMOJIS", "6"))
        except Exception:
            self.max_emojis = 6
        try:
            self.max_hashtags = int(os.environ.get("MAX_HASHTAGS", "8"))
        except Exception:
            self.max_hashtags = 8

    def limit_emojis(self, text: str) -> str:
        # emojis approximated as non-word unicode; conservative removal
        emojis = re.findall(r"[^\w\s,.\-/#@!?\(\)\'\"]", text)
        excess = max(0, len(emojis) - self.max_emojis)
        if excess > 0:
            text = re.sub(r"[^\w\s,.\-/#@!?\(\)\'\"]", "", text, count=excess)
        return text

    def limit_hashtags(self, text: str) -> str:
        tags = re.findall(r"(#\w+)", text, flags=re.I)
        if len(tags) > self.max_hashtags:
            keep = set(tags[:self.max_hashtags])
            parts = text.split()
            out = []
            for p in parts:
                if p.startswith("#") and p not in keep:
                    continue
                out.append(p)
            return " ".join(out)
        return text

    def add_mini_case(self, text: str) -> str:
        label, detail = random.choice(MINI_CASE_STUDIES)
        block = f"\n\n**Quick win from a recent engagement ({label}):**\n- {detail}"
        return text + block

    def soften_claims(self, text: str) -> str:
        # Add light caveat when strong % claims are present
        if re.search(r"\b\d{2,}%\b", text):
            text += "\n\n*Actual results depend on baseline and workload; I share assumptions and a quick plan upfront.*"
        return text

    def vary_opening(self, text: str, hook: Optional[str]) -> str:
        if not hook:
            return text
        # If text already has a bold/emoji heading, prepend a short one-liner instead of duplicating
        if re.match(r"^[^\w]*[A-Za-z0-9#]", text):
            return f"{hook}\n\n{text}"
        return text

    def human_tone(self, text: str) -> str:
        # Light contractions and more "I/we" voice
        text = re.sub(r"\bis not\b", "isn't", text, flags=re.I)
        text = re.sub(r"\bdo not\b", "don't", text, flags=re.I)
        text = re.sub(r"\bwe are\b", "we're", text, flags=re.I)
        text = re.sub(r"\bI am\b", "I'm", text, flags=re.I)
        # Remove repetitive filler phrases if duplicated
        text = re.sub(r"(Let’s connect\.)\s*\1+", r"\1", text, flags=re.I)
        return text

    def clean_spaces(self, text: str) -> str:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def finish(self, text: str) -> str:
        text = self.limit_emojis(text)
        text = self.limit_hashtags(text)
        text = self.clean_spaces(text)
        return text

# -----------------------------
# Existing Gemini generator
# -----------------------------

class GeminiContentGenerator:
    """Generates business-focused DevOps content."""
    
    def __init__(self, api_key: str, history_manager: PostHistoryManager):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.history_manager = history_manager
        self.validator = ContentValidator()
        # 🔹 ADD
        self.humanizer = Humanizer()
        try:
            self.sim_threshold = float(os.environ.get("SIMILARITY_THRESHOLD", "0.75"))
        except Exception:
            self.sim_threshold = 0.75
        try:
            self.diversity_days = int(os.environ.get("DIVERSITY_DAYS", "10"))
        except Exception:
            self.diversity_days = 10

    # 🔹 ADD: helpers for freelancer positioning
    def _opening_hook(self) -> str:
        try:
            return random.choice(OPENING_HOOKS)
        except Exception:
            return ""

    def _positioning_snippet(self) -> str:
        return ("If your startup needs DevOps outcomes without a full-time hire, "
                "I provide fractional/freelance support to cut costs, speed up releases, and boost reliability.")

    def _generate_hashtags_freelance(self, topic: str) -> str:
        base_hashtags = ["#DevOps", "#Cloud", "#Startups", "#Freelance", "#TechConsulting"]
        additional = []
        topic_lower = topic.lower()
        if "cost" in topic_lower or "optimization" in topic_lower:
            additional.extend(["#CloudSavings", "#CostOptimization"])
        if "security" in topic_lower:
            additional.extend(["#DevSecOps", "#Cybersecurity"])
        if "kubernetes" in topic_lower:
            additional.extend(["#Kubernetes", "#ContainerOrchestration"])
        if "startup" in topic_lower:
            additional.extend(["#ScaleUp", "#FractionalCTO"])
        all_hashtags = base_hashtags + additional[:4]
        # de-dupe & limit to 8
        seen, out = set(), []
        for t in all_hashtags:
            t = t if t.startswith("#") else f"#{t}"
            tl = t.lower()
            if tl not in seen:
                out.append(t)
                seen.add(tl)
            if len(out) >= 8:
                break
        return " ".join(out)

    def _enforce_length(self, s: str, limit: int = 3000) -> str:
        return s if len(s) <= limit else s[:limit-60].rstrip() + "\n\n…(truncated to fit)"

    # 🔹 ADD: helper to pick a topic respecting diversity window
    def _pick_diverse_topic(self) -> str:
        shuffled = BUSINESS_FOCUSED_TOPICS[:]
        random.shuffle(shuffled)
        for t in shuffled:
            if self.history_manager.topic_allowed(t, self.diversity_days):
                return t
        # fallback to any topic if all are blocked
        return random.choice(BUSINESS_FOCUSED_TOPICS)

    def generate_business_post(self, max_attempts: int = 5) -> Dict[str, Any]:
        """Generate a business-focused post."""
        for attempt in range(max_attempts):
            logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
            
            # 🔹 CHANGED by addition: topic selection with diversity window
            topic = self._pick_diverse_topic()
            content = self._generate_content(topic)
            enhanced_content = self._enhance_content(content, topic)

            # 🔹 ADD: humanize & add a mini case for realism
            if random.random() < 0.75:
                enhanced_content = self.humanizer.add_mini_case(enhanced_content)
            enhanced_content = self.humanizer.soften_claims(enhanced_content)
            enhanced_content = self.humanizer.human_tone(enhanced_content)
            enhanced_content = self.humanizer.finish(enhanced_content)
            
            # Validate content (existing)
            validation = self.validator.validate_content(topic, enhanced_content)
            
            # Check similarity (existing)
            if self.history_manager.is_similar_to_previous(enhanced_content):
                logger.info("Content too similar (legacy check), regenerating...")
                continue

            # 🔹 ADD: stronger similarity check & hash
            if self.history_manager.seen_hash(enhanced_content) or self.history_manager.is_too_similar(enhanced_content, self.sim_threshold):
                logger.info("Content too similar (enhanced check), regenerating...")
                continue
            
            if validation['is_valid'] and validation['score'] >= 75:
                logger.info(f"Quality content generated (score: {validation['score']})")
                # remember diversity signals now
                self.history_manager.remember_topic(topic)
                self.history_manager.remember_hash(enhanced_content)
                return {
                    'title': topic,
                    'content': enhanced_content,
                    'validation': validation,
                    'attempt': attempt + 1
                }
            else:
                logger.info(f"Quality insufficient (score: {validation['score']})")
        
        # Fallback (existing)
        logger.warning("Using fallback content")
        topic = self._pick_diverse_topic()
        fallback_content = self._generate_fallback_content(topic)
        enhanced_fallback = self._enhance_content(fallback_content, topic)
        # humanize fallback as well
        if random.random() < 0.75:
            enhanced_fallback = self.humanizer.add_mini_case(enhanced_fallback)
        enhanced_fallback = self.humanizer.soften_claims(enhanced_fallback)
        enhanced_fallback = self.humanizer.human_tone(enhanced_fallback)
        enhanced_fallback = self.humanizer.finish(enhanced_fallback)

        validation = self.validator.validate_content(topic, enhanced_fallback)
        self.history_manager.remember_topic(topic)
        self.history_manager.remember_hash(enhanced_fallback)
        
        return {
            'title': topic,
            'content': enhanced_fallback,
            'validation': validation,
            'attempt': max_attempts
        }
    
    def _generate_content(self, topic: str) -> str:
        """Generate content using Gemini API."""
        url = f"{self.api_url}?key={self.api_key}"
        
        prompt_template = random.choice(BUSINESS_VALUE_PROMPTS)  # (kept original line)
        # 🔹 ADD: prefer freelancer prompts if enabled (does not remove the original line)
        try:
            freelancer_mode = os.environ.get("FREELANCER_MODE", "true").lower() == "true"
        except Exception:
            freelancer_mode = True
        if freelancer_mode:
            try:
                prompt_template = random.choice(FREELANCER_PROMPTS)
            except Exception:
                pass
        
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
                "temperature": 0.85,
                "topK": 50,
                "topP": 0.95,
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
        """Enhance content with business elements and freelancer positioning (additive only)."""
        enhanced = content.strip()

        # 🔹 ADD: opening hook at the very top (human variation)
        hook = self._opening_hook()
        enhanced = self.humanizer.vary_opening(enhanced, hook)
        if hook:
            try:
                # remember hook to rotate
                self.history_manager.remember_choice("recent_hooks", hook)
            except Exception:
                pass

        # Add metrics if missing (existing behavior kept)
        if not re.search(r'\d+%', enhanced):
            metric = random.choice(BUSINESS_METRICS)
            enhanced += f"\n\n📊 Real impact: {metric}"

        # 🔹 ADD: freelance positioning paragraph before CTA
        try:
            freelancer_mode = os.environ.get("FREELANCER_MODE", "true").lower() == "true"
        except Exception:
            freelancer_mode = True
        if freelancer_mode:
            enhanced += f"\n\n{self._positioning_snippet()}"

        # Add CTA (now from combined pools; original CTAs preserved)
        try:
            cta_pool = CONVERSION_CTAS + FREELANCE_CTAS
        except Exception:
            cta_pool = CONVERSION_CTAS
        cta = random.choice(cta_pool)
        enhanced += f"\n\n{cta}"
        try:
            self.history_manager.remember_choice("recent_ctas", cta)
        except Exception:
            pass
        
        # Add hashtags (use freelancer-flavored set if enabled; original kept)
        if freelancer_mode:
            hashtags = self._generate_hashtags_freelance(topic)
        else:
            hashtags = self._generate_hashtags(topic)
        enhanced += f"\n\n{hashtags}"

        # 🔹 ADD: hard length cap to fit LinkedIn 3,000 chars
        enhanced = self._enforce_length(enhanced, limit=3000)
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
        cta_pool = CONVERSION_CTAS + FREELANCE_CTAS
        cta = random.choice(cta_pool)
        
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

# -----------------------------
# Existing LinkedIn helper
# -----------------------------

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

# -----------------------------
# Existing main
# -----------------------------

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
