#!/bin/bash

# Load environment variables
if [ -f .env ]; then
  source .env
else
  echo "ERROR: .env file not found"
  exit 1
fi

if [ -z "$1" ]; then
  echo "Usage: $0 <run_id>"
  exit 1
fi

RUN_ID="$1"
echo "Monitoring run: $RUN_ID"

# Try both tokens to see which one works
for TOKEN_VAR in "AGENT_API_TOKEN" "CLOUD_AGENT_API_TOKEN"; do
  TOKEN="${!TOKEN_VAR}"
  echo "Trying with $TOKEN_VAR..."

  response=$(curl -s -H "Authorization: Bearer $TOKEN" "https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev/runs/$RUN_ID")

  if echo "$response" | grep -q '"detail.*Invalid or expired token"'; then
    echo "Token $TOKEN_VAR failed"
  else
    echo "Success with $TOKEN_VAR:"
    echo "$response" | jq . 2>/dev/null || echo "$response"
    break
  fi
done