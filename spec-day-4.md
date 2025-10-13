# Crypto News & Sentiment Agent - Day 4 Specification

## Project Overview
Implement Amazon Bedrock Guardrails for content safety, build evaluation frameworks for sentiment accuracy, and add production resilience patterns including retry logic, circuit breakers, and fallback mechanisms.

## Why This Approach?
Day 4 focuses on **production safety, quality assurance, and resilience** that are critical for deploying AI agents in production:

### Guardrails & Safety
- **Amazon Bedrock Guardrails**: Built-in content filtering and topic detection
- **Prompt Injection Protection**: Validate inputs to prevent malicious prompts
- **Content Filtering**: Block sensitive topics and harmful content automatically
- **Topic Detection**: Ensure content stays within crypto/finance domain

### Evaluation & Quality
- **Gold Dataset**: Curated labeled examples for sentiment accuracy testing
- **Automated Evaluation**: Continuous monitoring of model performance
- **Confusion Matrix**: Track classification errors and model drift
- **A/B Testing**: Compare different models and prompts

### Production Resilience
- **Retry Logic**: Exponential backoff with jitter for transient failures
- **Circuit Breakers**: Prevent cascading failures in distributed systems
- **Fallback Mechanisms**: Graceful degradation when primary services fail
- **Cost Optimization**: Monitor and control Bedrock API spending

## Prerequisites: Bedrock Guardrails Access

**⚠️ IMPORTANT: Enable Amazon Bedrock Guardrails before proceeding**

### Required AWS Permissions:
1. **Bedrock Guardrails Access**: Enable Guardrails in Bedrock console
2. **IAM Permissions**: Add `bedrock:CreateGuardrail`, `bedrock:ApplyGuardrail` permissions
3. **Model Access**: Ensure Claude Sonnet and Haiku access for fallback strategies

### Bedrock Guardrails Requirements:
- **Content Filters**: Configure hate, insults, sexual, violence filters
- **Topic Filters**: Define allowed/denied topics (crypto, finance allowed)
- **Word Filters**: Custom profanity and sensitive term blocklists
- **PII Detection**: Redact personal information in user inputs

### Setup Steps:
1. Enable Bedrock Guardrails in AWS Console
2. Create guardrail configuration for crypto domain
3. Test guardrail with sample inputs
4. Configure cost alerts for Guardrail usage

**Note**: Without Guardrails access, content filtering will be disabled.

## Day 4 Requirements

### Core Functionality
- **Bedrock Guardrails Integration**: Implement content filtering and topic detection
- **Prompt Injection Protection**: Validate and sanitize user inputs
- **Evaluation Framework**: Build gold dataset and automated testing
- **Sentiment Accuracy Metrics**: Track precision, recall, F1 score
- **Retry Logic**: Implement exponential backoff for API failures
- **Circuit Breaker Pattern**: Prevent cascading failures
- **Fallback Mechanisms**: Multi-model strategy (Claude Sonnet → Haiku)
- **Cost Monitoring**: Track and alert on Bedrock API costs

### Technical Stack
- **Guardrails**: Amazon Bedrock Guardrails
- **Testing**: pytest + pytest-asyncio for async tests
- **Metrics**: Custom evaluation metrics (precision, recall, F1)
- **Resilience**: tenacity library for retry logic
- **Monitoring**: CloudWatch + Grafana for cost tracking
- **Validation**: pydantic for input validation

## Amazon Bedrock Guardrails Integration

### Guardrail Configuration

