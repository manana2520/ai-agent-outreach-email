#!/bin/bash

# Deploys the sales-personalized-email agent from its GitHub repository
# to the Keboola Agentic Runtime running locally.
#
# Prerequisites:
# 1. kubectl is installed and configured to access the Kubernetes cluster
#    where the Agentic Runtime is running.
# 2. The namespace 'ai-platform' exists in the cluster.
# 3. A secret named 'ai-agent-platform-api-token' exists in the 'ai-platform'
#    namespace containing the key 'api-token' with the bearer token (base64 encoded).
# 4. The following environment variables MUST be set before running this script:
#    - OPENAI_API_KEY: Your OpenAI API key.
#    - SERPER_API_KEY: Your Serper API key.

set -e # Exit immediately if a command exits with a non-zero status.
set -u # Treat unset variables as an error when substituting.
set -o pipefail # Causes a pipeline to return the exit status of the last command in the pipe that failed.

# --- Configuration ---
# API Endpoint for the Keboola Agentic Runtime Management API
AGENTIC_API_ENDPOINT="http://localhost:8080/api/runtimes"
# Kubernetes namespace where the API token secret resides
AGENT_NAMESPACE="ai-platform"
# Name of the Kubernetes secret containing the API token
AGENT_TOKEN_SECRET_NAME="ai-agent-platform-api-token"
# Key within the secret that holds the token value
AGENT_TOKEN_SECRET_KEY="api-token"

# Agent-specific details
AGENT_NAME="sales-personalized-email-agent"
AGENT_DESCRIPTION="Agent for generating personalized sales outreach emails using CrewAI"
AGENT_ENTRYPOINT="src/sales_personalized_email/main.py"
AGENT_REPO_URL="https://github.com/manana2520/ai-agent-outreach-email"
AGENT_REPO_BRANCH="main"

# --- Check Prerequisites ---
if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "Error: OPENAI_API_KEY environment variable is not set." >&2
  exit 1
fi

if [ -z "${SERPER_API_KEY:-}" ]; then
  echo "Error: SERPER_API_KEY environment variable is not set." >&2
  exit 1
fi

echo "Checking kubectl access and retrieving API token..."
API_TOKEN=$(kubectl --namespace "${AGENT_NAMESPACE}" get secret "${AGENT_TOKEN_SECRET_NAME}" -o jsonpath="{.data.${AGENT_TOKEN_SECRET_KEY}}" | base64 --decode)

if [ -z "$API_TOKEN" ]; then
    echo "Error: Failed to retrieve API token from Kubernetes secret '${AGENT_TOKEN_SECRET_NAME}' in namespace '${AGENT_NAMESPACE}'." >&2
    echo "Please ensure kubectl is configured correctly and the secret exists." >&2
    exit 1
fi
echo "API token retrieved successfully."

# --- Prepare JSON Payload ---
# Using heredoc for better readability and handling of quotes within variables
JSON_PAYLOAD=$(cat <<EOF
{
  "name": "${AGENT_NAME}",
  "description": "${AGENT_DESCRIPTION}",
  "entrypoint": "${AGENT_ENTRYPOINT}",
  "codeSource": {
    "type": "git",
    "gitRepo": {
      "url": "${AGENT_REPO_URL}",
      "branch": "${AGENT_REPO_BRANCH}"
    }
  },
  "envVars": [
    {
      "name": "OPENAI_API_KEY",
      "value": "${OPENAI_API_KEY}"
    },
    {
      "name": "SERPER_API_KEY",
      "value": "${SERPER_API_KEY}"
    }
  ]
}
EOF
)

# --- Deploy Agent ---
echo "Deploying agent '${AGENT_NAME}' to ${AGENTIC_API_ENDPOINT}..."

RESPONSE_CODE=$(curl --silent --output /dev/stderr --write-out "%{http_code}" \
  -X POST "${AGENTIC_API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -d "${JSON_PAYLOAD}")

# Check HTTP response code
if [ "$RESPONSE_CODE" -ge 200 ] && [ "$RESPONSE_CODE" -lt 300 ]; then
  echo # Add a newline for cleaner output
  echo "Deployment request sent successfully (HTTP Status: ${RESPONSE_CODE})."
  echo "Check the Agentic Runtime API or UI for the runtime status."
  exit 0
else
  echo # Add a newline for cleaner output
  echo "Error: Deployment request failed with HTTP Status: ${RESPONSE_CODE}." >&2
  exit 1
fi 