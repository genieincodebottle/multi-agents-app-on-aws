"""Shared configuration for all agents."""

import os
import logging
from functools import lru_cache

import boto3

# ---------------------------------------------------------------------------
# Environment config (override via .env or shell exports)
# ---------------------------------------------------------------------------

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DEFAULT_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514")
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
) -> str:
    """Send a single-turn message to Bedrock and return the text response.

    This is the simplest possible LLM call - no tools, no streaming, no
    conversation history. Each agent wraps this with its own system prompt.
    """
    client = get_bedrock_client()
    model = model_id or DEFAULT_MODEL_ID

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