#### Create Guardrail via AWS Console or CLI
```python
# Example guardrail configuration
guardrail_config = {
    "name": "crypto-sentiment-guardrail",
    "description": "Content filtering for crypto news sentiment analysis",
    "contentPolicyConfig": {
        "filtersConfig": [
            {
                "type": "HATE",
                "inputStrength": "HIGH",
                "outputStrength": "HIGH"
            },
            {
                "type": "INSULTS",
                "inputStrength": "MEDIUM",
                "outputStrength": "MEDIUM"
            },
            {
                "type": "SEXUAL",
                "inputStrength": "HIGH",
                "outputStrength": "HIGH"
            },
            {
                "type": "VIOLENCE",
                "inputStrength": "MEDIUM",
                "outputStrength": "MEDIUM"
            }
        ]
    },
    "topicPolicyConfig": {
        "topicsConfig": [
            {
                "name": "crypto-finance",
                "definition": "Cryptocurrency, blockchain, digital assets, financial markets",
                "examples": [
                    "Bitcoin price prediction",
                    "Ethereum market analysis",
                    "DeFi trends"
                ],
                "type": "ALLOW"
            },
            {
                "name": "political-extremism",
                "definition": "Extreme political views, conspiracy theories",
                "examples": [
                    "Government manipulation theories",
                    "Extreme political propaganda"
                ],
                "type": "DENY"
            }
        ]
    },
    "wordPolicyConfig": {
        "wordsConfig": [
            {
                "text": "scam"
            },
            {
                "text": "pump and dump"
            }
        ],
        "managedWordListsConfig": [
            {
                "type": "PROFANITY"
            }
        ]
    },
    "sensitiveInformationPolicyConfig": {
        "piiEntitiesConfig": [
            {
                "type": "EMAIL",
                "action": "ANONYMIZE"
            },
            {
                "type": "PHONE",
                "action": "ANONYMIZE"
            },
            {
                "type": "CREDIT_DEBIT_CARD_NUMBER",
                "action": "BLOCK"
            }
        ]
    }
}
```

#### Guardrail Service Implementation
```python
# src/services/guardrail_service.py
import boto3
import json
import logging
from typing import Dict, Any, Optional
from decouple import config

logger = logging.getLogger(__name__)

class GuardrailService:
    """Service for applying Amazon Bedrock Guardrails to content."""

    def __init__(self):
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=config('AWS_BEDROCK_REGION', default='us-east-1')
        )
        self.guardrail_id = config('BEDROCK_GUARDRAIL_ID')
        self.guardrail_version = config('BEDROCK_GUARDRAIL_VERSION', default='DRAFT')

    def validate_input(self, text: str) -> Dict[str, Any]:
        """
        Validate input text against guardrails.

        Args:
            text: Input text to validate

        Returns:
            Dict with validation result and details
        """
        try:
            response = self.bedrock_client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source='INPUT',
                content=[{
                    'text': {
                        'text': text
                    }
                }]
            )

            action = response.get('action', 'NONE')

            if action == 'GUARDRAIL_INTERVENED':
                return {
                    'valid': False,
                    'action': action,
                    'assessments': response.get('assessments', []),
                    'message': 'Content blocked by guardrails'
                }

            return {
                'valid': True,
                'action': action,
                'assessments': response.get('assessments', [])
            }

        except Exception as e:
            logger.error(f"Guardrail validation error: {e}")
            # Fail open - allow content if guardrail service fails
            return {
                'valid': True,
                'action': 'ERROR',
                'error': str(e),
                'message': 'Guardrail validation failed, allowing content'
            }

    def validate_output(self, text: str) -> Dict[str, Any]:
        """
        Validate model output against guardrails.

        Args:
            text: Model output to validate

        Returns:
            Dict with validation result and details
        """
        try:
            response = self.bedrock_client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source='OUTPUT',
                content=[{
                    'text': {
                        'text': text
                    }
                }]
            )

            action = response.get('action', 'NONE')

            if action == 'GUARDRAIL_INTERVENED':
                # Return sanitized message
                return {
                    'valid': False,
                    'action': action,
                    'assessments': response.get('assessments', []),
                    'sanitized_output': "I cannot provide a response due to content policy restrictions."
                }

            return {
                'valid': True,
                'action': action,
                'output': text
            }

        except Exception as e:
            logger.error(f"Output guardrail validation error: {e}")
            # Fail open - return original output if validation fails
            return {
                'valid': True,
                'action': 'ERROR',
                'output': text,
                'error': str(e)
            }
```

