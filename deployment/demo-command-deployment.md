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
      value: "${OPENROUTER_API_KEY}"
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