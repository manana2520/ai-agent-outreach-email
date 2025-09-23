#!/bin/bash

# Load environment variables
source .env

echo "Testing enhanced prospect validation system..."

# Test 1: Complete information provided (should validate LinkedIn)
echo "=== Test 1: Complete information provided ==="
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
      "country": "Czech Republic",
      "linkedin_profile": "https://www.linkedin.com/in/joe-eyles-93b66b265",
      "selling_intent": "Data platform to improve student outcomes"
    }
  }' | jq '.'

echo -e "\n=== Test 2: Minimal information (should research missing fields) ==="
# Test 2: Only required fields (should research title, country, LinkedIn)
curl -X POST "https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev/kickoff" \
  -H "Authorization: Bearer $CLOUD_AGENT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "sales_personalized_email",
    "inputs": {
      "first_name": "Satya",
      "last_name": "Nadella",
      "title": null,
      "company": "Microsoft",
      "phone": null,
      "country": null,
      "linkedin_profile": null,
      "selling_intent": null
    }
  }' | jq '.'

echo "Tests initiated. Use monitor-cloud-run.sh to check results."