### Enhanced Sentiment Analysis with Guardrails
```python
# src/services/sentiment_analyzer.py (updated)
from src.services.guardrail_service import GuardrailService

class SentimentAnalyzer:
    def __init__(self):
        # ... existing initialization
        self.guardrail_service = GuardrailService()

    def analyze_sentiment_with_guardrails(self, article_content: str) -> Dict[str, Any]:
        """
        Analyze sentiment with guardrail validation.

        Args:
            article_content: News article text

        Returns:
            Dict with sentiment and guardrail status
        """
        # Validate input
        input_validation = self.guardrail_service.validate_input(article_content)

        if not input_validation['valid']:
            logger.warning(f"Input blocked by guardrails: {input_validation['message']}")
            return {
                'sentiment': 'neutral',
                'confidence_score': 0.0,
                'guardrail_blocked': True,
                'reason': input_validation['message']
            }

        # Generate sentiment with Bedrock
        sentiment_response = self.analyze_sentiment(article_content)

        # Validate output
        output_text = json.dumps(sentiment_response)
        output_validation = self.guardrail_service.validate_output(output_text)

        if not output_validation['valid']:
            logger.warning(f"Output blocked by guardrails")
            return {
                'sentiment': 'neutral',
                'confidence_score': 0.0,
                'guardrail_blocked': True,
                'reason': 'Model output blocked by content policy'
            }

        return {
            **sentiment_response,
            'guardrail_validated': True
        }
```

## Evaluation Framework

### Gold Dataset Structure
```python
# evaluation/gold_dataset.json
{
    "version": "1.0",
    "created_at": "2025-10-13",
    "description": "Gold standard dataset for crypto sentiment evaluation",
    "samples": [
        {
            "id": 1,
            "text": "Bitcoin surges to new all-time high as institutional adoption accelerates",
            "expected_sentiment": "bullish",
            "expected_confidence": 0.9,
            "tokens": ["BTC"],
            "source": "manual_curation",
            "notes": "Clear positive sentiment with institutional backing"
        },
        {
            "id": 2,
            "text": "Ethereum crashes 20% amid regulatory concerns and network congestion",
            "expected_sentiment": "bearish",
            "expected_confidence": 0.85,
            "tokens": ["ETH"],
            "source": "manual_curation",
            "notes": "Strong negative sentiment with multiple bearish factors"
        },
        {
            "id": 3,
            "text": "Solana network experiences minor downtime, quickly restored",
            "expected_sentiment": "neutral",
            "expected_confidence": 0.7,
            "tokens": ["SOL"],
            "source": "manual_curation",
            "notes": "Mixed signals - negative event but quick resolution"
        }
        // ... 97 more samples for 100 total
    ]
}
```

