#!/bin/bash

# Exit on error, unset variable, or failed pipeline
set -euo pipefail

# --- Load environment variables ---
echo "[DEBUG] Loading .env file..."
if [ -f .env ]; then
  source .env
  echo "[DEBUG] .env loaded."
else
  echo "ERROR: .env file not found. Exiting."
  exit 1
fi

# --- Configuration (edit as needed) ---
AGENT_NAME="sales-personalized-email-agent"
AGENT_DESCRIPTION="MSales agent creating content of personalized email"
GITHUB_URL="https://github.com/manana2520/ai-agent-outreach-email"
GITHUB_BRANCH="main"
AGENT_ENTRYPOINT="src/sales_personalized_email/main.py"
NAMESPACE="aap-keboola" # Change if your namespace is different
KEBOOLA_API_TOKEN="${KEBOOLA_API_TOKEN:-}"

# --- Check required variables ---
echo "[DEBUG] Checking KEBOOLA_API_TOKEN..."
if [ -z "$KEBOOLA_API_TOKEN" ]; then
  echo "ERROR: KEBOOLA_API_TOKEN not set in .env"
  exit 1
fi
# Mask token for debug
MASKED_TOKEN="${KEBOOLA_API_TOKEN:0:4}****${KEBOOLA_API_TOKEN: -4}"
echo "[DEBUG] KEBOOLA_API_TOKEN is set: $MASKED_TOKEN"

# --- Prepare JSON payload for agent deployment ---
# OPENAI_API_BASE intentionally omitted to ensure agent uses the default OpenAI endpoint (https://api.openai.com/v1)
# This matches the config of other working agents and avoids OpenRouter authentication errors.
PAYLOAD=$(cat <<EOF
{
  "name": "$AGENT_NAME",
  "namespace": "$NAMESPACE",
  "description": "$AGENT_DESCRIPTION",
  "entrypoint": "$AGENT_ENTRYPOINT",
  "codeSource": {
    "type": "git",
    "gitRepo": {
      "url": "$GITHUB_URL",
      "branch": "$GITHUB_BRANCH"
    }
  },
  "envVars": [
    { "name": "OPENAI_API_KEY", "value": "${OPENAI_API_KEY:-}", "secure": false },
    { "name": "OPENROUTER_MODEL", "value": "openai/gpt-4o-mini" },
    { "name": "AGENT_API_TOKEN", "value": "${AGENT_API_TOKEN:-}", "secure": false }
  ]
}
EOF
)

echo "[DEBUG] JSON payload prepared."
if command -v jq >/dev/null 2>&1; then
  echo "$PAYLOAD" | jq .
else
  echo "$PAYLOAD"
fi

# --- Deploy or update the agent runtime ---
echo "[DEBUG] Deploying agent to Keboola Agentic cloud..."
KEBOOLA_API_URL="https://agentic.canary-orion.keboola.dev/api/runtimes"
response=$(curl -s -w "\n%{http_code}" -X POST "$KEBOOLA_API_URL" \
  -H "Authorization: Bearer $KEBOOLA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# --- Parse response ---
code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

echo "[DEBUG] HTTP status code: $code"
echo "[DEBUG] Response body:"
if command -v jq >/dev/null 2>&1; then
  echo "$body" | jq . || echo "$body"
else
  echo "$body"
fi

if [[ "$code" == "200" || "$code" == "201" ]]; then
  echo "Agent deployed successfully!"
else
  if [[ "$code" == "409" ]]; then
    echo "ERROR: Agent with this name already exists."
    read -p "Do you want to delete the existing agent and redeploy? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      echo "Deleting existing agent..."
      # Send DELETE request to Keboola API
      delete_response=$(curl -s -w "\n%{http_code}" -X DELETE "$KEBOOLA_API_URL/$AGENT_NAME?namespace=$NAMESPACE" \
        -H "Authorization: Bearer $KEBOOLA_API_TOKEN" \
        -H "Content-Type: application/json")
      delete_code=$(echo "$delete_response" | tail -n 1)
      delete_body=$(echo "$delete_response" | sed '$d')
      if [[ "$delete_code" == "200" || "$delete_code" == "204" ]]; then
        echo "Existing agent deleted successfully. Redeploying..."
        # Wait for backend to process deletion
        # This avoids immediate 409 errors if deletion is not yet complete
        echo "Waiting 10 seconds to ensure agent is fully deleted..."
        sleep 10
        # Try to redeploy
        echo "Redeploying agent..."
        response=$(curl -s -w "\n%{http_code}" -X POST "$KEBOOLA_API_URL" \
          -H "Authorization: Bearer $KEBOOLA_API_TOKEN" \
          -H "Content-Type: application/json" \
          -d "$PAYLOAD")
        code=$(echo "$response" | tail -n 1)
        body=$(echo "$response" | sed '$d')
        echo "[DEBUG] HTTP status code: $code"
        echo "[DEBUG] Response body:"
        if command -v jq >/dev/null 2>&1; then
          echo "$body" | jq . || echo "$body"
        else
          echo "$body"
        fi
        if [[ "$code" == "200" || "$code" == "201" ]]; then
          echo "Agent deployed successfully after deletion!"
        else
          echo "ERROR: Failed to redeploy agent after deletion (HTTP $code)"
          exit 1
        fi
      else
        echo "ERROR: Failed to delete existing agent (HTTP $delete_code)"
        if command -v jq >/dev/null 2>&1; then
          echo "$delete_body" | jq . || echo "$delete_body"
        else
          echo "$delete_body"
        fi
        exit 1
      fi
    else
      echo "Aborting deployment. Existing agent was not deleted."
      exit 0
    fi
  else
    echo "ERROR: Failed to deploy agent (HTTP $code)"
    exit 1
  fi
fi

# --- Optionally: Trigger a run or poll status here if needed --- 