"""Shared configuration for all agents."""

import os
import logging
from pathlib import Path
from functools import lru_cache

import boto3
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file (searches current dir, then parent dirs)
# ---------------------------------------------------------------------------

# Find .env relative to this file's location (project root)
_project_root = Path(__file__).resolve().parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()  # fallback: search from cwd upwards

# ---------------------------------------------------------------------------
# Environment config (override via .env or shell exports)
# ---------------------------------------------------------------------------

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DEFAULT_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))
MAX_RESEARCH_RESULTS = int(os.getenv("MAX_RESEARCH_RESULTS", "5"))
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("multi-agent")


# ---------------------------------------------------------------------------
# AWS clients (cached - one per process)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_bedrock_client():
    """Return a Bedrock Runtime client for the converse() API."""
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


@lru_cache(maxsize=1)
def get_bedrock_agent_client():
    """Return a Bedrock Agent Runtime client (for AgentCore invocations)."""
    return boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)


# ---------------------------------------------------------------------------
# Shared helper: call Bedrock converse() with retries
# ---------------------------------------------------------------------------

def call_llm(
    system_prompt: str,
    user_message: str,
    model_id: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    retries: int = 2,
) -> str:
    """Send a single-turn message to Bedrock and return the text response.

    This is the simplest possible LLM call - no tools, no streaming, no
    conversation history. Each agent wraps this with its own system prompt.

    Retries on throttling errors with exponential backoff.
    """
    import time
    from botocore.exceptions import ClientError

    client = get_bedrock_client()
    model = model_id or DEFAULT_MODEL_ID

    for attempt in range(retries + 1):
        try:
            response = client.converse(
                modelId=model,
                system=[{"text": system_prompt}],
                messages=[
                    {"role": "user", "content": [{"text": user_message}]},
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                },
            )
            return response["output"]["message"]["content"][0]["text"]

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            # Friendly error messages for common beginner issues
            if "AccessDeniedException" in error_code:
                if "INVALID_PAYMENT_INSTRUMENT" in error_msg:
                    raise RuntimeError(
                        f"\n{'=' * 60}\n"
                        f"  AWS BILLING ISSUE\n"
                        f"{'=' * 60}\n"
                        f"  Your AWS account needs a valid payment method.\n"
                        f"  Go to: https://console.aws.amazon.com/billing/\n"
                        f"  -> Payment Methods -> Add a credit/debit card\n"
                        f"  Then wait 2 minutes and try again.\n"
                        f"{'=' * 60}\n"
                    ) from e
                raise RuntimeError(
                    f"\n{'=' * 60}\n"
                    f"  MODEL ACCESS DENIED\n"
                    f"{'=' * 60}\n"
                    f"  Model: {model}\n"
                    f"  Fix: Go to https://console.aws.amazon.com/bedrock/home#/modelaccess\n"
                    f"  and enable 'Anthropic Claude Sonnet 4'.\n"
                    f"\n"
                    f"  Or use a cheaper model in .env:\n"
                    f"  BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0\n"
                    f"{'=' * 60}\n"
                ) from e

            if "ValidationException" in error_code:
                raise RuntimeError(
                    f"\n{'=' * 60}\n"
                    f"  INVALID MODEL ID\n"
                    f"{'=' * 60}\n"
                    f"  Model '{model}' is not valid in region '{AWS_REGION}'.\n"
                    f"  Check available models at:\n"
                    f"  https://console.aws.amazon.com/bedrock/home#/modelaccess\n"
                    f"\n"
                    f"  Try: BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0\n"
                    f"{'=' * 60}\n"
                ) from e

            if "ThrottlingException" in error_code and attempt < retries:
                wait = 2 ** attempt
                logger.warning("Rate limited, retrying in %ds (attempt %d/%d)", wait, attempt + 1, retries)
                time.sleep(wait)
                continue

            raise


def call_llm_with_history(
    system_prompt: str,
    messages: list[dict],
    model_id: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Send a multi-turn conversation to Bedrock.

    `messages` should be a list of {"role": "user"|"assistant", "content": [{"text": "..."}]}
    """
    client = get_bedrock_client()
    model = model_id or DEFAULT_MODEL_ID

    response = client.converse(
        modelId=model,
        system=[{"text": system_prompt}],
        messages=messages,
        inferenceConfig={
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    )

    return response["output"]["message"]["content"][0]["text"]