### Evaluation Service
```python
# src/services/evaluation_service.py
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
import numpy as np

logger = logging.getLogger(__name__)

class EvaluationService:
    """Service for evaluating sentiment analysis performance."""

    def __init__(self, gold_dataset_path: str = "evaluation/gold_dataset.json"):
        self.gold_dataset_path = Path(gold_dataset_path)
        self.gold_samples = self._load_gold_dataset()

    def _load_gold_dataset(self) -> List[Dict[str, Any]]:
        """Load gold standard dataset."""
        try:
            with open(self.gold_dataset_path, 'r') as f:
                data = json.load(f)
                return data.get('samples', [])
        except FileNotFoundError:
            logger.warning(f"Gold dataset not found at {self.gold_dataset_path}")
            return []

    def evaluate_model(self, sentiment_analyzer) -> Dict[str, Any]:
        """
        Evaluate sentiment analyzer against gold dataset.

        Args:
            sentiment_analyzer: SentimentAnalyzer instance

        Returns:
            Dict with evaluation metrics
        """
        if not self.gold_samples:
            return {
                'error': 'No gold dataset available',
                'metrics': {}
            }

        predictions = []
        expected = []
        results = []

        for sample in self.gold_samples:
            try:
                # Get prediction
                result = sentiment_analyzer.analyze_sentiment(sample['text'])
                predicted_sentiment = result.get('sentiment', 'neutral')

                predictions.append(predicted_sentiment)
                expected.append(sample['expected_sentiment'])

                results.append({
                    'id': sample['id'],
                    'text': sample['text'][:100] + '...',
                    'expected': sample['expected_sentiment'],
                    'predicted': predicted_sentiment,
                    'confidence': result.get('confidence_score', 0.0),
                    'correct': predicted_sentiment == sample['expected_sentiment']
                })

            except Exception as e:
                logger.error(f"Evaluation error for sample {sample['id']}: {e}")
                predictions.append('neutral')
                expected.append(sample['expected_sentiment'])

        # Calculate metrics
        labels = ['bullish', 'neutral', 'bearish']
        precision, recall, f1, support = precision_recall_fscore_support(
            expected,
            predictions,
            labels=labels,
            average='weighted',
            zero_division=0
        )

        # Per-class metrics
        per_class_precision, per_class_recall, per_class_f1, per_class_support = \
            precision_recall_fscore_support(
                expected,
                predictions,
                labels=labels,
                average=None,
                zero_division=0
            )

        # Confusion matrix
        cm = confusion_matrix(expected, predictions, labels=labels)

        # Accuracy
        accuracy = np.mean([r['correct'] for r in results])

        return {
            'total_samples': len(self.gold_samples),
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'per_class_metrics': {
                labels[i]: {
                    'precision': float(per_class_precision[i]),
                    'recall': float(per_class_recall[i]),
                    'f1_score': float(per_class_f1[i]),
                    'support': int(per_class_support[i])
                }
                for i in range(len(labels))
            },
            'confusion_matrix': {
                'labels': labels,
                'matrix': cm.tolist()
            },
            'sample_results': results[:10]  # First 10 for inspection
        }
```

### Evaluation API Endpoint
```python
# src/main.py (add this endpoint)
from src.services.evaluation_service import EvaluationService

evaluation_service = EvaluationService()

@app.post("/api/evaluate/sentiment/")
@limiter.limit("5/hour")  # Expensive operation
async def evaluate_sentiment_model(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    Evaluate sentiment analysis model against gold dataset.

    Returns accuracy, precision, recall, F1 score, and confusion matrix.
    """
    try:
        sentiment_analyzer = SentimentAnalyzer()
        results = evaluation_service.evaluate_model(sentiment_analyzer)

        return {
            'status': 'completed',
            'metrics': results,
            'model_id': sentiment_analyzer.model_id
        }
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        ) from None
```

## Resilience Patterns

### Retry Logic with Exponential Backoff
```python
# src/utils/retry.py
import time
import random
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retry logic with exponential backoff and jitter.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1

                    if retry_count > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (exponential_base ** (retry_count - 1)), max_delay)

                    # Add jitter
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Retry {retry_count}/{max_retries} for {func.__name__} "
                        f"after {delay:.2f}s. Error: {e}"
                    )

                    time.sleep(delay)

            return None

        return wrapper
    return decorator

# Usage example
from botocore.exceptions import ClientError

class SentimentAnalyzer:
    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        exceptions=(ClientError,)
    )
    def _call_bedrock_api(self, prompt: str) -> dict:
        """Call Bedrock API with retry logic."""
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.3
            })
        )
        return json.loads(response['body'].read())
```

