# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CrewAI-based sales personalized email generator that uses multiple AI agents to research prospects, personalize content, and write compelling outreach emails. The system includes both a local development setup and cloud deployment capabilities with a Streamlit web interface.

## Development Commands

### Core Development
- `uv lock` - Lock dependencies
- `uv sync` - Install/sync dependencies
- `uv run sales_personalized_email` - Run the crew locally
- `crewai run` - Alternative command to run the crew

### Agent Operations
- `uv run sales_personalized_email` - Run with default inputs (Joe Eyles example)
- `python -m sales_personalized_email.main train <iterations> <filename>` - Train the crew
- `python -m sales_personalized_email.main replay <task_id>` - Replay from specific task
- `python -m sales_personalized_email.main test <iterations> <model>` - Test the crew

### Streamlit Interface
- `streamlit run streamlit_app/app.py` - Start the web interface
- The app provides both cloud and local runner modes for agent execution

### Deployment Scripts
- `./deployment/deploy_and_run_agent_locally.sh` - Deploy to local Kubernetes with full monitoring
- `./scripts/start-local-k8-platform-port-forward.sh` - Start port forwarding for platform API
- `./scripts/run-streamlit-app.sh` - Run Streamlit interface
- `./scripts/test-agent-deployment.sh` - Test agent deployment

## Architecture

### Core Components
- **SalesPersonalizedEmailCrew**: Main crew orchestrator (src/sales_personalized_email/crew.py)
- **Three specialized agents**:
  - `prospect_researcher`: Uses SerperDevTool and ScrapeWebsiteTool to gather prospect information
  - `content_personalizer`: Identifies connection points between prospect and product
  - `email_copywriter`: Crafts the final personalized email with structured output

### Agent Configuration
- Agents defined in `src/sales_personalized_email/config/agents.yaml`
- Tasks defined in `src/sales_personalized_email/config/tasks.yaml`
- Sequential processing workflow with delegation disabled for focused execution

### Input Structure
The crew expects these input parameters:
- `name`: Prospect's name
- `title`: Job title
- `company`: Company name
- `industry`: Industry sector
- `linkedin_url`: LinkedIn profile URL
- `our_product`: Product/service description

### Output Structure
Returns a PersonalizedEmail object with:
- `subject_line`: Compelling, personalized subject (max 10 words)
- `email_body`: Conversational yet professional email body
- `follow_up_notes`: Suggested talking points for future interactions

## Deployment Architecture

### Local Development
- Uses UV for dependency management (Python 3.10-3.13)
- Environment variables loaded from `.env` file
- Supports OpenAI API or OpenRouter API (configured via environment)

### Cloud Deployment
- Kubernetes-based deployment using AIAgentRuntime custom resources
- Namespace: `ai-agent-platform`
- Uses OpenRouter API with GPT-4o-mini model by default
- Comprehensive monitoring with crash detection and log aggregation

### API Interface
- RESTful API with endpoints: `/kickoff`, `/runs/{id}`, `/health`
- Token-based authentication (Bearer tokens)
- Polling-based status monitoring for async operations

## Environment Variables

Required in `.env` file:
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY`: LLM API access
- `SERPER_API_KEY`: For web search functionality
- `AGENT_API_TOKEN`: Local agent API authentication
- `CLOUD_AGENT_API_TOKEN`: Cloud agent API authentication

## Important Notes

- The project uses sequential agent processing (not hierarchical)
- Web scraping tools require proper URL formatting in tool inputs
- Streamlit app provides real-time status updates with humorous messages during processing
- Deployment scripts include comprehensive error handling and pod crash detection
- The crew outputs structured JSON that can be easily integrated with email systems