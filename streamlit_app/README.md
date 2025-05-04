# Streamlit App for Personalized Email Agent

This Streamlit application provides a web interface to **trigger and monitor** the `SalesPersonalizedEmailCrew` agent running inside the Kubernetes Agentic Runtime.

**IMPORTANT:** This app **does not** run the agent code itself. It interacts with the deployed agent via its API.

## Prerequisites

1.  **Agent Deployed:** The `sales-personalized-email-agent` must be successfully deployed to your Kubernetes cluster (e.g., using `deployment/deploy_and_run_agent.sh` or other methods).
2.  **Port-Forward Active:** You **must** have the agent service port-forward running in a **separate terminal**. Execute the following command and leave it running:
    ```bash
    kubectl port-forward service/sales-personalized-email-agent -n ai-platform 8082:80
    ```
    The Streamlit app connects to `http://localhost:8082`.

## Setup

1.  **Ensure Main Dependencies are Installed:** Make sure you have installed all dependencies for the main project (CrewAI, etc.) listed in the root `pyproject.toml` or `requirements.txt`, ideally within a virtual environment.

2.  **Install Streamlit Dependencies:**
    ```bash
    # Activate your virtual environment if you haven't already
    # source .venv/bin/activate

    pip install -r streamlit_app/requirements.txt
    ```

3.  **Configure API Keys (Optional but Recommended):** Although this app doesn't run the agent directly, having a `.env` file in the project root can be helpful for consistency if you add other features later. The *deployed agent* must have its API keys configured correctly via its deployment.

## Running the App

Run the following command from the **project root directory** (`crewAI-agent-personalized-outreach-email/`):

```bash
# Make sure your virtual environment is active
# Make sure the kubectl port-forward command is running in another terminal

# Add the src directory to PYTHONPATH (Optional - no longer strictly needed by this app version)
# export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run Streamlit
streamlit run streamlit_app/app.py
```

The web application should open in your browser.

## How to Use

1.  Fill in the prospect's details in the form fields on the sidebar.
2.  Click the "Generate Personalized Email" button.
3.  Wait for the agent crew (running in Kubernetes) to process the request. The app will poll for status.
4.  The generated email subject and body (retrieved via API) will be displayed on the page upon completion. 