### Circuit Breaker Pattern
```python
# src/utils/circuit_breaker.py
import time
import logging
from enum import Enum
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker entering HALF_OPEN state for {func.__name__}")
            else:
                raise Exception(
                    f"Circuit breaker OPEN for {func.__name__}. "
                    f"Will retry after {self.recovery_timeout}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker reset to CLOSED state")

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker OPEN after {self.failure_count} failures. "
                f"Will attempt recovery after {self.recovery_timeout}s"
            )

# Decorator version
def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception
):
    """Circuit breaker decorator."""
    breaker = CircuitBreaker(failure_threshold, recovery_timeout, expected_exception)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

# Usage example
from botocore.exceptions import ClientError

class BedrockService:
    @circuit_breaker(
        failure_threshold=5,
        recovery_timeout=60.0,
        expected_exception=ClientError
    )
    def invoke_model(self, prompt: str) -> dict:
        """Invoke Bedrock model with circuit breaker protection."""
        # ... API call logic
        pass
```

### Multi-Model Fallback Strategy
```python
# src/services/sentiment_analyzer.py (enhanced)
from src.utils.retry import retry_with_backoff
from src.utils.circuit_breaker import circuit_breaker

class SentimentAnalyzer:
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

        # Primary model (Claude Sonnet - more accurate)
        self.primary_model_id = config(
            'BEDROCK_PRIMARY_MODEL_ID',
            default='anthropic.claude-3-sonnet-20240229-v1:0'
        )

        # Fallback model (Claude Haiku - faster/cheaper)
        self.fallback_model_id = config(
            'BEDROCK_FALLBACK_MODEL_ID',
            default='anthropic.claude-3-haiku-20240307-v1:0'
        )

        self.use_fallback = False

    @retry_with_backoff(max_retries=3)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60.0)
    def analyze_sentiment_with_fallback(self, article_content: str) -> Dict[str, Any]:
        """
        Analyze sentiment with automatic fallback to cheaper model.

        Args:
            article_content: News article text

        Returns:
            Dict with sentiment analysis results
        """
        model_id = self.fallback_model_id if self.use_fallback else self.primary_model_id

        try:
            result = self._invoke_bedrock(article_content, model_id)

            # Reset fallback flag on success with primary model
            if not self.use_fallback:
                self.use_fallback = False

            return result

        except Exception as e:
            logger.error(f"Primary model ({model_id}) failed: {e}")

            # Try fallback model if primary fails
            if not self.use_fallback:
                logger.info(f"Attempting fallback to {self.fallback_model_id}")
                self.use_fallback = True
                return self._invoke_bedrock(article_content, self.fallback_model_id)

            raise

    def _invoke_bedrock(self, content: str, model_id: str) -> Dict[str, Any]:
        """Invoke Bedrock model for sentiment analysis."""
        prompt = f"""Analyze the sentiment of this crypto news article.
        Respond with JSON: {{"sentiment": "bullish|neutral|bearish", "confidence": 0.0-1.0}}

        Article: {content}
        """

        response = self.bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.3
            })
        )

        result = json.loads(response['body'].read())
        content_text = result['content'][0]['text']

        # Parse JSON response
        sentiment_data = json.loads(content_text)

        return {
            'sentiment': sentiment_data['sentiment'],
            'confidence_score': sentiment_data['confidence'],
            'model_used': model_id
        }
```

## Cost Monitoring

