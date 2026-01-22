"""
Heuristic Routing Engine for RLM framework.

This module implements a deterministic, keyword-density scoring algorithm
that analyzes text chunks and assigns them to optimal AI models based on
their "Feature Fingerprints."
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional, Set
from collections import Counter

# Set up logging
logger = logging.getLogger(__name__)


class ProfileConfig:
    """Configuration for a specialist profile."""
    
    def __init__(self, name: str, model_id: str, keywords: Dict[str, float]):
        """
        Initialize a profile configuration.
        
        Args:
            name: Human-readable name of the profile
            model_id: Model identifier to route to
            keywords: Dictionary mapping keywords to their weights
        """
        self.name = name
        self.model_id = model_id
        self.keywords = keywords


# Profile A: The "Architect" (Maps to Claude Opus 4.5)
PROFILE_ARCHITECT = ProfileConfig(
    name="Architect",
    model_id="claude-opus-4.5",
    keywords={
        # Coding keywords (strong indicators)
        "class": 2.0,
        "def": 2.0,
        "import": 2.0,
        "return": 1.5,
        "async": 2.0,
        "await": 2.0,
        "interface": 2.0,
        "implements": 2.0,
        "public": 1.5,
        "static": 1.5,
        "void": 1.5,
        "function": 1.5,
        "method": 1.5,
        # Legal keywords (strong indicators)
        "section": 1.5,
        "clause": 2.0,
        "agreement": 2.0,
        "party": 1.5,
        "hereby": 2.0,
        "terms": 1.5,
        "conditions": 1.5,
        "contract": 2.0,
        "legal": 1.5,
        # Structural indicators (medium strength)
        "architecture": 1.5,
        "refactor": 2.0,
        "multi-file": 1.5,
    }
)

# Profile B: The "Project Manager" (Maps to GPT-5.2)
PROFILE_PROJECT_MANAGER = ProfileConfig(
    name="Project Manager",
    model_id="gpt-5.2",
    keywords={
        # Database keywords (strong indicators)
        "select": 2.0,
        "insert": 2.0,
        "update": 2.0,
        "delete": 2.0,
        "join": 2.0,
        "union": 2.0,
        "primary": 1.5,
        "foreign": 1.5,
        "key": 1.0,
        "schema": 2.0,
        "table": 1.5,
        "database": 1.5,
        "sql": 2.0,
        # Data format keywords (strong indicators)
        "json": 2.0,
        "yaml": 2.0,
        "xml": 2.0,
        # Planning keywords (medium strength)
        "step": 1.5,
        "phase": 1.5,
        "milestone": 1.5,
        "deliverable": 1.5,
        "workflow": 1.5,
        "roadmap": 1.5,
        "plan": 1.0,
        "schedule": 1.5,
        "timeline": 1.5,
    }
)

# Profile C: The "Creative Director" (Maps to Gemini 3)
PROFILE_CREATIVE_DIRECTOR = ProfileConfig(
    name="Creative Director",
    model_id="gemini-3",
    keywords={
        # Narrative keywords (medium strength)
        "story": 1.5,
        "character": 1.5,
        "plot": 1.5,
        "setting": 1.0,
        "theme": 1.0,
        "narrative": 2.0,
        "chapter": 1.5,
        "scene": 1.0,
        # Visual keywords (strong indicators)
        "image": 1.5,
        "video": 1.5,
        "slide": 1.5,
        "presentation": 1.5,
        "deck": 1.5,
        "graph": 1.5,
        "chart": 1.5,
        "visual": 1.5,
        "graphic": 1.5,
        # Research keywords (medium strength)
        "study": 1.5,
        "findings": 1.5,
        "abstract": 2.0,
        "conclusion": 1.5,
        "literature": 1.5,
        "review": 1.0,
        "research": 1.5,
        "analysis": 1.0,
        "summarize": 1.5,
        "summary": 1.5,
    }
)

# Profile D: The "News Analyst" (Maps to Grok 4.1)
PROFILE_NEWS_ANALYST = ProfileConfig(
    name="News Analyst",
    model_id="grok-4.1",
    keywords={
        # Temporal markers (strong indicators)
        "today": 2.0,
        "yesterday": 2.0,
        "current": 1.5,
        "breaking": 2.0,
        "live": 2.0,
        "update": 1.5,
        "2026": 2.0,
        "2025": 1.5,
        "latest": 1.5,
        "recent": 1.5,
        "now": 1.5,
        # Social signals (strong indicators)
        "twitter": 2.0,
        "x.com": 2.0,
        "trend": 1.5,
        "viral": 2.0,
        "sentiment": 1.5,
        "social": 1.0,
        "media": 1.0,
        "hashtag": 2.0,
        "tweet": 2.0,
        # Conversational/edgy tone (medium strength)
        "roast": 2.0,
        "joke": 1.5,
        "meme": 1.5,
        "news": 1.5,
        "event": 1.0,
    }
)

# Profile E: The "Efficiency Expert" (Maps to DeepSeek 3.2)
PROFILE_EFFICIENCY_EXPERT = ProfileConfig(
    name="Efficiency Expert",
    model_id="deepseek-3.2",
    keywords={
        # Mathematical notation (strong indicators)
        "latex": 2.0,
        "equation": 2.0,
        "theorem": 2.0,
        "proof": 2.0,
        "calculate": 1.5,
        "solve": 1.5,
        "integral": 2.0,
        "derivative": 2.0,
        "formula": 1.5,
        "mathematics": 1.5,
        "math": 1.5,
        # Logic keywords (medium strength)
        "logic": 1.5,
        "puzzle": 1.5,
        "syllogism": 2.0,
        "if": 0.5,  # Very common word, low weight
        "then": 0.5,
        "proof": 2.0,
    }
)

# All profiles in order
ALL_PROFILES = [
    PROFILE_ARCHITECT,
    PROFILE_PROJECT_MANAGER,
    PROFILE_CREATIVE_DIRECTOR,
    PROFILE_NEWS_ANALYST,
    PROFILE_EFFICIENCY_EXPERT,
]

# Fallback chains for each profile
# If the ideal model is unavailable, try the next in the chain
FALLBACK_CHAINS = {
    "claude-opus-4.5": ["claude-opus-4.5", "gpt-5.2", "deepseek-3.2"],  # Architect -> Project Manager -> Efficiency
    "gpt-5.2": ["gpt-5.2", "deepseek-3.2"],  # Project Manager -> Efficiency
    "gemini-3": ["gemini-3", "gpt-5.2", "deepseek-3.2"],  # Creative -> Project Manager -> Efficiency
    "grok-4.1": ["grok-4.1", "gpt-5.2", "deepseek-3.2"],  # News -> Project Manager -> Efficiency
    "deepseek-3.2": ["deepseek-3.2", "gpt-5.2"],  # Efficiency -> Project Manager
}


def get_available_models(model_map: Dict[str, Any]) -> Set[str]:
    """
    Detect which models are actually available in the model map.
    
    Args:
        model_map: Dictionary mapping model IDs to LLM instances
        
    Returns:
        Set of available model IDs
    """
    return set(model_map.keys())


def classify_chunk(
    text: str,
    available_models: Optional[Set[str]] = None,
    threshold: float = 0.3
) -> Tuple[str, Dict[str, Any]]:
    """
    Classify a text chunk and route to the best available model.
    
    This is the main routing function with single-key bypass optimization
    and fallback chain support.
    
    Args:
        text: Text chunk to classify
        available_models: Set of available model IDs. If None, assumes all models available.
        threshold: Confidence threshold for routing decision
        
    Returns:
        Tuple of (model_id, details):
            - model_id: Selected model ID
            - details: Dictionary with routing details (scores, fallback_used, etc.)
    """
    # Step 0: Single-Key Bypass
    if available_models is not None and len(available_models) == 1:
        single_model = list(available_models)[0]
        logger.info(f"Single-key bypass: Only one model available ({single_model}), skipping scoring")
        return single_model, {
            "bypass": True,
            "reason": "single_key_bypass",
            "available_models": len(available_models)
        }
    
    # Step 1: Run scoring to find ideal model
    engine = HeuristicRoutingEngine(threshold=threshold)
    result = engine.route_with_details(text)
    ideal_model = result['model_id']
    
    # If no available_models specified, assume all are available
    if available_models is None:
        return ideal_model, {
            "bypass": False,
            "ideal_model": ideal_model,
            "confidence": result['confidence'],
            "profile": result['profile_name'],
            "fallback_used": False
        }
    
    # Step 2: Check if ideal model is available
    if ideal_model in available_models:
        return ideal_model, {
            "bypass": False,
            "ideal_model": ideal_model,
            "confidence": result['confidence'],
            "profile": result['profile_name'],
            "fallback_used": False
        }
    
    # Step 3: Iterate through fallback chain
    fallback_chain = FALLBACK_CHAINS.get(ideal_model, [ideal_model, "deepseek-3.2"])
    
    for fallback_model in fallback_chain:
        if fallback_model in available_models:
            # Log warning about fallback
            logger.warning(
                f"{result['profile_name']} task detected, but {ideal_model} missing. "
                f"Re-routing to {fallback_model}."
            )
            return fallback_model, {
                "bypass": False,
                "ideal_model": ideal_model,
                "actual_model": fallback_model,
                "confidence": result['confidence'],
                "profile": result['profile_name'],
                "fallback_used": True,
                "fallback_chain": fallback_chain
            }
    
    # Step 4: If no fallback available, return deepseek-3.2 (default)
    logger.error(
        f"No models available in fallback chain for {ideal_model}. "
        f"Defaulting to deepseek-3.2"
    )
    return "deepseek-3.2", {
        "bypass": False,
        "ideal_model": ideal_model,
        "actual_model": "deepseek-3.2",
        "confidence": result['confidence'],
        "profile": result['profile_name'],
        "fallback_used": True,
        "fallback_chain": fallback_chain,
        "error": "no_models_in_chain_available"
    }



class HeuristicRoutingEngine:
    """
    Deterministic keyword-density scoring algorithm for routing text to optimal models.
    
    Analyzes text chunks and assigns them to the best AI model based on
    Feature Fingerprints using keyword matching and scoring.
    """
    
    def __init__(
        self,
        profiles: List[ProfileConfig] = None,
        threshold: float = 0.3,
        default_model_id: str = "deepseek-3.2"
    ):
        """
        Initialize the routing engine.
        
        Args:
            profiles: List of profile configurations (uses defaults if None)
            threshold: Minimum confidence score to accept a routing decision
            default_model_id: Model to use when confidence is below threshold
        """
        self.profiles = profiles if profiles is not None else ALL_PROFILES
        self.threshold = threshold
        self.default_model_id = default_model_id
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into lowercase tokens for analysis.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of lowercase tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Split on whitespace and punctuation, keeping alphanumeric and hyphens
        tokens = re.findall(r'\b[\w-]+\b', text)
        
        return tokens
    
    def calculate_score(self, text: str, profile: ProfileConfig) -> float:
        """
        Calculate confidence score for a given profile.
        
        Args:
            text: Input text chunk
            profile: Profile configuration to score against
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        tokens = self.tokenize(text)
        
        if not tokens:
            return 0.0
        
        # Count token occurrences
        token_counts = Counter(tokens)
        
        # Calculate weighted score
        total_score = 0.0
        total_weight = 0.0
        
        for keyword, weight in profile.keywords.items():
            keyword_lower = keyword.lower()
            if keyword_lower in token_counts:
                count = token_counts[keyword_lower]
                total_score += count * weight
                total_weight += weight
        
        # Normalize by total possible weight and text length
        if total_weight > 0:
            # Normalize by keyword density in text
            density = total_score / len(tokens)
            # Cap at 1.0
            return min(1.0, density * 10)  # Scale factor to reach 1.0 more easily
        
        return 0.0
    
    def route(self, text_chunk: str) -> Tuple[str, Dict[str, float]]:
        """
        Route a text chunk to the optimal model.
        
        Runs the scoring algorithm for all profiles and returns the model_id
        of the winner. If confidence is below threshold, returns the default
        efficiency model.
        
        Args:
            text_chunk: Input text to route
            
        Returns:
            Tuple of (model_id, scores_dict):
                - model_id: The selected model identifier
                - scores_dict: Dictionary of profile names to their scores
        """
        # Calculate scores for all profiles
        scores = {}
        for profile in self.profiles:
            score = self.calculate_score(text_chunk, profile)
            scores[profile.name] = score
        
        # Find the highest scoring profile
        if not scores:
            return self.default_model_id, {}
        
        max_profile_name = max(scores, key=scores.get)
        max_score = scores[max_profile_name]
        
        # Get the corresponding profile
        winning_profile = next(
            (p for p in self.profiles if p.name == max_profile_name),
            None
        )
        
        # Check threshold
        if max_score < self.threshold or winning_profile is None:
            # Fallback to default efficiency model
            return self.default_model_id, scores
        
        return winning_profile.model_id, scores
    
    def route_with_details(self, text_chunk: str) -> Dict[str, Any]:
        """
        Route a text chunk and return detailed routing information.
        
        Args:
            text_chunk: Input text to route
            
        Returns:
            Dictionary containing:
                - model_id: Selected model
                - profile_name: Name of winning profile (or "Default")
                - confidence: Confidence score
                - all_scores: All profile scores
                - is_fallback: Whether default fallback was used
        """
        model_id, scores = self.route(text_chunk)
        
        # Determine if fallback was used
        is_fallback = model_id == self.default_model_id
        
        if not scores:
            return {
                "model_id": model_id,
                "profile_name": "Default",
                "confidence": 0.0,
                "all_scores": {},
                "is_fallback": True
            }
        
        max_profile_name = max(scores, key=scores.get)
        max_score = scores[max_profile_name]
        
        # If fallback was used, set profile name accordingly
        if is_fallback and max_score < self.threshold:
            profile_name = "Default (below threshold)"
        elif is_fallback:
            profile_name = "Default"
        else:
            profile_name = max_profile_name
        
        return {
            "model_id": model_id,
            "profile_name": profile_name,
            "confidence": max_score,
            "all_scores": scores,
            "is_fallback": is_fallback
        }


# Convenience function for simple routing
def route_text(text_chunk: str, threshold: float = 0.3) -> str:
    """
    Route a text chunk to the optimal model (simple interface).
    
    Args:
        text_chunk: Input text to route
        threshold: Minimum confidence threshold (default: 0.3)
        
    Returns:
        Model identifier string
    """
    engine = HeuristicRoutingEngine(threshold=threshold)
    model_id, _ = engine.route(text_chunk)
    return model_id
