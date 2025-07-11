#!/bin/bash

# Deploy agent via local Management API (same as cloud deployment)
# This script uses the local Management API instead of direct Kubernetes deployment

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

# --- Configuration ---
AGENT_NAME="sales-personalized-email-agent"
AGENT_DESCRIPTION="Sales agent creating content of personalized email"
GITHUB_URL="https://github.com/manana2520/ai-agent-outreach-email"
GITHUB_BRANCH="main"
AGENT_ENTRYPOINT="src/sales_personalized_email/main.py"
NAMESPACE="ai-agent-platform"
LOCAL_API_URL="http://localhost:8000/api/runtimes"

# --- Check if Management API is running ---
echo "[DEBUG] Checking if Management API is accessible..."
if ! curl -f -s --connect-timeout 5 "http://localhost:8000/health" >/dev/null 2>&1; then
  echo "ERROR: Management API not accessible at http://localhost:8000/health"
  echo "Please ensure the Management API is running and port-forwarded:"
  echo "kubectl port-forward service/ai-agent-platform-management-api -n $NAMESPACE 8000:80"
  exit 1
fi
echo "[DEBUG] Management API is accessible."

# --- Get API token from Kubernetes secret ---
echo "[DEBUG] Retrieving API token from Kubernetes secret..."
API_TOKEN=$(kubectl get secret ai-agent-platform-api-token -n "$NAMESPACE" -o jsonpath='{.data.api-token}' 2>/dev/null | base64 -d || echo "")

if [ -z "$API_TOKEN" ]; then
  echo "ERROR: Could not retrieve API token from Kubernetes secret"
  echo "Please ensure the secret 'ai-agent-platform-api-token' exists in namespace '$NAMESPACE'"
  exit 1
fi

# Mask token for debug
MASKED_TOKEN="${API_TOKEN:0:4}****${API_TOKEN: -4}"
echo "[DEBUG] API token retrieved: $MASKED_TOKEN"

# --- Prepare JSON payload for agent deployment ---
PAYLOAD=$(cat <<EOF
{
  "name": "$AGENT_NAME",
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
    { "name": "OPENAI_API_KEY", "value": "${OPENROUTER_API_KEY:-}", "secure": false },
    { "name": "OPENAI_API_BASE", "value": "https://openrouter.ai/api/v1", "secure": false },
    { "name": "OPENROUTER_MODEL", "value": "openai/gpt-4o-mini", "secure": false }
  ]
}
EOF
)

echo "[DEBUG] JSON payload prepared:"
if command -v jq >/dev/null 2>&1; then
  echo "$PAYLOAD" | jq .
else
  echo "$PAYLOAD"
fi

# --- Deploy agent via Management API ---
echo "[DEBUG] Deploying agent via local Management API..."
response=$(curl -s -w "\n%{http_code}" -X POST "$LOCAL_API_URL" \
  -H "Authorization: Bearer $API_TOKEN" \
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
  echo "✅ Agent deployed successfully via Management API!"
  
  # Extract agent URL if available
  if command -v jq >/dev/null 2>&1; then
    AGENT_URL=$(echo "$body" | jq -r '.url // empty')
    if [ -n "$AGENT_URL" ] && [ "$AGENT_URL" != "null" ]; then
      echo "🌐 Agent URL: $AGENT_URL"
    fi
  fi
  
  echo ""
  echo "🎉 Deployment completed in seconds (like cloud deployment)!"
  echo "The agent is now being deployed by the Kubernetes operator."
  echo ""
  echo "To monitor the deployment:"
  echo "  kubectl get pods -n $NAMESPACE -l app=$AGENT_NAME"
  echo ""
  echo "To check agent logs:"
  echo "  kubectl logs -n $NAMESPACE -l app=$AGENT_NAME --follow"
  echo ""
  echo "To test the agent (once ready):"
  echo "  kubectl port-forward -n $NAMESPACE service/$AGENT_NAME 8082:80"
  echo "  curl http://localhost:8082/health"
  
else
  if [[ "$code" == "409" ]]; then
    echo "ERROR: Agent with this name already exists."
    read -p "Do you want to delete the existing agent and redeploy? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      echo "Deleting existing agent..."
      delete_response=$(curl -s -w "\n%{http_code}" -X DELETE "$LOCAL_API_URL/$AGENT_NAME" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json")
      delete_code=$(echo "$delete_response" | tail -n 1)
      delete_body=$(echo "$delete_response" | sed '$d')
      
      if [[ "$delete_code" == "200" || "$delete_code" == "204" ]]; then
        echo "Existing agent deleted successfully. Redeploying..."
        sleep 5
        response=$(curl -s -w "\n%{http_code}" -X POST "$LOCAL_API_URL" \
          -H "Authorization: Bearer $API_TOKEN" \
          -H "Content-Type: application/json" \
          -d "$PAYLOAD")
        code=$(echo "$response" | tail -n 1)
        body=$(echo "$response" | sed '$d')
        
        if [[ "$code" == "200" || "$code" == "201" ]]; then
          echo "✅ Agent deployed successfully after deletion!"
        else
          echo "ERROR: Failed to redeploy agent after deletion (HTTP $code)"
          exit 1
        fi
      else
        echo "ERROR: Failed to delete existing agent (HTTP $delete_code)"
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

echo ""
echo "🚀 Deployment completed! The agent is now being managed by the Kubernetes operator." 