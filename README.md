# Personalized Welcome Email Crew

Welcome to the Personalized Welcome Email Crew project, powered by [crewAI](https://crewai.com). This project is designed to create highly personalized welcome emails for new users or clients. It leverages a multi-agent AI system to research a person and their company, and then craft a custom email based on that information.

This template is built on the powerful and flexible framework provided by crewAI, enabling agents to collaborate effectively on complex tasks.

## Installation

Ensure you have Python >=3.10 <=3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

```bash
uv sync
```

### Customizing

**Add your API keys into the `.env` file.** At a minimum, you need `OPENAI_API_KEY`, but you may need others depending on the tools you use.

- Modify `src/personalized_welcome_email/config/agents.yaml` to define your agents.
- Modify `src/personalized_welcome_email/config/tasks.yaml` to define your tasks.
- Modify `src/personalized_welcome_email/crew.py` to add your own logic, tools, and specific arguments.
- Modify `src/personalized_welcome_email/main.py` to add custom inputs for your agents and tasks.

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
uv run personalized_welcome_email
```

This command initializes the Personalized Welcome Email Crew, assembling the agents and assigning them tasks as defined in your configuration. The agent will take input about a new user, research them, and generate a personalized welcome email.

The final output will be saved in `final_welcome_email.html`.

## Understanding Your Crew

The Personalized Welcome Email Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve the goal. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding this Crew or crewAI:
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