### Cost Tracking Service
```python
# src/services/cost_tracker.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Bedrock pricing (as of 2025, adjust as needed)
BEDROCK_PRICING = {
    'anthropic.claude-3-sonnet-20240229-v1:0': {
        'input_per_1k_tokens': 0.003,
        'output_per_1k_tokens': 0.015
    },
    'anthropic.claude-3-haiku-20240307-v1:0': {
        'input_per_1k_tokens': 0.00025,
        'output_per_1k_tokens': 0.00125
    },
    'amazon.titan-embed-text-v2:0': {
        'per_1k_tokens': 0.0001
    }
}

class CostTracker:
    """Track and monitor Bedrock API costs."""

    @staticmethod
    def calculate_sentiment_cost(
        input_tokens: int,
        output_tokens: int,
        model_id: str
    ) -> float:
        """Calculate cost for sentiment analysis call."""
        pricing = BEDROCK_PRICING.get(model_id, {})

        input_cost = (input_tokens / 1000) * pricing.get('input_per_1k_tokens', 0)
        output_cost = (output_tokens / 1000) * pricing.get('output_per_1k_tokens', 0)

        return input_cost + output_cost

    @staticmethod
    def calculate_embedding_cost(tokens: int, model_id: str) -> float:
        """Calculate cost for embedding generation."""
        pricing = BEDROCK_PRICING.get(model_id, {})
        return (tokens / 1000) * pricing.get('per_1k_tokens', 0)

    @staticmethod
    def get_daily_costs(db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily cost breakdown for the last N days.

        Args:
            db: Database session
            days: Number of days to retrieve

        Returns:
            List of daily cost summaries
        """
        # This requires a cost_tracking table (implement as needed)
        # For now, return estimated costs based on API calls

        # Query API call logs (you'll need to implement this table)
        # Example structure:
        daily_costs = []

        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            daily_costs.append({
                'date': date.strftime('%Y-%m-%d'),
                'sentiment_calls': 0,  # Count from logs
                'embedding_calls': 0,  # Count from logs
                'estimated_cost': 0.0,  # Calculate from counts
                'model_breakdown': {}
            })

        return daily_costs
```

### Cost Monitoring Endpoint
```python
# src/main.py (add this endpoint)
from src.services.cost_tracker import CostTracker

@app.get("/api/monitoring/costs/")
async def get_cost_monitoring(
    request: Request,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30, description="Number of days to retrieve")
):
    """
    Get Bedrock API cost monitoring data.

    Returns daily cost breakdown and usage statistics.
    """
    try:
        cost_tracker = CostTracker()
        daily_costs = cost_tracker.get_daily_costs(db, days=days)

        total_cost = sum(day['estimated_cost'] for day in daily_costs)

        return {
            'period_days': days,
            'total_estimated_cost': round(total_cost, 4),
            'daily_breakdown': daily_costs,
            'pricing_info': {
                'currency': 'USD',
                'note': 'Costs are estimates based on token counts'
            }
        }
    except Exception as e:
        logger.error(f"Cost monitoring error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cost data: {str(e)}"
        ) from None
```

## Testing & Validation

### Synthetic Test Suite
```python
# tests/test_resilience.py
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

def test_retry_logic_success_after_failure():
    """Test retry logic succeeds after transient failure."""
    mock_client = MagicMock()
    # Fail twice, then succeed
    mock_client.invoke_model.side_effect = [
        ClientError({'Error': {'Code': 'ThrottlingException'}}, 'InvokeModel'),
        ClientError({'Error': {'Code': 'ThrottlingException'}}, 'InvokeModel'),
        {'body': MagicMock(read=lambda: '{"content": [{"text": "{\\"sentiment\\": \\"bullish\\", \\"confidence\\": 0.8}"}]}')}
    ]

    # Test that retry succeeds
    # ... implementation

def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures."""
    # ... implementation

def test_fallback_to_haiku_on_sonnet_failure():
    """Test fallback from Claude Sonnet to Haiku."""
    # ... implementation

def test_guardrail_blocks_inappropriate_content():
    """Test guardrails block inappropriate content."""
    # ... implementation

def test_evaluation_metrics_calculation():
    """Test evaluation metrics are calculated correctly."""
    # ... implementation
```

## API Endpoints Summary

### New Day 4 Endpoints

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/api/guardrails/validate/input/` | POST | Validate input against guardrails | 30/minute |
| `/api/guardrails/validate/output/` | POST | Validate output against guardrails | 30/minute |
| `/api/evaluate/sentiment/` | POST | Evaluate model against gold dataset | 5/hour |
| `/api/monitoring/costs/` | GET | Get Bedrock API cost breakdown | 10/minute |
| `/api/monitoring/health/resilience/` | GET | Check resilience patterns status | 30/minute |

### Enhanced Existing Endpoints
- `/api/analyze/sentiment/` - Now includes guardrail validation and fallback logic
- All endpoints - Now have retry logic and circuit breaker protection

## Environment Variables

### New Day 4 Variables
```bash
# Guardrails Configuration
BEDROCK_GUARDRAIL_ID=your-guardrail-id
BEDROCK_GUARDRAIL_VERSION=DRAFT

