#!/bin/bash

# Load environment variables
if [ -f .env ]; then
  source .env
else
  echo "ERROR: .env file not found"
  exit 1
fi

# Check if CLOUD_AGENT_API_TOKEN is set
if [ -z "$CLOUD_AGENT_API_TOKEN" ]; then
  echo "ERROR: CLOUD_AGENT_API_TOKEN not set in .env"
  exit 1
fi

echo "Triggering cloud agent run..."

curl -X POST "https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev/kickoff" \
  -H "Authorization: Bearer $CLOUD_AGENT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "sales_personalized_email",
    "inputs": {
      "first_name": "Joe",
      "last_name": "Eyles",
      "title": "Vice Principal",
      "company": "Park Lane International School",
      "phone": null,
      "country": "UK",
      "linkedin_profile": "https://www.linkedin.com/in/joe-eyles-93b66b265",
      "selling_intent": "AI and Data Platform for Education to improve student outcomes and administrative efficiency"
    }
  }'