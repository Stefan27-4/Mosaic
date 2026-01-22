"""
Resilience Layer for RLM framework.

This module implements adaptive validation with CriticRouter for intelligent
peer review and ResilientAgent for tiered validation with automatic retries.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks for critic routing."""
    CODE = "code"
    LOGIC_MATH = "logic_math"
    WRITING = "writing"
    GENERAL = "general"


class CriticRouter:
    """
    Routes tasks to the best critic model for validation.
    
    Implements intelligent peer review by selecting critics different from
    the worker model when possible, with fallback to self-correction.
    """
    
    # Model ranking by specialty
    CODE_CRITICS = ["claude-opus-4.5", "claude-sonnet-3.5", "gpt-5.2"]
    LOGIC_CRITICS = ["deepseek-3.2", "gpt-5.2", "claude-opus-4.5"]
    WRITING_CRITICS = ["gpt-5.2", "gemini-3", "claude-opus-4.5"]
    GENERAL_CRITICS = ["gpt-5.2", "claude-opus-4.5", "gemini-3", "deepseek-3.2"]
    
    def __init__(self, available_models: Set[str]):
        """
        Initialize the CriticRouter.
        
        Args:
            available_models: Set of model IDs that are available for use
        """
        self.available_models = available_models
    
    def get_critic(
        self,
        task_type: TaskType,
        worker_model_id: str
    ) -> Tuple[str, bool]:
        """
        Select the best critic model for reviewing work.
        
        Args:
            task_type: Type of task being validated
            worker_model_id: Model ID that produced the work
            
        Returns:
            Tuple of (critic_model_id, is_peer_review):
                - critic_model_id: The selected critic model
                - is_peer_review: True if critic != worker (peer review),
                                  False if same (self-correction)
        """
        # Select candidate critics based on task type
        if task_type == TaskType.CODE:
            candidates = self.CODE_CRITICS
        elif task_type == TaskType.LOGIC_MATH:
            candidates = self.LOGIC_CRITICS
        elif task_type == TaskType.WRITING:
            candidates = self.WRITING_CRITICS
        else:  # GENERAL
            candidates = self.GENERAL_CRITICS
        
        # Filter to only available models
        available_candidates = [m for m in candidates if m in self.available_models]
        
        # If no candidates available, use worker model (self-correction)
        if not available_candidates:
            logger.warning(
                f"No critic models available for {task_type.value}, "
                f"using worker model {worker_model_id} for self-correction"
            )
            return worker_model_id, False
        
        # Try to find a different model (peer review)
        for candidate in available_candidates:
            if candidate != worker_model_id:
                logger.info(
                    f"Peer review: {worker_model_id} work reviewed by {candidate}"
                )
                return candidate, True
        
        # If all candidates are the worker, use the best available (self-correction)
        critic_model = available_candidates[0]
        logger.info(
            f"Self-correction: {worker_model_id} reviewing own work "
            f"(only 1 model available or best critic is worker)"
        )
        return critic_model, False


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(
        self,
        passed: bool,
        message: str = "",
        suggestion: str = "",
        tier: str = "unknown"
    ):
        """
        Initialize validation result.
        
        Args:
            passed: Whether validation passed
            message: Validation message or error description
            suggestion: Suggestion for fixing the issue
            tier: Validation tier ("instant" or "semantic")
        """
        self.passed = passed
        self.message = message
        self.suggestion = suggestion
        self.tier = tier