# Multi-Model Configuration
BEDROCK_PRIMARY_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_FALLBACK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Resilience Configuration
ENABLE_RETRY_LOGIC=true
MAX_RETRIES=3
ENABLE_CIRCUIT_BREAKER=true
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Cost Monitoring
ENABLE_COST_TRACKING=true
COST_ALERT_THRESHOLD=100.00  # USD per day

# Evaluation
GOLD_DATASET_PATH=evaluation/gold_dataset.json
```

## Database Schema Updates

### Cost Tracking Table
```sql
-- Optional: Track API costs (for Day 4)
CREATE TABLE api_cost_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    model_id VARCHAR(100) NOT NULL,
    operation VARCHAR(50) NOT NULL,  -- 'sentiment', 'embedding', 'guardrail'
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost DECIMAL(10, 6),
    request_id VARCHAR(255),
    endpoint VARCHAR(255)
);

CREATE INDEX idx_cost_log_timestamp ON api_cost_log(timestamp DESC);
CREATE INDEX idx_cost_log_model ON api_cost_log(model_id);
```

## Deployment Checklist

### Day 4 Prerequisites
- [ ] Enable Amazon Bedrock Guardrails in AWS Console
- [ ] Create guardrail configuration for crypto domain
- [ ] Update IAM policies with Guardrail permissions
- [ ] Add guardrail ID to environment variables
- [ ] Create gold dataset with 100+ labeled samples
- [ ] Configure cost alerts in CloudWatch
- [ ] Test retry logic with synthetic failures
- [ ] Verify circuit breaker behavior
- [ ] Test fallback from Sonnet to Haiku

### Production Hardening
- [ ] Implement cost tracking and monitoring
- [ ] Set up alerts for high API costs
- [ ] Configure guardrail content filters
- [ ] Test prompt injection protection
- [ ] Validate evaluation metrics accuracy
- [ ] Document resilience patterns
- [ ] Create runbook for circuit breaker recovery
- [ ] Test failover scenarios

## Success Metrics

### Day 4 Completion Criteria
- ✅ Guardrails successfully block inappropriate content
- ✅ Evaluation framework shows >80% accuracy on gold dataset
- ✅ Retry logic handles transient API failures
- ✅ Circuit breaker prevents cascading failures
- ✅ Fallback to Haiku works when Sonnet fails
- ✅ Cost tracking shows accurate API spend
- ✅ All resilience patterns tested and documented

### Performance Targets
- **Guardrail Latency**: < 200ms per validation
- **Evaluation Accuracy**: > 80% F1 score
- **API Availability**: > 99.5% (with retry + circuit breaker)
- **Cost Efficiency**: < $10/day for 1000 articles
- **Fallback Success Rate**: > 95% when primary fails

## Student Learning Outcomes

By the end of Day 4, students will be able to:
1. Implement Amazon Bedrock Guardrails for content safety
2. Build evaluation frameworks for LLM quality assurance
3. Apply resilience patterns (retry, circuit breaker, fallback)
4. Monitor and optimize LLM API costs
5. Test and validate production AI systems
6. Design robust error handling for distributed systems
7. Balance cost, speed, and safety in production AI

## Next Steps: Day 5

Day 5 will focus on:
- **Dashboard UI**: Streamlit or React dashboard for crypto sentiment
- **Advanced Features**: Sentiment trends, alerts, news scoring
- **Performance Optimization**: Caching, indexing, connection pooling
- **Final Integration**: Polish all components for production readiness
- **Team Presentations**: Architecture decisions and lessons learned

