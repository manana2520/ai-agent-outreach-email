Platofrm running (k9s, rancher)
kubectl port-forward service/ai-agent-platform-management-api -n ai-platform 8000:80

Auth token

curl -H "Authorization: Bearer $(kubectl exec -n ai-platform ai-agent-platform-management-api-5d6d696788-8zh7v -- cat /var/run/secrets/kubernetes.io/serviceaccount/token)" http://localhost:8000/health | cat


# AI Agent Platform Demo: Deploy & Run Sales Personalized Email Agent

This demo shows how to:
- Delete any existing sales agent runtime
- Deploy the latest agent from a GitHub repository
- Check the pod status
- Kick off the agent with custom parameters and capture the run ID
- Check the agent run status (polling until complete)
- Check the personalized email output in the running pod

## 1. Delete Existing Sales Agent

```bash
kubectl delete aiagentruntime sales-personalized-email-agent -n ai-platform --ignore-not-found
```

## 2. Deploy the Agent from GitHub

Create the YAML file `/tmp/sales-agent-runtime.yaml` with the following content:

```yaml
apiVersion: agentic.keboola.io/v1alpha1
kind: AIAgentRuntime
metadata:
  name: sales-personalized-email-agent
  namespace: ai-platform
spec:
  entrypoint: "src/sales_personalized_email/main.py"
  codeSource:
    type: git
    gitRepo:
      url: "https://github.com/manana2520/ai-agent-outreach-email"
      branch: "main"
  envVars:
    - name: OPENAI_API_KEY
      value: "***REMOVED***"
    - name: OPENAI_API_BASE
      value: "https://openrouter.ai/api/v1"
    - name: OPENROUTER_MODEL
      value: "openai/gpt-4o-mini"
  replicas: 1
```

Then apply it:

```bash
kubectl apply -f /tmp/sales-agent-runtime.yaml
```

## 3. Check Pod Status

After deploying, check the pod status to ensure the agent is running:

```bash
kubectl get pods -n ai-platform -l app=sales-personalized-email-agent -o wide
```

Wait until the pod status is `Running` before proceeding.

## 4. Port Forward the Agent Service

```bash
kubectl port-forward service/sales-personalized-email-agent -n ai-platform 8082:80
```

*(Leave this running in a separate terminal while you interact with the API)*

## 5. Kick Off the Agent and Capture the Run ID

```bash
RUN_ID=$(curl -s -X POST http://localhost:8082/kickoff \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ***REMOVED***" \
  -d '{"crew": "sales_personalized_email", "inputs": {"name": "Joe Eyles", "title": "Vice Principal", "company": "Park Lane International School", "industry": "Education", "linkedin_url": "https://www.linkedin.com/in/joe-eyles-93b66b265", "our_product": "AI and DAta Platform for Education"}}' | jq -r .run_id)
echo "Run ID: $RUN_ID"
```

## 6. Check Agent Run Status

```bash
curl -s -X GET "http://localhost:8082/runs/$RUN_ID" \
  -H "Authorization: Bearer ***REMOVED***" | jq
```

## 7. Wait for Completion (Optional Polling Loop)

```bash
while true; do
  STATUS=$(curl -s -X GET "http://localhost:8082/runs/$RUN_ID" -H "Authorization: Bearer ***REMOVED***" | jq -r .status)
  echo "Current status: $STATUS"
  if [[ "$STATUS" == "completed" || "$STATUS" == "error" ]]; then
    break
  fi
  sleep 2
done
```

## 8. Check the Output in the Pod

Display the generated email in one step:

```bash
kubectl exec $(kubectl get pods -n ai-platform -l app=sales-personalized-email-agent --no-headers -o custom-columns=":metadata.name") -n ai-platform -- cat /app/personalized_email.md
```

---

**Expected Result:**  
The output file should contain a personalized email for the provided parameters, confirming the agent is working as intended. 