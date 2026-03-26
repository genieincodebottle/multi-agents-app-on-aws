<div align="center">

# Multi-Agent AI App on AWS

### Build and deploy a production-ready multi-agent system on AWS using Bedrock AgentCore

**3 specialized AI agents + 1 orchestrator = Your AI research team**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![AWS AgentCore](https://img.shields.io/badge/AWS-Bedrock%20AgentCore-orange.svg)](https://aws.amazon.com/bedrock/agentcore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Agents: 4](https://img.shields.io/badge/Agents-4-purple.svg)](#architecture)

</div>

---

## What You'll Build

A multi-agent system where 4 AI agents collaborate to research any topic and produce a comprehensive report:

| Agent | Role | What It Does |
|-------|------|-------------|
| **Orchestrator** | Supervisor | Breaks down your request, delegates to specialists, assembles final output |
| **Research Agent** | Web Researcher | Searches the web, gathers sources, summarizes findings |
| **Analyst Agent** | Data Analyst | Analyzes research data, identifies patterns, computes comparisons |
| **Writer Agent** | Report Writer | Takes research + analysis and produces a polished, structured report |

**Example prompt:**
> "Research the current state of AI agents in enterprise. Compare top frameworks (LangGraph, CrewAI, AutoGen, Strands). Include adoption trends and pricing."

**What you get:** A structured report with sourced research, comparative analysis, and actionable recommendations - all produced by collaborating agents.

---

## Architecture

<div align="center">
<img src="./images/architecture.svg" alt="Multi-Agent System Architecture" width="800"/>
</div>

**AWS Services Used:**
- **Bedrock AgentCore Runtime** - Serverless agent hosting (auto-scales, per-second billing)
- **Amazon Bedrock** - Foundation models (Claude Sonnet 4)
- **AgentCore Memory** - Conversation history + long-term memory
- **AgentCore Gateway** - Tool management (web search, calculator)
- **IAM** - Permissions and security

**Estimated Cost:** ~$0.01-0.05 per research request (mostly LLM token costs)

---

## Quick Start (Local Development)

### Prerequisites

| Requirement | How to Get It |
|------------|---------------|
| Python 3.10+ | [python.org/downloads](https://python.org/downloads) |
| AWS Account | [aws.amazon.com/free](https://aws.amazon.com/free) (Free Tier works) |
| AWS CLI v2 | [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| Bedrock Model Access | Enable Claude Sonnet in [Bedrock Console](https://console.aws.amazon.com/bedrock/home#/modelaccess) |

### Step 1: Clone and Install

```bash
git clone https://github.com/genieincodebottle/multi-agents-app-on-aws.git
cd multi-agents-app-on-aws

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure AWS

```bash
# Configure AWS credentials (if not already done)
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)
```

> **Don't have AWS credentials?** Go to [IAM Console](https://console.aws.amazon.com/iam/) -> Users -> Create User -> Attach `AmazonBedrockFullAccess` + `BedrockAgentCoreFullAccess` policies -> Create Access Key.

### Step 3: Enable Bedrock Models

Go to [Amazon Bedrock Model Access](https://console.aws.amazon.com/bedrock/home#/modelaccess) and enable:
- **Anthropic Claude Sonnet 4** (`us.anthropic.claude-sonnet-4-20250514-v1:0`)

> Model access approval is instant for most models. If Claude is not available in your region, you can change the model in `.env` (see Configuration section).

### Step 4: Set Up Environment

```bash
cp .env.example .env
# Edit .env with your preferences (defaults work for most users)
```

### Step 5: Run Locally

```bash
# Option A: Quick test from command line
python -m agents.orchestrator --query "Compare Python vs Rust for AI development"

# Option B: Run the Streamlit UI (web interface)
pip install -r ui/requirements.txt
streamlit run ui/app.py
```

> **First run slow?** The first Bedrock API call may take 5-10 seconds (cold start). Subsequent calls are faster.

> **Billing error?** If you see `INVALID_PAYMENT_INSTRUMENT`, add a payment method at [AWS Billing Console](https://console.aws.amazon.com/billing/) and retry after 2 minutes.

### Step 6: Test It

```bash
# Test with a simple query
python -m agents.orchestrator --query "What is machine learning?"

# Use verbose mode to see each agent's output
python -m agents.orchestrator --query "What is machine learning?" --verbose
```

> **Want to save money?** Use Amazon Nova Lite (10x cheaper) by editing `.env`:
> ```
> BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0
> ```
> Nova Lite works great for testing. Switch to Claude Sonnet for production quality.

---

## Deploy to AWS (AgentCore)

Once you've tested locally, deploy to AWS AgentCore for production use.

### Prerequisites

```bash
# Install AgentCore CLI
pip install bedrock-agentcore-starter-toolkit
```

### Option A: One-Command Deploy (Recommended for Beginners)

```bash
# This script deploys all 4 agents to AgentCore
bash scripts/deploy.sh
```

The script will:
1. Configure IAM roles (if not exists)
2. Deploy each agent to AgentCore Runtime
3. Print the endpoint URLs
4. Run a health check

### Option B: Manual Deploy (Step by Step)

```bash
# 1. Deploy Research Agent
cd deploy/agentcore
agentcore configure -e research_agent.py
agentcore launch
# Note the ARN printed - you'll need it

# 2. Deploy Analyst Agent
agentcore configure -e analyst_agent.py
agentcore launch

# 3. Deploy Writer Agent
agentcore configure -e writer_agent.py
agentcore launch

# 4. Deploy Orchestrator (needs other agent ARNs)
# Edit orchestrator.py with the ARNs from steps 1-3
agentcore configure -e orchestrator.py
agentcore launch
```

### Option C: Terraform (Production-Grade)

```bash
cd deploy/terraform

# Initialize Terraform
terraform init

# Preview what will be created
terraform plan -var="aws_region=us-east-1"

# Deploy everything
terraform apply -var="aws_region=us-east-1"

# Get outputs (agent endpoints)
terraform output
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region for all services |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Foundation model for agents |
| `TAVILY_API_KEY` | (optional) | Web search API key ([tavily.com](https://tavily.com) - free tier: 1000 searches/month) |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `MAX_RESEARCH_RESULTS` | `5` | Number of web search results per query |
| `MAX_AGENT_ITERATIONS` | `10` | Safety limit for agent reasoning loops |
| `AGENTCORE_MEMORY_ID` | (auto-created) | AgentCore Memory resource ID (for deployed mode) |

### Supported Models

| Model | Model ID | Cost (Input/Output per 1M tokens) |
|-------|----------|-----------------------------------|
| Claude Sonnet 4 (default) | `us.anthropic.claude-sonnet-4-20250514-v1:0` | $3.00 / $15.00 |
| Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001` | $0.80 / $4.00 |
| Amazon Nova Pro | `us.amazon.nova-pro-v1:0` | $0.80 / $3.20 |
| Amazon Nova Lite | `us.amazon.nova-lite-v1:0` | $0.06 / $0.24 |
| Llama 4 Scout | `us.meta.llama4-scout-17b-instruct-v1:0` | $0.27 / $0.35 |

> Change `BEDROCK_MODEL_ID` in `.env` to use a different model. Nova Lite is cheapest for testing.

---

## Project Structure

```
multi-agents-app-on-aws/
├── agents/                      # Agent source code
│   ├── __init__.py
│   ├── config.py                # Shared configuration
│   ├── research_agent.py        # Web research specialist
│   ├── analyst_agent.py         # Data analysis specialist
│   ├── writer_agent.py          # Report writing specialist
│   └── orchestrator.py          # Supervisor that coordinates all agents
│
├── tools/                       # Custom tools for agents
│   ├── __init__.py
│   ├── web_search.py            # Tavily web search integration
│   └── calculator.py            # Math computation tool
│
├── deploy/                      # Deployment configurations
│   ├── agentcore/               # AgentCore CLI deployment
│   │   ├── research_agent.py    # Runtime entrypoint
│   │   ├── analyst_agent.py     # Runtime entrypoint
│   │   ├── writer_agent.py      # Runtime entrypoint
│   │   ├── orchestrator.py      # Runtime entrypoint
│   │   └── requirements.txt
│   └── terraform/               # Infrastructure as Code
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── providers.tf
│
├── ui/                          # Streamlit frontend
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
│
├── scripts/                     # Helper scripts
│   ├── setup.sh                 # Initial AWS setup
│   ├── deploy.sh                # Deploy all agents
│   ├── cleanup.sh               # Tear down all resources
│   └── test_agents.sh           # Test deployed agents
│
├── tests/                       # Unit tests
│   ├── test_research_agent.py
│   ├── test_analyst_agent.py
│   └── test_orchestrator.py
│
├── examples/                    # Example outputs
│   └── sample_research_report.md
│
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev/test dependencies
├── pyproject.toml               # Project metadata
├── LICENSE
└── README.md
```

---

## How It Works

### Agent Communication Flow

```
User: "Research AI agent frameworks and compare them"
  │
  ▼
Orchestrator receives request
  │
  ├─► Orchestrator breaks down into subtasks:
  │     1. "Research current AI agent frameworks"
  │     2. "Analyze and compare the frameworks"
  │     3. "Write a comprehensive report"
  │
  ├─► Step 1: Calls Research Agent
  │     └─► Searches web for "AI agent frameworks 2026"
  │     └─► Summarizes: LangGraph, CrewAI, Strands, AutoGen, OpenAI Agents SDK
  │     └─► Returns structured findings with sources
  │
  ├─► Step 2: Calls Analyst Agent (receives research output)
  │     └─► Compares frameworks on: ease of use, scalability, ecosystem
  │     └─► Creates comparison matrix
  │     └─► Identifies trends and recommendations
  │     └─► Returns structured analysis
  │
  ├─► Step 3: Calls Writer Agent (receives research + analysis)
  │     └─► Structures into executive summary + sections
  │     └─► Adds formatting, citations, recommendations
  │     └─► Returns final report
  │
  ▼
Orchestrator combines outputs and returns final report to user
```

### Local Mode vs Deployed Mode

| Feature | Local Mode | Deployed (AgentCore) |
|---------|-----------|---------------------|
| How agents run | All in one Python process | Each agent in isolated microVM |
| Communication | Direct function calls | A2A protocol over HTTPS |
| Memory | In-memory (lost on restart) | AgentCore Memory (persistent) |
| Scaling | Single machine | Auto-scales 0 to 1000s |
| Cost | Just Bedrock API calls | AgentCore Runtime + Bedrock API |
| Best for | Development, testing | Production, multi-user |

---

## Customization

### Adding a New Agent

1. Create the agent in `agents/`:

```python
# agents/my_custom_agent.py
from agents.config import get_bedrock_client, DEFAULT_MODEL_ID

SYSTEM_PROMPT = """You are a specialist in [your domain].
Your job is to [specific task]."""

def run(input_data: dict) -> dict:
    client = get_bedrock_client()
    response = client.converse(
        modelId=DEFAULT_MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": input_data["query"]}]}],
    )
    return {
        "result": response["output"]["message"]["content"][0]["text"],
        "agent": "my_custom_agent",
    }
```

2. Register it in `agents/orchestrator.py`:

```python
AGENTS = {
    "research": research_agent,
    "analyst": analyst_agent,
    "writer": writer_agent,
    "my_custom": my_custom_agent,  # Add here
}
```

3. Update the orchestrator's system prompt to know about the new agent.

### Adding a New Tool

1. Create the tool in `tools/`:

```python
# tools/my_tool.py
def my_tool(param: str) -> str:
    """Description of what this tool does."""
    # Your tool logic
    return result
```

2. Add it to the agent that needs it (in `agents/research_agent.py` or whichever).

### Using a Different LLM Framework

The agents use raw Bedrock `converse()` API by default (zero dependencies, simplest for beginners). To use a framework instead:

**Strands Agents:**
```python
from strands import Agent
from strands.models.bedrock import BedrockModel

agent = Agent(
    model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0"),
    system_prompt="You are a research specialist.",
    tools=[web_search, calculator],
)
result = agent("Research AI frameworks")
```

**LangGraph:**
```python
from langgraph.prebuilt import create_react_agent
from langchain_aws import ChatBedrockConverse

model = ChatBedrockConverse(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")
agent = create_react_agent(model, tools=[web_search, calculator])
result = agent.invoke({"messages": [("user", "Research AI frameworks")]})
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `AccessDeniedException` on Bedrock | Enable model access in [Bedrock Console](https://console.aws.amazon.com/bedrock/home#/modelaccess) |
| `NoCredentialsError` | Run `aws configure` or set `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` |
| `ResourceNotFoundException` for model | Check `AWS_REGION` - Claude models available in us-east-1, us-west-2, eu-west-1 |
| `ThrottlingException` | You've hit rate limits. Add `time.sleep(1)` between calls or request limit increase |
| `agentcore: command not found` | Run `pip install bedrock-agentcore-starter-toolkit` |
| Agents timeout during deploy | Increase timeout: `agentcore configure --timeout 300` |
| Web search returns empty | Get a free Tavily API key at [tavily.com](https://tavily.com) and set `TAVILY_API_KEY` |

---

## Cleanup

```bash
# Remove all deployed AgentCore resources
bash scripts/cleanup.sh

# Or with Terraform
cd deploy/terraform
terraform destroy -var="aws_region=us-east-1"
```

---

## Cost Breakdown

| Service | Usage | Estimated Cost |
|---------|-------|---------------|
| Bedrock AgentCore Runtime | ~18s CPU per request | ~$0.0005/request |
| Amazon Bedrock (Claude Sonnet 4) | ~4000 tokens per agent call | ~$0.01-0.04/request |
| AgentCore Memory | ~10 events per session | ~$0.003/session |
| AgentCore Gateway | ~3 tool calls per request | ~$0.000015/request |
| **Total per research request** | | **~$0.01-0.05** |

> With Nova Lite model: ~$0.001-0.005 per request (10x cheaper, slightly lower quality).

---

## Learn More

- [AWS Bedrock AgentCore Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AgentCore SDK (GitHub)](https://github.com/aws/bedrock-agentcore-sdk-python)
- [AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- [Strands Agents Framework](https://github.com/strands-agents/sdk-python)
- [Build AI Systems Visually - AI/ML Companion](https://aimlcompanion.ai/)

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-agent`)
3. Commit your changes (`git commit -m 'Add new agent'`)
4. Push to the branch (`git push origin feature/new-agent`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built by [Rajesh Srivastava](https://github.com/genieincodebottle)**

[AI/ML Companion](https://aimlcompanion.ai/) | [YouTube](https://youtube.com/@genieincodebottle) | [Instagram](https://instagram.com/genieincodebottle)

</div>