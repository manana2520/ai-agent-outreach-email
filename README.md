# SalesPersonalizedEmail Crew

Welcome to the SalesPersonalizedEmail Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <=3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

1. First lock the dependencies and then install them:
```bash
uv lock
```
```bash
uv sync
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/sales_personalized_email/config/agents.yaml` to define your agents
- Modify `src/sales_personalized_email/config/tasks.yaml` to define your tasks
- Modify `src/sales_personalized_email/crew.py` to add your own logic, tools and specific args
- Modify `src/sales_personalized_email/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```
or
```bash
uv run sales_personalized_email
```

### Dynamic Selling Intent Feature

The agent now supports **dynamic selling intent** - you can specify ANY use case and the email will focus on it:

```bash
# Example with coffee machine use case
uv run python src/sales_personalized_email/main.py \
  --first_name "Milan" \
  --last_name "Kulhanek" \
  --company "Deloitte" \
  --selling_intent "coffee machine"

# Example with CRM use case
uv run python src/sales_personalized_email/main.py \
  --first_name "John" \
  --last_name "Doe" \
  --company "Acme Corp" \
  --selling_intent "CRM integration"

# Example with no selling intent (uses general Keboola benefits)
uv run python src/sales_personalized_email/main.py \
  --first_name "Jane" \
  --last_name "Smith" \
  --company "TechCorp"
```

**Key Features:**
- ✅ NO hardcoded use cases - fully dynamic
- ✅ Subject line includes selling intent keywords
- ✅ Email body focuses exclusively on specified use case
- ✅ Falls back to general industry benefits when no intent provided
- ✅ Strong assumptive CTAs ("When's the best time..." not "Would you be open...")

### Cloud Deployment

The agent is deployed at:
```
https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev
```

Test with curl:
```bash
curl -X POST "https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev/kickoff" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "sales_personalized_email",
    "inputs": {
      "first_name": "Milan",
      "last_name": "Kulhanek",
      "title": "",
      "company": "Deloitte",
      "selling_intent": "coffee machine"
    }
  }'
```

## Understanding Your Crew

The sales-personalized-email Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the SalesPersonalizedEmail Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