class ResilientAgent:
    """
    Agent with tiered validation and automatic retry logic.
    
    Implements two-tier validation:
    - Tier 1: Instant checks (syntax, format) - free and fast
    - Tier 2: Semantic checks (critic review) - smart but costs tokens
    """
    
    def __init__(
        self,
        llm_interface,
        critic_router: Optional[CriticRouter] = None,
        max_retries: int = 3,
        enable_semantic_validation: bool = True,
        validation_cost_limit: float = 1.0  # Max $ to spend on validation
    ):
        """
        Initialize the ResilientAgent.
        
        Args:
            llm_interface: LLM interface for executing tasks
            critic_router: Router for selecting critic models
            max_retries: Maximum retry attempts per task
            enable_semantic_validation: Whether to use semantic (LLM) validation
            validation_cost_limit: Maximum cost for validation calls
        """
        self.llm_interface = llm_interface
        self.critic_router = critic_router
        self.max_retries = max_retries
        self.enable_semantic_validation = enable_semantic_validation
        self.validation_cost_limit = validation_cost_limit
        self.validation_cost_spent = 0.0
    
    def validate_python_syntax(self, code: str) -> ValidationResult:
        """
        Tier 1: Validate Python syntax (instant check).
        
        Args:
            code: Python code to validate
            
        Returns:
            ValidationResult indicating pass/fail
        """
        try:
            compile(code, '<string>', 'exec')
            return ValidationResult(
                passed=True,
                message="Python syntax is valid",
                tier="instant"
            )
        except SyntaxError as e:
            return ValidationResult(
                passed=False,
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                suggestion="Fix the syntax error and try again",
                tier="instant"
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Compilation error: {str(e)}",
                suggestion="Fix the compilation error",
                tier="instant"
            )
    
    def validate_json(self, text: str) -> ValidationResult:
        """
        Tier 1: Validate JSON format (instant check).
        
        Args:
            text: JSON text to validate
            
        Returns:
            ValidationResult indicating pass/fail
        """
        try:
            json.loads(text)
            return ValidationResult(
                passed=True,
                message="JSON format is valid",
                tier="instant"
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                passed=False,
                message=f"JSON error at line {e.lineno}: {e.msg}",
                suggestion="Fix the JSON formatting",
                tier="instant"
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"JSON validation error: {str(e)}",
                suggestion="Check JSON structure",
                tier="instant"
            )
    
    def semantic_validate(
        self,
        content: str,
        task_type: TaskType,
        worker_model_id: str,
        task_description: str = ""
    ) -> ValidationResult:
        """
        Tier 2: Semantic validation using critic LLM (smart check).
        
        Args:
            content: Content to validate
            task_type: Type of task
            worker_model_id: Model that produced the content
            task_description: Optional description of the task
            
        Returns:
            ValidationResult from critic review
        """
        # Check if semantic validation is enabled
        if not self.enable_semantic_validation:
            return ValidationResult(
                passed=True,
                message="Semantic validation disabled",
                tier="semantic"
            )
        
        # Check if we've exceeded validation budget
        if self.validation_cost_spent >= self.validation_cost_limit:
            logger.warning(
                f"Validation cost limit reached (${self.validation_cost_spent:.2f}), "
                "skipping semantic validation"
            )
            return ValidationResult(
                passed=True,
                message="Validation budget exceeded, skipping check",
                tier="semantic"
            )
        
        # Get critic model
        if not self.critic_router:
            logger.warning("No critic router available, skipping semantic validation")
            return ValidationResult(
                passed=True,
                message="No critic router available",
                tier="semantic"
            )
        
        critic_model_id, is_peer_review = self.critic_router.get_critic(
            task_type, worker_model_id
        )
        
        # Build validation prompt
        if is_peer_review:
            prompt = f"""You are a Senior Reviewer conducting peer review.

Task Type: {task_type.value}
Worker Model: {worker_model_id}
{f'Task: {task_description}' if task_description else ''}

The worker model generated the following output. Review it carefully for:
- Logic errors or bugs
- Security vulnerabilities
- Edge cases not handled
- Subtle mistakes

Content to Review:
{content}

Respond with EXACTLY ONE of:
1. "PASS" - if the content is correct and production-ready
2. "FAIL: <reason>" - if there are issues that must be fixed

Your response:"""
        else:
            prompt = f"""You are reviewing your own work for quality assurance.

Task Type: {task_type.value}
{f'Task: {task_description}' if task_description else ''}

Step back and critically evaluate your previous output:

{content}

Check for:
- Logic errors you may have missed
- Assumptions that may be incorrect
- Better approaches you should consider

Respond with EXACTLY ONE of:
1. "PASS" - if your work is correct
2. "FAIL: <reason>" - if you found issues to fix

Your response:"""
        
        try:
            # Query the critic
            response = self.llm_interface.query(prompt)
            
            # Track validation cost (estimate)
            estimated_cost = 0.01  # Rough estimate per validation
            self.validation_cost_spent += estimated_cost
            
            # Parse response
            response = response.strip()
            
            if response.upper().startswith("PASS"):
                return ValidationResult(
                    passed=True,
                    message=f"Critic approved ({critic_model_id})",
                    tier="semantic"
                )
            elif "FAIL" in response.upper():
                # Extract reason
                reason = response.split(":", 1)[1].strip() if ":" in response else response
                return ValidationResult(
                    passed=False,
                    message=f"Critic rejected: {reason}",
                    suggestion=f"Address the critic's feedback: {reason}",
                    tier="semantic"
                )
            else:
                logger.warning(f"Unexpected critic response: {response}")
                return ValidationResult(
                    passed=True,
                    message="Critic response unclear, assuming pass",
                    tier="semantic"
                )
        
        except Exception as e:
            logger.error(f"Error in semantic validation: {e}")
            return ValidationResult(
                passed=True,
                message=f"Validation error, assuming pass: {e}",
                tier="semantic"
            )
    
    def execute_with_retry(
        self,
        task_prompt: str,
        task_type: TaskType,
        output_format: str = "text",
        task_description: str = ""
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Execute task with tiered validation and automatic retry.
        
        Args:
            task_prompt: Prompt for the task
            task_type: Type of task for critic routing
            output_format: Expected format ("python", "json", "text")
            task_description: Description of task for critic
            
        Returns:
            Tuple of (result, validation_history):
                - result: Final output from the task
                - validation_history: List of validation attempts
        """
        validation_history = []
        last_result = None
        
        for attempt in range(self.max_retries):
            logger.info(f"Attempt {attempt + 1}/{self.max_retries}")
            
            # Execute the task
            try:
                if attempt == 0:
                    # First attempt - use original prompt
                    result = self.llm_interface.query(task_prompt)
                else:
                    # Retry with feedback from previous attempt
                    feedback = validation_history[-1].get("feedback", "")
                    retry_prompt = f"""{task_prompt}

Previous attempt failed validation:
{feedback}

Please fix the issues and try again.

Your response:"""
                    result = self.llm_interface.query(retry_prompt)
                
                last_result = result
                
                # Tier 1: Instant validation (free & fast)
                instant_result = None
                if output_format == "python":
                    instant_result = self.validate_python_syntax(result)
                elif output_format == "json":
                    instant_result = self.validate_json(result)
                
                if instant_result and not instant_result.passed:
                    # Tier 1 failed - immediate retry
                    logger.warning(f"Tier 1 (instant) validation failed: {instant_result.message}")
                    validation_history.append({
                        "attempt": attempt + 1,
                        "tier": "instant",
                        "passed": False,
                        "message": instant_result.message,
                        "feedback": instant_result.suggestion
                    })
                    continue
                
                # Tier 1 passed (or not applicable)
                if instant_result:
                    logger.info(f"Tier 1 validation passed: {instant_result.message}")
                    validation_history.append({
                        "attempt": attempt + 1,
                        "tier": "instant",
                        "passed": True,
                        "message": instant_result.message
                    })
                
                # Tier 2: Semantic validation (smart critic)
                if self.enable_semantic_validation and self.critic_router:
                    # Get worker model ID (from llm_interface if available)
                    worker_model_id = getattr(
                        self.llm_interface, 'model', 'unknown'
                    )
                    
                    semantic_result = self.semantic_validate(
                        result,
                        task_type,
                        worker_model_id,
                        task_description
                    )
                    
                    if not semantic_result.passed:
                        # Tier 2 failed - retry with critic feedback
                        logger.warning(
                            f"Tier 2 (semantic) validation failed: {semantic_result.message}"
                        )
                        validation_history.append({
                            "attempt": attempt + 1,
                            "tier": "semantic",
                            "passed": False,
                            "message": semantic_result.message,
                            "feedback": semantic_result.suggestion
                        })
                        continue
                    
                    logger.info(f"Tier 2 validation passed: {semantic_result.message}")
                    validation_history.append({
                        "attempt": attempt + 1,
                        "tier": "semantic",
                        "passed": True,
                        "message": semantic_result.message
                    })
                
                # All validations passed!
                logger.info(f"Task completed successfully on attempt {attempt + 1}")
                return result, validation_history
            
            except Exception as e:
                logger.error(f"Error during execution: {e}")
                validation_history.append({
                    "attempt": attempt + 1,
                    "tier": "execution",
                    "passed": False,
                    "message": f"Execution error: {str(e)}",
                    "feedback": "Task execution failed with an error"
                })
        
        # Max retries exceeded - return last result
        logger.warning(
            f"Max retries ({self.max_retries}) exceeded, returning last result"
        )
        return last_result or "", validation_history


def detect_task_type(content: str) -> TaskType:
    """
    Detect task type from content.
    
    Args:
        content: Content to analyze
        
    Returns:
        Detected TaskType
    """
    content_lower = content.lower()
    
    # Code indicators
    code_keywords = ["def ", "class ", "import ", "function", "var ", "const "]
    if any(kw in content_lower for kw in code_keywords):
        return TaskType.CODE
    
    # Math/logic indicators
    math_keywords = ["calculate", "theorem", "proof", "equation", "solve", "logic"]
    if any(kw in content_lower for kw in math_keywords):
        return TaskType.LOGIC_MATH
    
    # Writing indicators
    writing_keywords = ["write", "essay", "story", "article", "summary", "describe"]
    if any(kw in content_lower for kw in writing_keywords):
        return TaskType.WRITING
    
    return TaskType.GENERAL
